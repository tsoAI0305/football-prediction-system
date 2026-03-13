import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.match import Match
from datetime import datetime, timezone
from sqlalchemy import func

db = SessionLocal()
total = db.query(Match).count()
print(f'總比賽數: {total}')

if total > 0:
    oldest = db.query(Match).order_by(Match.match_date.asc()).first()
    newest = db.query(Match).order_by(Match.match_date.desc()).first()
    print(f'最舊: {oldest.match_date.date()}')
    print(f'最新: {newest.match_date.date()}')
    print(f'對陣: {newest.home_team} vs {newest.away_team}')
    
    today = datetime.now(timezone.utc).date()
    days_old = (today - newest.match_date.date()).days
    print(f'距今: {days_old} 天')
    
    if days_old > 7:
        print('⚠️ 需要更新資料')
    
    leagues = db.query(Match.league, func.count(Match.id)).group_by(Match.league).all()
    print(f'\n聯賽:')
    for league, count in leagues:
        print(f'  {league}: {count}')

db.close()
