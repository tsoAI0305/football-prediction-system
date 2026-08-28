"""FastAPI main application."""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os
from sqlalchemy.orm import Session
from app.routers import matches, predictions, health, teams
from app.routers import history as history_router
from app.config import settings
from app.database import get_db
from app.models.prediction import Prediction

# Central logging configuration
from app.services.logging_config import configure_logging
configure_logging()

app = FastAPI(
    title="Football Prediction API",
    version="1.0.0"
)


app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(history_router.router)  # mounts /api/history/ directly

_cors_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Football Prediction API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/predictions/")
async def get_predictions(
    league: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
):
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        all_predictions = json.load(f)
    
    filtered = all_predictions
    
    if league:
        filtered = [p for p in filtered if p["league"].lower() == league.lower()]
    
    if team:
        filtered = [p for p in filtered 
                   if team.lower() in p["home_team"].lower() 
                   or team.lower() in p["away_team"].lower()]
    
    if date:
        filtered = [p for p in filtered if p["date"] == date]
    
    return {"total": len(filtered), "predictions": filtered}

@app.get("/api/predictions/leagues")
async def get_leagues():
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料��生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    leagues = list(set(p["league"] for p in predictions))
    
    return {"leagues": sorted(leagues), "count": len(leagues)}

@app.get("/api/predictions/teams")
async def get_teams(league: Optional[str] = None):
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    if league:
        predictions = [p for p in predictions if p["league"] == league]
    
    teams = set()
    for p in predictions:
        teams.add(p["home_team"])
        teams.add(p["away_team"])
    
    return {"teams": sorted(list(teams)), "count": len(teams)}

def _load_csv_results() -> dict:  # kept for any legacy internal callers
    """Load match results into a lookup dict from all available result sources.

    Sources (in order of preference):
    1. match_results.csv — output of update_results_and_retrain.py (when present)
    2. football-data.co.uk league files (e.g. E0_2526.csv, D1_2526.csv)

    Key: (date_iso, home_std, away_std)  →  (home_score, away_score)
    All team names are normalised through std_team() before storage so that
    fuzzy-matched queries ("Eintracht Frankfurt" vs "Ein Frankfurt") resolve
    to the same canonical key.
    """
    from app.utils.helpers import std_team as _std
    import csv as _csv
    import glob as _glob
    import re as _re

    lookup: dict = {}

    def _ingest_row(date_raw: str, home_raw: str, away_raw: str,
                    score_h: str, score_a: str) -> None:
        """Parse one result row and insert into lookup (does not overwrite)."""
        if not (date_raw and home_raw and away_raw and score_h and score_a):
            return
        try:
            sh = int(float(score_h))
            sa = int(float(score_a))
        except (ValueError, TypeError):
            return
        # Accept YYYY-MM-DD directly or convert from DD/MM/YYYY
        date_raw = date_raw.strip()
        try:
            if "-" in date_raw and len(date_raw) == 10:
                date_iso = date_raw
            else:
                parts = date_raw.split("/")
                if len(parts) == 3:
                    date_iso = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                else:
                    return
        except Exception:
            return
        key = (date_iso, _std(home_raw.strip()), _std(away_raw.strip()))
        if key not in lookup:
            lookup[key] = (sh, sa)

    # ── 1. match_results.csv (generated by update_results_and_retrain.py) ──
    mr_path = os.path.join("data", "match_results.csv")
    if os.path.exists(mr_path):
        try:
            with open(mr_path, encoding="utf-8-sig", newline="") as f:
                reader = _csv.DictReader(f)
                for row in reader:
                    _ingest_row(
                        row.get("date", "") or row.get("match_date", ""),
                        row.get("home_team", ""),
                        row.get("away_team", ""),
                        row.get("home_score", "") or row.get("FTHG", ""),
                        row.get("away_score", "") or row.get("FTAG", ""),
                    )
        except Exception:
            pass

    # ── 2. football-data.co.uk league files ───────────────────────────────
    for path in _glob.glob(os.path.join("data", "*.csv")):
        fname = os.path.basename(path)
        if not _re.match(r"^[A-Z][A-Z0-9]_\d{4}\.csv$", fname):
            continue
        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                reader = _csv.DictReader(f)
                for row in reader:
                    _ingest_row(
                        row.get("Date", ""),
                        row.get("HomeTeam", ""),
                        row.get("AwayTeam", ""),
                        row.get("FTHG", ""),
                        row.get("FTAG", ""),
                    )
        except Exception:
            pass

    return lookup


@app.get("/api/history/stats")
async def get_history_stats():
    """取得預測統計"""
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="尚無預測記錄")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    total = len(predictions)
    home_wins = sum(1 for p in predictions if p["prediction"]["prediction"] == "home_win")
    draws = sum(1 for p in predictions if p["prediction"]["prediction"] == "draw")
    away_wins = sum(1 for p in predictions if p["prediction"]["prediction"] == "away_win")
    
    avg_confidence = sum(p["prediction"]["confidence"] for p in predictions) / total if total > 0 else 0
    
    league_stats = {}
    for pred in predictions:
        league = pred["league"]
        if league not in league_stats:
            league_stats[league] = 0
        league_stats[league] += 1
    
    return {
        "total_predictions": total,
        "result_distribution": {
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins
        },
        "average_confidence": round(avg_confidence, 2),
        "league_distribution": league_stats,
        "accuracy_rate": None
    }
