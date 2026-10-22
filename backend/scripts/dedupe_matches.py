"""
Merge duplicate matches that are the same fixture under different team names.

Keeps the row with B365 / shots when possible, copies missing stats onto it,
then deletes extras. Display names are rewritten to the longest alias seen.

  docker compose exec api python scripts/dedupe_matches.py --dry-run
  docker compose exec api python scripts/dedupe_matches.py
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.match import Match
from app.utils.helpers import std_team

MERGE_FIELDS = (
    "home_score",
    "away_score",
    "home_shots",
    "away_shots",
    "home_shots_on_target",
    "away_shots_on_target",
    "home_corners",
    "away_corners",
    "home_fouls",
    "away_fouls",
    "home_yellow",
    "away_yellow",
    "home_red",
    "away_red",
    "b365_home",
    "b365_draw",
    "b365_away",
    "avg_home",
    "avg_draw",
    "avg_away",
    "odds_home",
    "odds_draw",
    "odds_away",
    "api_fixture_id",
    "home_team_id",
    "away_team_id",
    "season",
    "league",
)


def _day(m: Match):
    return m.match_date.date() if m.match_date else None


def _group_key(m: Match):
    if not m.home_team or not m.away_team or not m.match_date:
        return None
    return (_day(m), std_team(m.home_team), std_team(m.away_team))


def _richness(m: Match) -> tuple:
    return (
        int(m.b365_home is not None),
        int(m.home_shots is not None),
        int(m.home_score is not None),
        int(m.api_fixture_id is not None),
        len(m.home_team or "") + len(m.away_team or ""),
        -(m.id or 0),
    )


def _preferred_name(names: list[str]) -> str:
    return max(names, key=lambda n: (len(n), n))


def _merge(keeper: Match, donor: Match) -> list[str]:
    filled = []
    for field in MERGE_FIELDS:
        if getattr(keeper, field) is None and getattr(donor, field) is not None:
            setattr(keeper, field, getattr(donor, field))
            filled.append(field)
    return filled


def _collect_groups(db) -> dict:
    groups = defaultdict(list)
    orphan = 0
    for m in db.query(Match).all():
        key = _group_key(m)
        if key is None:
            orphan += 1
            continue
        groups[key].append(m)
    return groups, orphan


def run(dry_run: bool) -> int:
    db = SessionLocal()
    try:
        groups, orphan = _collect_groups(db)
        dups = {k: v for k, v in groups.items() if len(v) > 1}
        extra = sum(len(v) - 1 for v in dups.values())
        print(f"matches: {sum(len(v) for v in groups.values())}  orphan: {orphan}")
        print(f"unique fixtures: {len(groups)}")
        print(f"duplicate groups: {len(dups)}  extra rows: {extra}")

        if not dups:
            print("nothing to merge")
            return 0

        delete_ids = []
        for key, rows in sorted(dups.items()):
            ranked = sorted(rows, key=_richness, reverse=True)
            keeper, losers = ranked[0], ranked[1:]
            filled = []
            for donor in losers:
                filled.extend(_merge(keeper, donor))
            homes = [m.home_team for m in rows if m.home_team]
            aways = [m.away_team for m in rows if m.away_team]
            keeper.home_team = _preferred_name(homes)
            keeper.away_team = _preferred_name(aways)
            if keeper.status != "FINISHED" and any(m.status == "FINISHED" for m in rows):
                keeper.status = "FINISHED"
            delete_ids.extend(m.id for m in losers)
            if filled or losers:
                print(
                    f"  keep {keeper.id} {key[0]} {keeper.home_team} vs {keeper.away_team} "
                    f"(drop {[m.id for m in losers]}"
                    f"{', fill ' + ','.join(filled) if filled else ''})"
                )

        if dry_run:
            print(f"\ndry-run: would delete {len(delete_ids)} rows")
            db.rollback()
            return 0

        if delete_ids:
            deleted = (
                db.query(Match)
                .filter(Match.id.in_(delete_ids))
                .delete(synchronize_session=False)
            )
            db.commit()
            print(f"\ndeleted {deleted} duplicate matches")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Dedupe matches by alias + date")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
