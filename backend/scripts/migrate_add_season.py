"""
One-shot: add matches.season, normalize status casing, backfill season from date.
Safe to re-run (IF NOT EXISTS + idempotent UPDATEs).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.database import SessionLocal
from app.models.match import Match, MatchStatus
from app.utils.season import season_from_date


def main():
    db = SessionLocal()
    try:
        db.execute(text(
            "ALTER TABLE matches ADD COLUMN IF NOT EXISTS season VARCHAR"
        ))
        db.commit()

        db.execute(text(
            "UPDATE matches SET status = :fin WHERE lower(status) = 'finished'"
        ), {"fin": MatchStatus.FINISHED.value})
        db.execute(text(
            "UPDATE matches SET status = :sch "
            "WHERE lower(status) IN ('scheduled', 'upcoming')"
        ), {"sch": MatchStatus.SCHEDULED.value})
        db.execute(text(
            "UPDATE matches SET status = :can "
            "WHERE lower(status) IN ('canceled', 'cancelled', 'postponed')"
        ), {"can": MatchStatus.CANCELED.value})
        db.commit()

        filled = 0
        rows = db.query(Match).filter(Match.season.is_(None)).all()
        for match in rows:
            code = season_from_date(match.match_date)
            if code:
                match.season = code
                filled += 1
        db.commit()

        total = db.query(Match).count()
        finished = db.query(Match).filter(Match.status == MatchStatus.FINISHED.value).count()
        print(
            f"Migration done — matches={total}, FINISHED={finished}, "
            f"season backfilled={filled}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
