"""
Download football-data.co.uk CSVs for multiple seasons and upsert into matches.

Default seasons: 2122–2526, leagues E0/D1/SP1/I1/F1.

  python scripts/fetch_football_data_co_uk.py
  python scripts/fetch_football_data_co_uk.py --seasons 2526
"""
import argparse
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import requests
from datetime import datetime
from pathlib import Path

from app.database import SessionLocal
from app.models.match import Match, MatchStatus
from app.utils.helpers import std_team
from app.utils.season import season_from_date

DEFAULT_SEASONS = ["2122", "2223", "2324", "2425", "2526"]
LEAGUE_FILES = [
    {"file": "E0", "league": "Premier League"},
    {"file": "D1", "league": "Bundesliga"},
    {"file": "SP1", "league": "La Liga"},
    {"file": "I1", "league": "Serie A"},
    {"file": "F1", "league": "Ligue 1"},
]
BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{file}.csv"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SNAPSHOT_DIR = DATA_DIR / "training_snapshots"
REQUEST_DELAY_SEC = 1.2
MAX_RETRIES = 3

TEAM_NAME_MAP = {
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves": "Wolverhampton Wanderers",
    "Spurs": "Tottenham",
    "Bayern Munich": "FC Bayern München",
    "Leverkusen": "Bayer Leverkusen",
    "Dortmund": "Borussia Dortmund",
    "M'gladbach": "Borussia Mönchengladbach",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "Werder Bremen": "Werder Bremen",
    "Ath Madrid": "Atlético Madrid",
    "Ath Bilbao": "Athletic Club",
    "Betis": "Real Betis",
    "Espanol": "Espanyol",
    "Vallecano": "Rayo Vallecano",
    "Inter": "Inter Milan",
    "AC Milan": "Milan",
    "Verona": "Hellas Verona",
    "Paris SG": "Paris Saint-Germain",
    "St Etienne": "Saint-Étienne",
    "Marseille": "Olympique de Marseille",
    "Lyon": "Olympique Lyonnais",
    "Betis": "Real Betis",
    "St Pauli": "FC St. Pauli",
    "Hamburg": "Hamburger SV",
    "Bochum": "VfL Bochum",
    "Levante": "Levante UD",
    "Hoffenheim": "TSG Hoffenheim",
    "Oviedo": "Real Oviedo",
}

HEADERS = {
    "User-Agent": "football-prediction-system/1.0 (local research ingest)",
}


def normalize_team(name: str) -> str:
    return TEAM_NAME_MAP.get(name.strip(), name.strip())


def parse_date(s: str) -> datetime | None:
    for fmt in ("%Y/%m/%d", "%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def to_float(val) -> float | None:
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None


def to_int(val) -> int | None:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def download_csv(season: str, file_code: str) -> pd.DataFrame | None:
    url = BASE_URL.format(season=season, file=file_code)
    print(f"  download {url}")
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            time.sleep(REQUEST_DELAY_SEC)
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
            content = resp.content.decode("latin-1")
            df = pd.read_csv(io.StringIO(content))
            if "HomeTeam" not in df.columns:
                print(f"     skip: no HomeTeam column ({list(df.columns)[:6]})")
                return None
            df = df[df["HomeTeam"].notna() & (df["HomeTeam"] != "")]
            print(f"     {len(df)} rows")
            return df
        except Exception as exc:
            last_error = exc
            print(f"     retry {attempt}/{MAX_RETRIES}: {exc}")
    print(f"  failed: {last_error}")
    return None


def save_local(df: pd.DataFrame, file_code: str, season: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{file_code}_{season}.csv"
    df.to_csv(path, index=False)
    print(f"     saved {path.name}")


def _find_existing(db, home: str, away: str, dt):
    """Match a row even when the DB still has SofaScore / short-form names."""
    hs, as_ = std_team(home), std_team(away)
    day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    candidates = (
        db.query(Match)
        .filter(Match.match_date >= day_start, Match.match_date <= day_end)
        .all()
    )
    for m in candidates:
        if m.home_team and m.away_team and std_team(m.home_team) == hs and std_team(m.away_team) == as_:
            return m
    return None


def _fill(existing, attr, val) -> bool:
    if val is not None and getattr(existing, attr) is None:
        setattr(existing, attr, val)
        return True
    return False


def upsert_league(df: pd.DataFrame, league_name: str, season: str, db) -> dict:
    created = updated = skipped = 0
    finished = MatchStatus.FINISHED.value
    scheduled = MatchStatus.SCHEDULED.value

    for _, row in df.iterrows():
        home = normalize_team(str(row.get("HomeTeam", "")))
        away = normalize_team(str(row.get("AwayTeam", "")))
        dt = parse_date(str(row.get("Date", "")))
        if not home or not away or not dt:
            skipped += 1
            continue

        home_score = to_int(row.get("FTHG"))
        away_score = to_int(row.get("FTAG"))
        ftr = str(row.get("FTR", "")).strip()
        status = finished if ftr in ("H", "D", "A") else scheduled
        row_season = season or season_from_date(dt)

        home_shots = to_int(row.get("HS"))
        away_shots = to_int(row.get("AS"))
        home_sot = to_int(row.get("HST"))
        away_sot = to_int(row.get("AST"))
        home_corners = to_int(row.get("HC"))
        away_corners = to_int(row.get("AC"))
        home_fouls = to_int(row.get("HF"))
        away_fouls = to_int(row.get("AF"))
        home_yellow = to_int(row.get("HY"))
        away_yellow = to_int(row.get("AY"))
        home_red = to_int(row.get("HR"))
        away_red = to_int(row.get("AR"))
        b365_h = to_float(row.get("B365H"))
        b365_d = to_float(row.get("B365D"))
        b365_a = to_float(row.get("B365A"))
        avg_h = to_float(row.get("AvgH"))
        avg_d = to_float(row.get("AvgD"))
        avg_a = to_float(row.get("AvgA"))

        existing = _find_existing(db, home, away, dt)

        if existing:
            changed = False
            if home_score is not None:
                existing.home_score = home_score
                changed = True
            if away_score is not None:
                existing.away_score = away_score
                changed = True
            if ftr in ("H", "D", "A"):
                existing.status = finished
                changed = True
            if row_season and existing.season != row_season:
                existing.season = row_season
                changed = True
            if existing.home_team != home:
                existing.home_team = home
                changed = True
            if existing.away_team != away:
                existing.away_team = away
                changed = True
            for attr, val in (
                ("home_shots", home_shots),
                ("away_shots", away_shots),
                ("home_shots_on_target", home_sot),
                ("away_shots_on_target", away_sot),
                ("home_corners", home_corners),
                ("away_corners", away_corners),
                ("home_fouls", home_fouls),
                ("away_fouls", away_fouls),
                ("home_yellow", home_yellow),
                ("away_yellow", away_yellow),
                ("home_red", home_red),
                ("away_red", away_red),
            ):
                if _fill(existing, attr, val):
                    changed = True
            if b365_h:
                existing.b365_home = b365_h
                changed = True
            if b365_d:
                existing.b365_draw = b365_d
                changed = True
            if b365_a:
                existing.b365_away = b365_a
                changed = True
            if avg_h:
                existing.avg_home = avg_h
                changed = True
            if avg_d:
                existing.avg_draw = avg_d
                changed = True
            if avg_a:
                existing.avg_away = avg_a
                changed = True
            if changed:
                updated += 1
        else:
            db.add(
                Match(
                    league=league_name,
                    match_date=dt,
                    season=row_season,
                    home_team=home,
                    away_team=away,
                    home_score=home_score,
                    away_score=away_score,
                    status=status,
                    home_shots=home_shots,
                    away_shots=away_shots,
                    home_shots_on_target=home_sot,
                    away_shots_on_target=away_sot,
                    home_corners=home_corners,
                    away_corners=away_corners,
                    home_fouls=home_fouls,
                    away_fouls=away_fouls,
                    home_yellow=home_yellow,
                    away_yellow=away_yellow,
                    home_red=home_red,
                    away_red=away_red,
                    b365_home=b365_h,
                    b365_draw=b365_d,
                    b365_away=b365_a,
                    avg_home=avg_h,
                    avg_draw=avg_d,
                    avg_away=avg_a,
                )
            )
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


def export_training_snapshot(db) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / "training_snapshot_latest.csv"
    rows = (
        db.query(Match)
        .filter(
            Match.status == MatchStatus.FINISHED.value,
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        )
        .order_by(Match.match_date)
        .all()
    )
    records = []
    for m in rows:
        if m.home_score > m.away_score:
            result = "H"
        elif m.home_score < m.away_score:
            result = "A"
        else:
            result = "D"
        records.append(
            {
                "match_id": m.id,
                "season": m.season,
                "league": m.league,
                "match_date": m.match_date.isoformat() if m.match_date else None,
                "home_team": m.home_team,
                "away_team": m.away_team,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "result": result,
                "b365_home": m.b365_home,
                "b365_draw": m.b365_draw,
                "b365_away": m.b365_away,
                "status": m.status,
            }
        )
    pd.DataFrame(records).to_csv(path, index=False)
    print(f"snapshot {len(records)} rows -> {path}")
    return path


def print_health_report(db) -> None:
    from sqlalchemy import func

    q = db.query(Match).filter(Match.status == MatchStatus.FINISHED.value)
    total = q.count()
    print("\n--- training health ---")
    print(f"FINISHED: {total}")
    if total == 0:
        return
    dates = db.query(func.min(Match.match_date), func.max(Match.match_date)).filter(
        Match.status == MatchStatus.FINISHED.value
    ).one()
    print(f"date range: {dates[0]} -> {dates[1]}")

    h = d = a = 0
    missing_odds = 0
    for m in q.all():
        if m.home_score is None or m.away_score is None:
            continue
        if m.home_score > m.away_score:
            h += 1
        elif m.home_score < m.away_score:
            a += 1
        else:
            d += 1
        if m.b365_home is None:
            missing_odds += 1
    scored = h + d + a
    print(f"H/D/A: {h}/{d}/{a}" + (f"  ({h/scored:.1%}/{d/scored:.1%}/{a/scored:.1%})" if scored else ""))
    print(f"B365 missing: {missing_odds}/{total} ({missing_odds / total:.1%})")
    print("by league:")
    for league, count in (
        db.query(Match.league, func.count(Match.id))
        .filter(Match.status == MatchStatus.FINISHED.value)
        .group_by(Match.league)
        .order_by(Match.league)
        .all()
    ):
        print(f"  {league}: {count}")
    print("by season:")
    for season, count in (
        db.query(Match.season, func.count(Match.id))
        .filter(Match.status == MatchStatus.FINISHED.value)
        .group_by(Match.season)
        .order_by(Match.season)
        .all()
    ):
        print(f"  {season}: {count}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=DEFAULT_SEASONS,
        help="Season codes, e.g. 2122 2223 … 2526",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 55)
    print(f"football-data.co.uk ingest seasons={args.seasons}")
    print("=" * 55)

    db = SessionLocal()
    total = {"created": 0, "updated": 0, "skipped": 0}
    try:
        for season in args.seasons:
            for league in LEAGUE_FILES:
                print(f"\n[{season}] {league['league']}")
                df = download_csv(season, league["file"])
                if df is None:
                    continue
                save_local(df, league["file"], season)
                result = upsert_league(df, league["league"], season, db)
                for key in total:
                    total[key] += result[key]
                print(
                    f"  created={result['created']} "
                    f"updated={result['updated']} skipped={result['skipped']}"
                )

        print(
            f"\ndone created={total['created']} "
            f"updated={total['updated']} skipped={total['skipped']}"
        )
        export_training_snapshot(db)
        print_health_report(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
