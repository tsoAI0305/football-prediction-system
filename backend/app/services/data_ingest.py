# Minimal data ingestion utilities for fixtures/top_players/injuries.
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

class DataIngestError(Exception):
    pass

class DataIngestWarning(Warning):
    pass

def _read_any(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise DataIngestError(f"File not found: {path}")
    suf = p.suffix.lower()
    if suf == ".csv":
        return pd.read_csv(p)
    if suf in {".json", ".ndjson", ".jsonl"}:
        # ndjson/jsonl are line-delimited JSON
        lines = suf in {".ndjson", ".jsonl"}
        return pd.read_json(p, lines=lines)
    raise DataIngestError("Unsupported file type: " + suf)

def load_fixtures(path: str) -> pd.DataFrame:
    df = _read_any(path)
    # minimal normalization
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    # ensure match_id exists
    if "match_id" not in df.columns:
        df["match_id"] = df.index.astype(str)
    return df

def load_top_players(path: str) -> pd.DataFrame:
    df = _read_any(path)
    # normalize column names to expected minimal set
    return df

def load_injuries(path: str) -> pd.DataFrame:
    df = _read_any(path)
    return df

def validate_schema(df: pd.DataFrame, schema: Dict[str,str], null_threshold: float=0.2) -> Tuple[bool, List[str]]:
    errors = []
    for col, t in schema.items():
        if col not in df.columns:
            errors.append(f"missing column: {col}")
        else:
            null_rate = df[col].isna().mean()
            if null_rate > null_threshold:
                errors.append(f"high null rate {null_rate:.2f} in column {col}")
    ok = len(errors) == 0
    return ok, errors

def normalize_team_names(df: pd.DataFrame, mapping: Dict[str,str], team_col: str="team") -> pd.DataFrame:
    mapping = mapping or {}
    if team_col in df.columns:
        df["team_std"] = df[team_col].astype(str).map(lambda x: mapping.get(x, x))
    else:
        # create a column of explicit None values matching the index
        df["team_std"] = pd.Series([None] * len(df), index=df.index)
    return df