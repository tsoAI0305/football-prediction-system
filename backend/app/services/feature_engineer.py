# Minimal feature engineering / joiner skeleton
import pandas as pd
from typing import Dict, Optional

def build_feature_matrix(fixtures_df: pd.DataFrame,
                         teams_df: Optional[pd.DataFrame],
                         top_players_df: pd.DataFrame,
                         injuries_df: pd.DataFrame,
                         options: Dict = None) -> pd.DataFrame:
    """
    Minimal feature builder:
    - ensures match_id present
    - computes simple team-level aggregates from top_players and injuries
    """
    opts = options or {}
    top_k = opts.get("top_k_players", 3)

    df = fixtures_df.copy()
    if "match_id" not in df.columns:
        df["match_id"] = df.index.astype(str)

    # example: compute number of injured players per fixture (very minimal: join via team name)
    df["home_team_std"] = df.get("home_team", df.get("home_team_name", "")).astype(str)
    df["away_team_std"] = df.get("away_team", df.get("away_team_name", "")).astype(str)

    # injuries_df expected to have team_std and player columns
    inj_counts = {}
    if injuries_df is not None and "team_std" in injuries_df.columns:
        grp = injuries_df.groupby("team_std").size()
        inj_counts = grp.to_dict()

    def inj_for_team(team_std):
        return int(inj_counts.get(team_std, 0))

    df["home_inj_count"] = df["home_team_std"].map(inj_for_team).fillna(0).astype(int)
    df["away_inj_count"] = df["away_team_std"].map(inj_for_team).fillna(0).astype(int)

    # placeholder numeric features
    df["num_features"] = df["home_inj_count"] + df["away_inj_count"]

    # ensure numeric dtype
    df["num_features"] = df["num_features"].astype(float)

    # minimal feature set: match_id, date, home_team_std, away_team_std, num_features
    out_cols = ["match_id", "date", "home_team_std", "away_team_std", "num_features"]
    for c in out_cols:
        if c not in df.columns:
            df[c] = None
    return df[out_cols]