"""Check database status."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.match import Match
from datetime import datetime, timedelta
from sqlalchemy import func

db = SessionLocal()

print("="*70)
print("📊 資料庫狀態")
print("="*70)

# 最新比賽
latest = db.query(Match).order_by(Match.match_date.desc()).first()
if latest:
    print(f"\n📅 最新比賽: {latest.match_date.date()}")
    print(f"   聯賽: {latest.league}")
    print(f"   比賽: {latest.home_team} {latest.home_score}-{latest.away_score} {latest.away_team}")
    
    days_ago = (datetime.now() - latest.match_date).days
    print(f"   距今: {days_ago} 天")

# 最舊比賽
oldest = db.query(Match).order_by(Match.match_date.asc()).first()
if oldest:
    print(f"\n📅 最舊比賽: {oldest.match_date.date()}")

# 總比賽數
total = db.query(Match).count()
print(f"\n📊 總比賽數: {total}")

# 各聯賽比賽數
league_counts = db.query(
    Match.league, 
    func.count(Match.id)
).group_by(Match.league).all()

print("\n📋 各聯賽比賽數:")
for league, count in sorted(league_counts):
    print(f"   {league}: {count}")

# 最近7天的比賽
week_ago = datetime.now() - timedelta(days=7)
recent_count = db.query(Match).filter(Match.match_date >= week_ago).count()
print(f"\n🔥 最近7天比賽: {recent_count}")

db.close()

print("="*70)
