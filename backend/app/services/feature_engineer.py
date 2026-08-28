"""
app/services/feature_engineer.py

Feature engineering pipeline:
  - standings   : rank, points, gd, wins, form
  - injuries    : injured player count per team
  - injury_alert: key player (top scorer/assister/rated) injured → impact score
  - top_players : team offensive strength (goals, assists, rating)
  - DB history  : recent form (last 5), home/away win rate
"""

import glob
import os
import re
from pathlib import Path
from typing import Optional, Dict

import pandas as pd
from sqlalchemy.orm import Session

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# ── Helpers ──────────────────────────────────────────────────────────────

def _latest_csv(pattern: str) -> Optional[Path]:
    """回傳符合 glob pattern 中最新的檔案"""
    files = sorted(glob.glob(str(DATA_DIR / pattern)), key=os.path.getmtime, reverse=True)
    return Path(files[0]) if files else None

def _load_standings() -> pd.DataFrame:
    f = _latest_csv("top5_standings_latest.csv") or _latest_csv("top5_standings_*.csv")
    if f is None:
        return pd.DataFrame()
    df = pd.read_csv(f)
    # 統一 team 欄位名稱
    df = df.rename(columns={"team": "team_name"})
    return df

def _load_injuries() -> pd.DataFrame:
    """合併五大聯賽傷員表"""
    files = list(DATA_DIR.glob("*_teams_injuries_sportsgambler.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    # 過濾掉 header row 誤入資料的情況
    df = df[df["player"] != "Name"].copy()
    if "team_std" in df.columns:
        df["team_std"] = df["team_std"].map(_std_name)
    return df

def _load_injury_alerts() -> pd.DataFrame:
    """合併五大聯賽關鍵球員傷員報告"""
    files = list(DATA_DIR.glob("*_injury_alert_report.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def _load_top_players() -> pd.DataFrame:
    files = list(DATA_DIR.glob("*_team_top_players_sofascore_std.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    # ← 加這行：統一 team_std 為小寫無符號格式
    if "team_std" in df.columns:
        df["team_std"] = df["team_std"].map(_std_name)
    return df

def _std_name(name: str) -> str:
    """Normalise team name: unidecode accents → lowercase → strip non-alphanum."""
    try:
        from unidecode import unidecode
        name = unidecode(str(name))
    except ImportError:
        name = str(name)
    return re.sub(r"[^a-z0-9]", "", name.lower())

# ── DB-based features ─────────────────────────────────────────────────────

def _compute_team_history(db: Session) -> Dict[str, dict]:
    """
    從 DB matches 計算每支球隊近期表現：
    - 近5場勝率
    - 主場勝率（近10場）
    - 客場勝率（近10場）
    """
    from app.models.match import Match
    from sqlalchemy import or_

    history: Dict[str, dict] = {}

    matches = (
        db.query(Match)
        .filter(
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        )
        .order_by(Match.match_date.desc())
        .all()
    )

    # 建立每隊的主客場紀錄
    home_records: Dict[str, list] = {}
    away_records: Dict[str, list] = {}

    for m in matches:
        h, a = m.home_team, m.away_team
        if not h or not a:
            continue
        h_win = 1 if m.home_score > m.away_score else 0
        a_win = 1 if m.away_score > m.home_score else 0
        home_records.setdefault(h, []).append(h_win)
        away_records.setdefault(a, []).append(a_win)

    all_teams = set(home_records.keys()) | set(away_records.keys())
    for team in all_teams:
        h_list = home_records.get(team, [])[:10]
        a_list = away_records.get(team, [])[:10]
        recent = (h_list + a_list)
        recent_5 = sorted(
            [(i, v) for i, v in enumerate(recent)],
            key=lambda x: x[0]
        )[:5]
        recent_5_wins = [v for _, v in recent_5]

        history[team] = {
            "home_win_rate": round(sum(h_list) / len(h_list), 3) if h_list else 0.5,
            "away_win_rate": round(sum(a_list) / len(a_list), 3) if a_list else 0.5,
            "recent_form_rate": round(sum(recent_5_wins) / len(recent_5_wins), 3) if recent_5_wins else 0.5,
        }

    return history

# ── Main builder ──────────────────────────────────────────────────────────

def build_feature_matrix(
    fixtures_df: pd.DataFrame,
    db: Optional[Session] = None,
    options: Dict = None,
) -> pd.DataFrame:
    """
    輸入: fixtures_df（必須有 home_team / away_team / league 欄位）
    輸出: feature matrix（每場比賽一行）
    """
    opts = options or {}
    df = fixtures_df.copy()

    # 標準化欄位名稱
    if "home" in df.columns and "home_team" not in df.columns:
        df = df.rename(columns={"home": "home_team", "away": "away_team"})

    if "match_id" not in df.columns:
        df["match_id"] = df.index.astype(str)

    df["home_std"] = df["home_team"].map(_std_name)
    df["away_std"] = df["away_team"].map(_std_name)

    # ── 1. Standings features ─────────────────────────────────────────────
    standings = _load_standings()
    if not standings.empty:
        standings["team_std"] = standings["team_name"].map(_std_name)
        st_cols = ["team_std", "rank", "points", "goal_diff", "wins", "draws",
                   "losses", "played", "goals_for", "goals_against"]
        st = standings[[c for c in st_cols if c in standings.columns]].copy()

        for side, std_col in [("home", "home_std"), ("away", "away_std")]:
            merged = df[[std_col]].merge(
                st.rename(columns={"team_std": std_col}),
                on=std_col, how="left"
            )
            for col in [c for c in st_cols if c != "team_std"]:
                if col in merged.columns:
                    df[f"{side}_{col}"] = merged[col].values

    # ── 2. Injury count ───────────────────────────────────────────────────
    injuries = _load_injuries()
    inj_counts: Dict[str, int] = {}
    if not injuries.empty and "team_std" in injuries.columns:
        valid = injuries[injuries["player"].notna() & (injuries["player"] != "")]
        inj_counts = valid.groupby("team_std").size().to_dict()

    df["home_inj_count"] = df["home_std"].map(lambda t: inj_counts.get(t, 0))
    df["away_inj_count"] = df["away_std"].map(lambda t: inj_counts.get(t, 0))

    # ── 3. Key player injury impact ───────────────────────────────────────
    alerts = _load_injury_alerts()
    alert_impact: Dict[str, float] = {}
    if not alerts.empty and "team" in alerts.columns:
        alerts["team_std"] = alerts["team"].map(_std_name)
        # 每位關鍵傷員的影響分（進球*2 + 助攻 + 評分*0.5），加總後取 log 壓縮
        alerts["goals"] = pd.to_numeric(alerts.get("goals", 0), errors="coerce").fillna(0)
        alerts["assists"] = pd.to_numeric(alerts.get("assists", 0), errors="coerce").fillna(0)
        alerts["rating"] = pd.to_numeric(alerts.get("rating", 0), errors="coerce").fillna(0)
        alerts["impact"] = alerts["goals"] * 2 + alerts["assists"] + alerts["rating"] * 0.5
        alert_impact = alerts.groupby("team_std")["impact"].sum().to_dict()

    df["home_key_inj_impact"] = df["home_std"].map(lambda t: round(alert_impact.get(t, 0.0), 2))
    df["away_key_inj_impact"] = df["away_std"].map(lambda t: round(alert_impact.get(t, 0.0), 2))

    # ── 4. Top players offensive strength ─────────────────────────────────
    top = _load_top_players()
    team_offense: Dict[str, dict] = {}
    if not top.empty and "team_std" in top.columns:
        top["goals"] = pd.to_numeric(top.get("goals", 0), errors="coerce").fillna(0)
        top["assists"] = pd.to_numeric(top.get("assists", 0), errors="coerce").fillna(0)
        top["rating"] = pd.to_numeric(top.get("rating", 0), errors="coerce").fillna(0)
        # 只取每隊評分榜前3
        top3 = (
            top[top["stat_type"] == "rating"]
            .sort_values("rating", ascending=False)
            .groupby("team_std")
            .head(3)
            .groupby("team_std")
            .agg(
                top3_goals=("goals", "sum"),
                top3_assists=("assists", "sum"),
                top3_avg_rating=("rating", "mean"),
            )
        )
        team_offense = top3.to_dict("index")

    for side, std_col in [("home", "home_std"), ("away", "away_std")]:
        df[f"{side}_top3_goals"] = df[std_col].map(
            lambda t: team_offense.get(t, {}).get("top3_goals", 0))
        df[f"{side}_top3_assists"] = df[std_col].map(
            lambda t: team_offense.get(t, {}).get("top3_assists", 0))
        df[f"{side}_top3_avg_rating"] = df[std_col].map(
            lambda t: team_offense.get(t, {}).get("top3_avg_rating", 0.0))

    # ── 5. DB historical form ─────────────────────────────────────────────
    if db is not None:
        team_history = _compute_team_history(db)
        for side in ["home", "away"]:
            team_col = f"{side}_team"
            df[f"{side}_home_win_rate"] = df[team_col].map(
                lambda t: team_history.get(t, {}).get("home_win_rate", 0.5))
            df[f"{side}_away_win_rate"] = df[team_col].map(
                lambda t: team_history.get(t, {}).get("away_win_rate", 0.5))
            df[f"{side}_recent_form"] = df[team_col].map(
                lambda t: team_history.get(t, {}).get("recent_form_rate", 0.5))
    else:
        for side in ["home", "away"]:
            df[f"{side}_home_win_rate"] = 0.5
            df[f"{side}_away_win_rate"] = 0.5
            df[f"{side}_recent_form"] = 0.5

    # ── 6. 填補 NaN ───────────────────────────────────────────────────────
    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df


# ── Quick test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    # 用 DB 的未來賽程做測試
    from app.database import SessionLocal
    from app.models.match import Match

    db = SessionLocal()
    upcoming = (
        db.query(Match)
        .filter(Match.status == "SCHEDULED")
        .order_by(Match.match_date)
        .limit(20)
        .all()
    )
    db.close()

    if not upcoming:
        print("❌ DB 沒有未來賽程，先跑 ingest_sofascore_csv.py")
    else:
        rows = [{"home_team": m.home_team, "away_team": m.away_team,
                 "league": m.league, "match_date": m.match_date,
                 "match_id": m.id} for m in upcoming]
        fix_df = pd.DataFrame(rows)

        db2 = SessionLocal()
        feat = build_feature_matrix(fix_df, db=db2)
        db2.close()

        print(f"✅ Feature matrix: {feat.shape[0]} 場比賽 × {feat.shape[1]} 個 features")
        print(feat.columns.tolist())
        print(feat.head(3).to_string())
