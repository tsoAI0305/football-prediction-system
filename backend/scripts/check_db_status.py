"""Phase 0 inventory: match counts, status casing, date range, odds coverage."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, text

from app.database import SessionLocal
from app.models.match import Match

db = SessionLocal()

print("=" * 70)
print("Phase 0 訓練集盤點")
print("=" * 70)

total = db.query(Match).count()
print(f"\n總比賽數: {total}")

status_rows = (
    db.query(Match.status, func.count(Match.id))
    .group_by(Match.status)
    .order_by(func.count(Match.id).desc())
    .all()
)
print("\nstatus 分佈:")
if status_rows:
    for status, count in status_rows:
        print(f"  {status!r}: {count}")
else:
    print("  （無資料）")

finished = db.query(Match).filter(Match.status == "FINISHED").count()
finished_lower = db.query(Match).filter(Match.status == "finished").count()
finished_any_case = db.query(Match).filter(func.lower(Match.status) == "finished").count()
with_scores = (
    db.query(Match)
    .filter(Match.home_score.isnot(None), Match.away_score.isnot(None))
    .count()
)
trainable = (
    db.query(Match)
    .filter(
        Match.status == "FINISHED",
        Match.home_score.isnot(None),
        Match.away_score.isnot(None),
    )
    .count()
)
trainable_if_case_fixed = (
    db.query(Match)
    .filter(
        func.lower(Match.status) == "finished",
        Match.home_score.isnot(None),
        Match.away_score.isnot(None),
    )
    .count()
)

print(f"\nFINISHED（訓練腳本認得的）: {finished}")
print(f"finished（小寫，會被 train_model 跳過）: {finished_lower}")
print(f"任何大小寫 finished: {finished_any_case}")
print(f"有比分: {with_scores}")
print(f"可訓練（FINISHED + 比分）: {trainable}")
print(f"若修好大小寫後可訓練: {trainable_if_case_fixed}")

oldest = db.query(Match).order_by(Match.match_date.asc()).first()
newest = db.query(Match).order_by(Match.match_date.desc()).first()
if oldest and newest and oldest.match_date and newest.match_date:
    print(f"\n最早 match_date: {oldest.match_date}")
    print(f"最晚 match_date: {newest.match_date}")
else:
    print("\n最早／最晚 match_date: 無（當 0）")

b365 = db.query(Match).filter(Match.b365_home.isnot(None)).count()
odds = db.query(Match).filter(Match.odds_home.isnot(None)).count()
print(f"\n有 B365 主勝賠率: {b365}（佔總場 {b365 / total * 100:.1f}%）" if total else "\n有 B365 主勝賠率: 0")
print(f"有 odds_home: {odds}")

print("\n各聯賽:")
for league, count in (
    db.query(Match.league, func.count(Match.id)).group_by(Match.league).order_by(Match.league).all()
):
    print(f"  {league}: {count}")

has_season = False
try:
    db.execute(text("SELECT season FROM matches LIMIT 1"))
    has_season = True
except Exception:
    db.rollback()
print(f"\nmatches.season 欄: {'有' if has_season else '沒有（Phase 1 再加）'}")
if has_season:
    print("各 season:")
    for season, count in (
        db.query(Match.season, func.count(Match.id))
        .group_by(Match.season)
        .order_by(Match.season)
        .all()
    ):
        print(f"  {season}: {count}")

    h = d = a = 0
    for m in db.query(Match).filter(Match.status == "FINISHED").all():
        if m.home_score is None or m.away_score is None:
            continue
        if m.home_score > m.away_score:
            h += 1
        elif m.home_score < m.away_score:
            a += 1
        else:
            d += 1
    scored = h + d + a
    if scored:
        print(f"\nFINISHED H/D/A: {h}/{d}/{a} ({h/scored:.1%}/{d/scored:.1%}/{a/scored:.1%})")

db.close()
print("=" * 70)
