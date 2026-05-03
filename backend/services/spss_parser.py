import pyreadstat
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SPSS_DIR = DATA_DIR / "spss"
PARQUET_DIR = DATA_DIR / "parquet"

SPSS_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_DIR.mkdir(parents=True, exist_ok=True)


def parse_spss(file_path: str) -> tuple[pd.DataFrame, dict]:
    """Read SPSS .sav file and return DataFrame + metadata dict."""
    df, meta = pyreadstat.read_sav(file_path, apply_value_formats=False)

    variable_names = meta.column_names
    variable_labels = meta.column_labels  # ordered list matching column_names
    value_labels = meta.variable_value_labels  # {var_name: {code: label}}

    var_label_map = dict(zip(variable_names, variable_labels))

    return df, {
        "variable_labels": var_label_map,
        "value_labels": value_labels,
        "variable_names": variable_names,
    }


def save_parquet(df: pd.DataFrame, project_id: int) -> str:
    path = str(PARQUET_DIR / f"project_{project_id}.parquet")
    df.to_parquet(path, index=False)
    return path


def load_parquet(project_id: int) -> pd.DataFrame:
    path = str(PARQUET_DIR / f"project_{project_id}.parquet")
    return pd.read_parquet(path)
