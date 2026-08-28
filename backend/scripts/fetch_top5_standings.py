"""Fetch top-5 league standings and upsert to DB/CSV.

Default source: SofaScore (more suitable when API-Football free plan has limits).
Optional source: API-Football.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from playwright.sync_api import sync_playwright
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import SessionLocal
from app.models.team import Team


API_KEY = settings.football_api_key
BASE_URL = settings.football_api_base_url.rstrip("/")

# API-Football league ids for top-5 leagues
API_LEAGUES = [
    {"league_id": 39, "league": "Premier League"},
    {"league_id": 140, "league": "La Liga"},
    {"league_id": 78, "league": "Bundesliga"},
    {"league_id": 135, "league": "Serie A"},
    {"league_id": 61, "league": "Ligue 1"},
]

# SofaScore tournament/season ids (same set already used in existing scripts)
SOFASCORE_LEAGUES = [
    {"tournament_id": 17, "season_id": 76986, "league": "Premier League"},
    {"tournament_id": 8, "season_id": 77559, "league": "La Liga"},
    {"tournament_id": 35, "season_id": 77333, "league": "Bundesliga"},
    {"tournament_id": 23, "season_id": 76457, "league": "Serie A"},
    {"tournament_id": 34, "season_id": 77356, "league": "Ligue 1"},
]

CSV_FIELDS = [
    "fetched_at",
    "season",
    "league_id",
    "league",
    "rank",
    "team",
    "played",
    "wins",
    "draws",
    "losses",
    "goals_for",
    "goals_against",
    "goal_diff",
    "points",
    "form",
    "status",
    "description",
]


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def send_alert(message: str):
    """Send ETL alert to webhook if configured."""
    webhook_url = os.getenv("ETL_ALERT_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json={"text": message}, timeout=10)
    except requests.RequestException:
        # keep ETL behavior deterministic even if alert channel is down
        pass


def save_recovery_payload(rows: List[Dict], reason: str) -> Path:
    """Save rows for manual replay when DB write fails."""
    out_dir = Path(__file__).resolve().parents[1] / "data" / "recovery"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"standings_recovery_{ts}.json"
    payload = {
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "row_count": len(rows),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def check_db_health() -> None:
    """Fail fast when database is unavailable."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        msg = f"DB health check failed: {e}"
        send_alert(f"[ETL] {msg}")
        raise RuntimeError(msg) from e
    finally:
        db.close()


def fetch_api_standings(league_id: int, season: int, league_name: str) -> List[Dict]:
    """Fetch standings for one league and normalize output rows."""
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}
    response = requests.get(
        f"{BASE_URL}/standings",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    api_rows = payload.get("response", [])
    if not api_rows:
        return []

    standings_groups = api_rows[0].get("league", {}).get("standings", [])
    if not standings_groups:
        return []

    fetched_at = datetime.now(timezone.utc).isoformat()
    normalized = []
    # Usually first group is the main table; iterate all groups for robustness
    for group in standings_groups:
        for row in group:
            team = row.get("team", {}) or {}
            all_stats = row.get("all", {}) or {}
            goals = all_stats.get("goals", {}) or {}
            normalized.append(
                {
                    "fetched_at": fetched_at,
                    "season": season,
                    "league_id": league_id,
                    "league": league_name,
                    "rank": _safe_int(row.get("rank")),
                    "team": team.get("name", "").strip(),
                    "played": _safe_int(all_stats.get("played")),
                    "wins": _safe_int(all_stats.get("win")),
                    "draws": _safe_int(all_stats.get("draw")),
                    "losses": _safe_int(all_stats.get("lose")),
                    "goals_for": _safe_int(goals.get("for")),
                    "goals_against": _safe_int(goals.get("against")),
                    "goal_diff": _safe_int(row.get("goalsDiff")),
                    "points": _safe_int(row.get("points")),
                    "form": row.get("form") or "",
                    "status": (row.get("status") or "").strip(),
                    "description": (row.get("description") or "").strip(),
                }
            )
    return normalized


def _parse_sofascore_team_row(row: Dict, league_name: str, tournament_id: int) -> Dict:
    team = row.get("team", {}) or {}
    rank = _safe_int(row.get("position", row.get("rank")))
    played = _safe_int(row.get("matches", row.get("played")))
    wins = _safe_int(row.get("wins", row.get("win")))
    draws = _safe_int(row.get("draws", row.get("draw")))
    losses = _safe_int(row.get("losses", row.get("lose")))
    goals_for = _safe_int(row.get("scoresFor", row.get("goalsFor")))
    goals_against = _safe_int(row.get("scoresAgainst", row.get("goalsAgainst")))
    goal_diff = _safe_int(row.get("scoreDiff", row.get("goalDiff", goals_for - goals_against)))
    points = _safe_int(row.get("points"))
    promotion = row.get("promotion", {}) or {}
    description = (promotion.get("text") or "").strip()
    status = (promotion.get("id") or "").strip() if isinstance(promotion.get("id"), str) else ""

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "season": datetime.now().year,
        "league_id": tournament_id,
        "league": league_name,
        "rank": rank,
        "team": (team.get("name") or "").strip(),
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "goal_diff": goal_diff,
        "points": points,
        "form": row.get("form") or "",
        "status": status,
        "description": description,
    }


def fetch_sofascore_standings(tournament_id: int, season_id: int, league_name: str) -> List[Dict]:
    """Fetch standings from SofaScore public API."""
    url = (
        f"https://api.sofascore.com/api/v1/unique-tournament/"
        f"{tournament_id}/season/{season_id}/standings/total"
    )
    with sync_playwright() as p:
        ctx = p.request.new_context(
            extra_http_headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
            }
        )
        try:
            r = ctx.get(url, timeout=30000)
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            payload = r.json()
        finally:
            ctx.dispose()

    standings_list = payload.get("standings", [])
    if not standings_list:
        return []
    rows = standings_list[0].get("rows", [])
    return [_parse_sofascore_team_row(row, league_name, tournament_id) for row in rows]


def write_csv(rows: List[Dict], season: int) -> Path:
    """Write standings rows to timestamped CSV and latest CSV."""
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    date_tag = datetime.now().strftime("%Y%m%d")
    ts_file = out_dir / f"top5_standings_{season}_{date_tag}.csv"
    latest_file = out_dir / "top5_standings_latest.csv"

    for path in (ts_file, latest_file):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    return ts_file


def upsert_teams(rows: List[Dict]) -> Dict[str, int]:
    """Upsert standings stats into Team table."""
    db = SessionLocal()
    created = 0
    updated = 0
    processed = 0
    try:
        for row in rows:
            team_name = row["team"]
            if not team_name:
                continue
            team = db.query(Team).filter(Team.name == team_name).first()
            if team is None:
                team = Team(
                    name=team_name,
                    league=row["league"],
                    current_points=row["points"],
                    current_gd=row["goal_diff"],
                    current_rank=row["rank"],
                )
                db.add(team)
                created += 1
            else:
                team.league = row["league"]
                team.current_points = row["points"]
                team.current_gd = row["goal_diff"]
                team.current_rank = row["rank"]
                updated += 1
            processed += 1
        db.commit()
        return {"created": created, "updated": updated, "processed": processed}
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"DB upsert failed: {e}") from e
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch top-5 standings and upsert into teams table.")
    parser.add_argument("--source", choices=["sofascore", "api"], default="sofascore")
    parser.add_argument("--season", type=int, default=datetime.now().year)
    args = parser.parse_args()

    season = args.season
    source = args.source
    print(f"🚀 Fetching top-5 standings (source={source}, season={season})")

    # strict pre-flight check: fail early when DB is not available
    check_db_health()
    print("✅ DB health check passed")

    all_rows: List[Dict] = []
    if source == "api":
        if not API_KEY:
            print("❌ football_api_key not found. Please set it in .env")
            return
        for item in API_LEAGUES:
            league_id = item["league_id"]
            league_name = item["league"]
            try:
                rows = fetch_api_standings(league_id, season, league_name)
                print(f"✅ {league_name}: {len(rows)} rows")
                all_rows.extend(rows)
            except Exception as e:
                print(f"❌ {league_name}: {e}")
    else:
        for item in SOFASCORE_LEAGUES:
            league_name = item["league"]
            try:
                rows = fetch_sofascore_standings(
                    tournament_id=item["tournament_id"],
                    season_id=item["season_id"],
                    league_name=league_name,
                )
                print(f"✅ {league_name}: {len(rows)} rows")
                all_rows.extend(rows)
            except Exception as e:
                print(f"❌ {league_name}: {e}")

    if not all_rows:
        print("⚠️ No standings fetched. Nothing to save/upsert.")
        return

    csv_path = write_csv(all_rows, season)
    try:
        result = upsert_teams(all_rows)
    except RuntimeError as e:
        recovery_path = save_recovery_payload(all_rows, str(e))
        send_alert(f"[ETL] standings upsert failed. Recovery: {recovery_path}")
        print(f"❌ {e}")
        print(f"🛟 Recovery file saved: {recovery_path}")
        raise SystemExit(2)

    print("\n🎉 Done")
    print(f"📁 CSV: {csv_path}")
    print(f"📊 Total rows: {len(all_rows)}")
    print(
        f"🗄️ Team upsert - created: {result['created']}, "
        f"updated: {result['updated']}, processed: {result['processed']}"
    )

    # verify DB write count matches ingested rows
    if result["processed"] != len(all_rows):
        msg = (
            "Upsert row mismatch: "
            f"processed={result['processed']} vs csv_rows={len(all_rows)}"
        )
        recovery_path = save_recovery_payload(all_rows, msg)
        send_alert(f"[ETL] {msg}. Recovery: {recovery_path}")
        print(f"❌ {msg}")
        print(f"🛟 Recovery file saved: {recovery_path}")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
