"""History router — prediction history with CSV result join and DB sync."""
import csv as _csv
import glob as _glob
import json
import os
import re as _re
from datetime import date as _date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.helpers import std_team as _std

router = APIRouter(tags=["History"])

_PREDICTIONS_FILE = os.path.join("data", "final_predictions.json")

# Map long-form prediction strings to H/D/A
_PRED_MAP = {
    "home_win": "H", "draw": "D", "away_win": "A",
    "H": "H", "D": "D", "A": "A",
}


# ── CSV result loader ─────────────────────────────────────────────────────────

def _load_csv_results() -> dict:
    """Load match results into (date_iso, home_std, away_std) → (home_score, away_score).

    Sources checked in order (first writer wins):
      1. data/match_results.csv  — output of update_results_and_retrain.py
      2. data/??_????.csv        — football-data.co.uk league files
    """
    lookup: dict = {}

    def _ingest(date_raw: str, home_raw: str, away_raw: str,
                score_h: str, score_a: str) -> None:
        if not (date_raw and home_raw and away_raw and score_h and score_a):
            return
        try:
            sh = int(float(score_h))
            sa = int(float(score_a))
        except (ValueError, TypeError):
            return
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

    # 1. match_results.csv
    mr = os.path.join("data", "match_results.csv")
    if os.path.exists(mr):
        try:
            with open(mr, encoding="utf-8-sig", newline="") as f:
                for row in _csv.DictReader(f):
                    _ingest(
                        row.get("date", "") or row.get("match_date", ""),
                        row.get("home_team", ""),
                        row.get("away_team", ""),
                        row.get("home_score", "") or row.get("FTHG", ""),
                        row.get("away_score", "") or row.get("FTAG", ""),
                    )
        except Exception:
            pass

    # 2. football-data.co.uk files
    for path in _glob.glob(os.path.join("data", "*.csv")):
        fname = os.path.basename(path)
        if not _re.match(r"^[A-Z][A-Z0-9]_\d{4}\.csv$", fname):
            continue
        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                for row in _csv.DictReader(f):
                    _ingest(
                        row.get("Date", ""),
                        row.get("HomeTeam", ""),
                        row.get("AwayTeam", ""),
                        row.get("FTHG", ""),
                        row.get("FTAG", ""),
                    )
        except Exception:
            pass

    return lookup


# ── DB prediction sync ────────────────────────────────────────────────────────

def _sync_db_predictions(csv_results: dict, db: Session, today_str: str) -> int:
    """Scan DB predictions with missing actual_result and fill from csv_results.

    For each DB Prediction where:
      - actual_result is NULL
      - the linked Match date <= today

    Looks up (date, home_std, away_std) in csv_results and writes:
      - Prediction.actual_result  (H/D/A enum)
      - Prediction.is_correct     (bool)
      - Match.home_score / away_score / status=FINISHED

    Returns count of predictions updated.
    """
    from app.models.prediction import Prediction as PModel, PredictionResult
    from app.models.match import Match as MModel

    updated = 0
    try:
        preds = (
            db.query(PModel)
            .filter(PModel.actual_result.is_(None))
            .all()
        )
        for pred in preds:
            if not pred.match_id:
                continue
            match = db.query(MModel).filter(MModel.id == pred.match_id).first()
            if not match or not match.match_date:
                continue
            match_date = match.match_date.strftime("%Y-%m-%d")
            if match_date > today_str:
                continue
            if not match.home_team or not match.away_team:
                continue

            key = (match_date, _std(match.home_team), _std(match.away_team))
            if key not in csv_results:
                continue

            sh, sa = csv_results[key]
            actual = "H" if sh > sa else ("D" if sh == sa else "A")

            try:
                pred.actual_result = PredictionResult(actual)
            except ValueError:
                continue

            pred_val = getattr(pred.predicted_result, "value",
                               str(pred.predicted_result) if pred.predicted_result else "")
            pred.is_correct = (actual == pred_val) if pred_val else False

            if match.home_score is None:
                match.home_score = sh
                match.away_score = sa
                match.status = "FINISHED"

            updated += 1

        if updated > 0:
            db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    return updated


# ── Score resolver ────────────────────────────────────────────────────────────

def _resolve_scores(
    match_date_str: str, home_team: str, away_team: str,
    match_id, predicted_result: str, ou_pick: str,
    csv_results: dict, today_str: str, db: Session,
) -> dict:
    """Try DB then CSV to find actual scores. Returns score fields dict."""
    from app.models.match import Match as MModel
    from sqlalchemy import or_

    actual_home = actual_away = actual_result = is_correct = ou_hit = None

    # DB lookup
    try:
        if match_id is not None:
            match = db.query(MModel).filter(
                or_(MModel.id == match_id, MModel.api_fixture_id == match_id)
            ).first()
            if match is None and match_date_str and home_team and away_team:
                match = db.query(MModel).filter(
                    MModel.home_team == home_team,
                    MModel.away_team == away_team,
                ).first()
            if match and match.home_score is not None and match.away_score is not None:
                actual_home = match.home_score
                actual_away = match.away_score
    except Exception:
        pass

    # CSV fallback
    if actual_home is None and match_date_str and match_date_str <= today_str:
        h_std = _std(home_team or "")
        a_std = _std(away_team or "")
        key = (match_date_str, h_std, a_std)
        if key in csv_results:
            actual_home, actual_away = csv_results[key]
        else:
            for (kd, kh, ka), scores in csv_results.items():
                if kd == match_date_str and kh == h_std and ka == a_std:
                    actual_home, actual_away = scores
                    break

    # Derive result + hit flags
    if actual_home is not None and actual_away is not None:
        actual_result = "H" if actual_home > actual_away else (
            "D" if actual_home == actual_away else "A"
        )
        pred_std = _PRED_MAP.get(predicted_result or "", predicted_result)
        is_correct = bool(actual_result == pred_std) if pred_std else False
        if ou_pick:
            total = actual_home + actual_away
            ou_hit = bool(ou_pick == ("OVER" if total > 2.5 else "UNDER"))

    return {
        "actual_home_score": actual_home,
        "actual_away_score": actual_away,
        "actual_result":     actual_result,
        "is_correct":        is_correct,
        "is_hit":            is_correct,  # explicit bool alias for frontend
        "ou_hit":            ou_hit,
    }


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/api/history/")
async def get_history(
    limit: int = Query(50, le=200),
    only_completed: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Prediction history with automatic result join from CSV sources.

    Flow:
    1. Load csv_results from match_results.csv (primary) + football-data.co.uk CSVs.
    2. Sync DB Prediction rows that have missing actual_result (writes back to DB).
    3. Iterate final_predictions.json; resolve scores per match.
    4. Return structured response with is_hit as a real boolean.
    """
    today_str = _date.today().isoformat()

    csv_results: dict = {}
    try:
        csv_results = _load_csv_results()
    except Exception:
        pass

    # Sync DB records with CSV results (background side-effect)
    try:
        _sync_db_predictions(csv_results, db, today_str)
    except Exception:
        pass

    history: list[dict] = []

    if os.path.exists(_PREDICTIONS_FILE):
        try:
            with open(_PREDICTIONS_FILE, "r", encoding="utf-8") as f:
                raw_preds = json.load(f)
        except Exception:
            raw_preds = []

        for idx, pred in enumerate(raw_preds[:limit], 1):
            try:
                match_id       = pred.get("match_id")
                pred_detail    = pred.get("prediction") or {}
                predicted_res  = pred_detail.get("prediction")
                ou_pick        = pred_detail.get("ou_pick")
                match_date     = pred.get("date", "")
                home_team      = pred.get("home_team", "")
                away_team      = pred.get("away_team", "")

                scores = _resolve_scores(
                    match_date, home_team, away_team,
                    match_id, predicted_res, ou_pick,
                    csv_results, today_str, db,
                )

                has_score = scores["actual_home_score"] is not None
                is_past   = bool(match_date and match_date <= today_str)

                if has_score:
                    status = "已完賽"
                elif is_past:
                    status = "結果待確認"
                else:
                    status = "未開賽"

                history.append({
                    "id":              idx,
                    "match_id":        match_id,
                    "date":            match_date,
                    "time":            pred.get("time"),
                    "league":          pred.get("league"),
                    "home_team":       home_team,
                    "away_team":       away_team,
                    "predicted_result": predicted_res,
                    "predicted_ou":    ou_pick,
                    "confidence":      pred_detail.get("confidence"),
                    "over25_prob":     pred_detail.get("over25_prob"),
                    "status":          status,
                    **scores,
                })
            except Exception:
                pass

    else:
        # Fallback: read from DB predictions table
        from app.models.prediction import Prediction as PModel
        from app.models.match import Match as MModel

        try:
            preds = (
                db.query(PModel)
                .order_by(PModel.created_at.desc())
                .limit(limit)
                .all()
            )
            for idx, p in enumerate(preds, 1):
                try:
                    match = db.query(MModel).filter(MModel.id == p.match_id).first()
                    home_team  = match.home_team if match else None
                    away_team  = match.away_team if match else None
                    match_date = (
                        match.match_date.strftime("%Y-%m-%d")
                        if match and match.match_date else None
                    )
                    home_s = match.home_score if match else None
                    away_s = match.away_score if match else None

                    if home_s is None and match_date and match_date <= today_str and home_team and away_team:
                        key = (match_date, _std(home_team), _std(away_team))
                        if key in csv_results:
                            home_s, away_s = csv_results[key]

                    has_score = home_s is not None
                    is_past   = bool(match_date and match_date <= today_str)
                    status    = "已完賽" if has_score else ("結果待確認" if is_past else "未開賽")

                    actual_res = None
                    is_correct = None
                    is_hit_val = False
                    if home_s is not None and away_s is not None:
                        actual_res = "H" if home_s > away_s else ("D" if home_s == away_s else "A")
                        pred_val = getattr(p.predicted_result, "value", None)
                        is_correct = bool(actual_res == pred_val) if pred_val else False
                        is_hit_val = is_correct

                    history.append({
                        "id":               idx,
                        "match_id":         p.match_id,
                        "date":             match_date,
                        "time":             (match.match_date.strftime("%H:%M")
                                             if match and match.match_date else None),
                        "league":           match.league if match else None,
                        "home_team":        home_team,
                        "away_team":        away_team,
                        "predicted_result": getattr(p.predicted_result, "value", None),
                        "predicted_ou":     None,
                        "confidence":       p.ai_score / 10 if p.ai_score else None,
                        "over25_prob":      None,
                        "status":           status,
                        "actual_home_score": home_s,
                        "actual_away_score": away_s,
                        "actual_result":    actual_res,
                        "is_correct":       is_correct,
                        "is_hit":           is_hit_val,
                        "ou_hit":           None,
                    })
                except Exception:
                    pass
        except Exception:
            pass

    if only_completed:
        history = [r for r in history if r.get("actual_result") is not None]

    completed = [r for r in history if r.get("actual_result") is not None]
    correct   = sum(1 for r in completed if r.get("is_correct"))
    accuracy  = round(100.0 * correct / len(completed), 1) if completed else 0.0

    ou_done    = [r for r in history if r.get("ou_hit") is not None]
    ou_correct = sum(1 for r in ou_done if r["ou_hit"])
    ou_acc     = round(100.0 * ou_correct / len(ou_done), 1) if ou_done else 0.0

    return {
        "total":       len(history),
        "completed":   len(completed),
        "correct":     correct,
        "accuracy":    accuracy,
        "ou_correct":  ou_correct,
        "ou_accuracy": ou_acc,
        "records":     history,
    }
