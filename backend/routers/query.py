import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import get_db
from models.db_models import Project, Dataset, Datamap, ChatHistory
from services.spss_parser import load_parquet
from services.claude_agent import run_query

router = APIRouter(prefix="/projects", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    user_id: int | None = None  # None until Phase B auth; replaced with JWT-extracted user id


@router.post("/{project_id}/query")
async def query_project(project_id: int, body: QueryRequest, db: Session = Depends(get_db)):
    """Send a natural language question about the project's survey data."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    dataset = db.query(Dataset).filter(Dataset.project_id == project_id).first()
    datamap = db.query(Datamap).filter(Datamap.project_id == project_id).first()

    if not dataset or not datamap:
        raise HTTPException(status_code=400, detail="Project data not uploaded yet")

    df = load_parquet(project_id)
    registry = json.loads(datamap.question_registry)

    result = await run_query(
        question=body.question,
        df=df,
        registry=registry,
        weight_variable=datamap.weight_variable,
        wave_variable=dataset.wave_variable,
    )

    history = ChatHistory(
        user_id=body.user_id,
        project_id=project_id,
        question=body.question,
        response=result["response"],
        chart_json=json.dumps(result["chart"]) if result.get("chart") else None,
    )
    db.add(history)
    db.commit()

    return result


@router.get("/{project_id}/history")
def get_history(
    project_id: int,
    user_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Retrieve chat history for a project (scoped to the given user)."""
    q = db.query(ChatHistory).filter(ChatHistory.project_id == project_id)
    if user_id is not None:
        q = q.filter(ChatHistory.user_id == user_id)
    history = q.order_by(ChatHistory.created_at.desc()).limit(limit).all()
    return [
        {
            "id": h.id,
            "question": h.question,
            "response": h.response,
            "chart": json.loads(h.chart_json) if h.chart_json else None,
            "created_at": h.created_at,
        }
        for h in history
    ]
