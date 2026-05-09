import pandas as pd
import numpy as np
from typing import Optional


def apply_filters(df: pd.DataFrame, filters: dict, registry: dict) -> pd.DataFrame:
    """
    Apply filters to the DataFrame.

    filters format: {question_id_or_variable: values}
      - List of values: equality filter (df[var].isin(values))
      - List of two numbers [min, max]: range filter for numeric variables (e.g. age 25-35)
    """
    filtered = df.copy()
    for key, values in filters.items():
        var = _resolve_variable(key, registry, df)
        if var is None:
            continue

        if (
            isinstance(values, list)
            and len(values) == 2
            and all(isinstance(v, (int, float)) for v in values)
        ):
            filtered = filtered[(filtered[var] >= values[0]) & (filtered[var] <= values[1])]
        elif isinstance(values, list):
            filtered = filtered[filtered[var].isin(values)]

    return filtered


def _resolve_variable(key: str, registry: dict, df: pd.DataFrame) -> Optional[str]:
    """Map a question_id or variable name to a DataFrame column name."""
    if key in registry:
        q = registry[key]
        if q["type"] == "single" and len(q["variables"]) >= 1:
            return q["variables"][0]
    if key in df.columns:
        return key
    return None


def _weighted_base(df: pd.DataFrame, weight_col: Optional[str]) -> float:
    if weight_col and weight_col in df.columns:
        return float(df[weight_col].sum())
    return float(len(df))


def get_frequency(
    df: pd.DataFrame,
    registry: dict,
    question_code: str,
    filters: Optional[dict] = None,
    weighted: bool = True,
    weight_variable: Optional[str] = None,
    wave: Optional[str] = None,
    wave_variable: Optional[str] = None,
) -> dict:
    """Frequency / % breakdown of a single-code or multi-response question."""
    if filters:
        df = apply_filters(df, filters, registry)
    if wave and wave_variable and wave_variable in df.columns:
        df = df[df[wave_variable].astype(str) == str(wave)]

    q = registry.get(question_code)
    if not q:
        return {"error": f"Question '{question_code}' not found in registry"}

    weight_col = weight_variable if (weighted and weight_variable and weight_variable in df.columns) else None
    total_n = len(df)
    w_total_base = _weighted_base(df, weight_col)
    answered_n = total_n
    w_base = w_total_base

    results = {}

    if q["type"] in ("single", "scale"):
        var = q["variables"][0]
        if var not in df.columns:
            return {"error": f"Variable '{var}' not found in dataset"}

        answered_df = df[df[var].notna()]
        answered_n = len(answered_df)
        w_base = _weighted_base(answered_df, weight_col)
        unique_vals = answered_df[var].unique()

        for val in sorted(unique_vals):
            mask = answered_df[var] == val
            # Normalise the value key: SPSS stores as float (1.0), map to "1"
            val_key = str(int(val)) if isinstance(val, float) and val == int(val) else str(val)
            label = q["option_labels"].get(val_key, str(val))

            if weight_col:
                n = float(answered_df.loc[mask, weight_col].sum())
            else:
                n = float(mask.sum())

            results[str(val)] = {
                "label": label,
                "pct": round(n / w_base * 100, 1) if w_base > 0 else 0.0,
                "n": round(n, 1),
            }

    elif q["type"] == "multi":
        for var in q["variables"]:
            if var not in df.columns:
                continue
            opt_label = q["option_labels"].get(var, var)
            mask = df[var] == 1

            if weight_col:
                n = float(df.loc[mask, weight_col].sum())
            else:
                n = float(mask.sum())

            results[var] = {
                "label": opt_label,
                "pct": round(n / w_base * 100, 1) if w_base > 0 else 0.0,
                "n": round(n, 1),
            }

    return {
        "question_code": question_code,
        "question_label": q["label"],
        "question_type": q["type"],
        "results": results,
        "total_n": total_n,
        "answered_n": answered_n,
        "base_n": answered_n,
        "weighted_base": round(w_base, 1),
        "weighted": bool(weight_col),
    }


def get_trend(
    df: pd.DataFrame,
    registry: dict,
    question_code: str,
    wave_variable: Optional[str] = None,
    filters: Optional[dict] = None,
    weighted: bool = True,
    weight_variable: Optional[str] = None,
) -> dict:
    """Wave-over-wave trend for a question."""
    if filters:
        df = apply_filters(df, filters, registry)

    if not wave_variable or wave_variable not in df.columns:
        return {"error": f"Wave variable '{wave_variable}' not found in dataset. Cannot compute trend."}

    waves = sorted(df[wave_variable].dropna().unique(), key=str)
    trend_data = []

    for wave in waves:
        wave_df = df[df[wave_variable] == wave]
        result = get_frequency(
            wave_df, registry, question_code,
            weighted=weighted, weight_variable=weight_variable,
        )
        trend_data.append({"wave": str(wave), "data": result})

    return {
        "question_code": question_code,
        "wave_variable": wave_variable,
        "waves": [str(w) for w in waves],
        "trend": trend_data,
    }


def get_top_box(
    df: pd.DataFrame,
    registry: dict,
    question_code: str,
    top_values: list,
    box_label: str = "Top Box",
    filters: Optional[dict] = None,
    weighted: bool = True,
    weight_variable: Optional[str] = None,
    wave: Optional[str] = None,
    wave_variable: Optional[str] = None,
) -> dict:
    """Box score: % of answered respondents who chose one of the specified values. Supports top and bottom box."""
    if filters:
        df = apply_filters(df, filters, registry)
    if wave and wave_variable and wave_variable in df.columns:
        df = df[df[wave_variable].astype(str) == str(wave)]

    q = registry.get(question_code)
    if not q or q["type"] not in ("single", "scale"):
        return {"error": f"Top box only supported for single-code or scale questions. '{question_code}' is type '{q['type'] if q else 'unknown'}'."}

    var = q["variables"][0]
    if var not in df.columns:
        return {"error": f"Variable '{var}' not found in dataset"}

    weight_col = weight_variable if (weighted and weight_variable and weight_variable in df.columns) else None
    total_n = len(df)

    answered_df = df[df[var].notna()]
    answered_n = len(answered_df)
    w_answered_base = _weighted_base(answered_df, weight_col)

    mask = answered_df[var].isin(top_values)
    if weight_col:
        n = float(answered_df.loc[mask, weight_col].sum())
    else:
        n = float(mask.sum())

    return {
        "question_code": question_code,
        "question_label": q["label"],
        "box_label": box_label,
        "top_values": top_values,
        "pct": round(n / w_answered_base * 100, 1) if w_answered_base > 0 else 0.0,
        "n": round(n, 1),
        "total_n": total_n,
        "answered_n": answered_n,
        "base_n": answered_n,
        "weighted_base": round(w_answered_base, 1),
        "weighted": bool(weight_col),
    }


def get_mean(
    df: pd.DataFrame,
    registry: dict,
    question_code: str,
    filters: Optional[dict] = None,
    weighted: bool = True,
    weight_variable: Optional[str] = None,
    wave: Optional[str] = None,
    wave_variable: Optional[str] = None,
) -> dict:
    """Weighted or unweighted mean for a numeric/rating question."""
    if filters:
        df = apply_filters(df, filters, registry)
    if wave and wave_variable and wave_variable in df.columns:
        df = df[df[wave_variable].astype(str) == str(wave)]

    q = registry.get(question_code)
    if not q:
        return {"error": f"Question '{question_code}' not found in registry"}

    var = q["variables"][0]
    if var not in df.columns:
        return {"error": f"Variable '{var}' not found in dataset"}

    weight_col = weight_variable if (weighted and weight_variable and weight_variable in df.columns) else None
    total_n = len(df)
    valid = df[var].notna()
    base_n = int(valid.sum())

    if base_n == 0:
        return {"error": "No valid (non-null) values found for this question after applying filters"}

    if weight_col:
        mean_val = float(np.average(df.loc[valid, var], weights=df.loc[valid, weight_col]))
        w_base = float(df.loc[valid, weight_col].sum())
    else:
        mean_val = float(df.loc[valid, var].mean())
        w_base = float(base_n)

    return {
        "question_code": question_code,
        "question_label": q["label"],
        "mean": round(mean_val, 2),
        "total_n": total_n,
        "answered_n": base_n,
        "base_n": base_n,
        "weighted_base": round(w_base, 1),
        "weighted": bool(weight_col),
    }
