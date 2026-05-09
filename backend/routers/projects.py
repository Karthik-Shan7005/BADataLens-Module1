import shutil
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models.db_models import Project, Dataset, Datamap
from services.spss_parser import parse_spss, save_parquet, SPSS_DIR
from services.datamap_parser import parse_datamap

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", status_code=201)
async def create_project(
    name: str = Form(...),
    expiry_months: int = Form(3),
    spss_file: UploadFile = File(...),
    datamap_file: UploadFile = File(...),
    wave_variable: str = Form(None),
    db: Session = Depends(get_db),
):
    """Create a new project by uploading an SPSS file and a datamap Excel file."""
    project = Project(name=name, expiry_months=expiry_months)
    db.add(project)
    db.flush()

    # Persist uploaded files
    spss_path = str(SPSS_DIR / f"project_{project.id}_{spss_file.filename}")
    datamap_path = str(SPSS_DIR / f"project_{project.id}_datamap.xlsx")

    with open(spss_path, "wb") as f:
        shutil.copyfileobj(spss_file.file, f)
    with open(datamap_path, "wb") as f:
        shutil.copyfileobj(datamap_file.file, f)

    # Parse SPSS and convert to parquet
    try:
        df, spss_meta = parse_spss(spss_path)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Failed to parse SPSS file: {e}")

    parquet_path = save_parquet(df, project.id)

    # Parse datamap
    try:
        registry, weight_variable = parse_datamap(datamap_path)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))

    # Enrich registry with SPSS value labels.
    # single/scale questions always use SPSS code-based labels (correct code→name mapping).
    # multi questions only fill from SPSS when datamap provided no option_labels.
    spss_value_labels = spss_meta.get("value_labels", {})
    for q in registry.values():
        for var in q["variables"]:
            if var in spss_value_labels:
                spss_code_labels = {
                    str(int(code)) if isinstance(code, float) and code == int(code) else str(code): label
                    for code, label in spss_value_labels[var].items()
                }
                if spss_code_labels:
                    if q["type"] in ("single", "scale") or not q["option_labels"]:
                        q["option_labels"] = spss_code_labels

    dataset = Dataset(
        project_id=project.id,
        spss_path=spss_path,
        parquet_path=parquet_path,
        wave_variable=wave_variable,
    )
    db.add(dataset)

    datamap_record = Datamap(
        project_id=project.id,
        question_registry=json.dumps(registry),
        weight_variable=weight_variable,
    )
    db.add(datamap_record)

    db.commit()
    db.refresh(project)

    return {
        "project_id": project.id,
        "name": project.name,
        "questions_loaded": len(registry),
        "weight_variable": weight_variable,
        "wave_variable": wave_variable,
        "total_respondents": len(df),
    }


@router.get("/")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [
        {"id": p.id, "name": p.name, "created_at": p.created_at, "expiry_months": p.expiry_months}
        for p in projects
    ]


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    datamap = db.query(Datamap).filter(Datamap.project_id == project_id).first()
    dataset = db.query(Dataset).filter(Dataset.project_id == project_id).first()
    registry = json.loads(datamap.question_registry) if datamap else {}

    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "expiry_months": project.expiry_months,
        "questions": [
            {"code": k, "label": v["label"], "type": v["type"]}
            for k, v in registry.items()
        ],
        "weight_variable": datamap.weight_variable if datamap else None,
        "wave_variable": dataset.wave_variable if dataset else None,
    }
