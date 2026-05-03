import pandas as pd
from typing import Optional

REQUIRED_COLUMNS = {"question_id", "variable_name", "question_text", "question_type"}
OPTIONAL_COLUMNS = {"answer_option", "is_weight"}

WEIGHT_FLAG_VALUES = {"yes", "true", "1", "y"}


def parse_datamap(file_path: str) -> tuple[dict, Optional[str]]:
    """
    Parse the datamap Excel file into a question registry and weight variable name.

    Returns:
        registry: {question_id: {label, type, variables, option_labels}}
        weight_variable: variable name of the weight column, or None
    """
    df = pd.read_excel(file_path, dtype=str)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Datamap is missing required columns: {missing}. "
            f"Expected: question_id, variable_name, question_text, question_type, "
            f"answer_option (optional), is_weight (optional)"
        )

    registry: dict = {}
    weight_variable: Optional[str] = None

    for _, row in df.iterrows():
        qid = str(row["question_id"]).strip()
        var = str(row["variable_name"]).strip()

        if not qid or qid.lower() in ("nan", "none"):
            continue

        is_weight_raw = str(row.get("is_weight", "")).strip().lower()
        if is_weight_raw in WEIGHT_FLAG_VALUES:
            weight_variable = var
            continue

        if qid not in registry:
            registry[qid] = {
                "label": str(row["question_text"]).strip(),
                "type": str(row["question_type"]).strip().lower(),
                "variables": [],
                "option_labels": {},
            }

        registry[qid]["variables"].append(var)

        answer_option = str(row.get("answer_option", "")).strip()
        if answer_option and answer_option.lower() not in ("nan", "none", ""):
            registry[qid]["option_labels"][var] = answer_option

    return registry, weight_variable
