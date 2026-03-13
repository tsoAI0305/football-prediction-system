import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.match import Match
from app.config import settings

API_KEY = settings.football_api_key
BASE_URL = settings.football_api_base_url
headers = {'x-apisports-key': API_KEY}

# 最近 7 天
today = datetime.now()
from_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
to_date = today.strftime('%Y-%m-%d')

print(f"測試抓取: {from_date} ~ {to_date}")

for league_id, league_name in [(39, 'Premier League'), (140, 'La Liga')]:
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={'league': league_id, 'from': from_date, 'to': to_date},
        timeout=10
    )
    
    if response.status_code == 200:
        matches = response.json().get('response', [])
        print(f"\n{league_name}: {len(matches)} 場")
        
        db = SessionLocal()
        imported = 0
        for m in matches:
            fixture = m['fixture']
            teams = m['teams']
            goals = m.get('goals', {})
            
            # 檢查是否存在
            if db.query(Match).filter(Match.api_fixture_id == fixture['id']).first():
                continue
            
            # 新增
            match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
            new_match = Match(
                league=league_name,
                match_date=match_date,
                home_team=teams['home']['name'],
                away_team=teams['away']['name'],
                home_score=goals.get('home'),
                away_score=goals.get('away'),
                status='finished' if fixture['status']['short'] == 'FT' else 'scheduled',
                api_fixture_id=fixture['id'],
            )
            db.add(new_match)
            imported += 1
        
        db.commit()
        db.close()
        print(f"  匯入 {imported} 場新比賽")

print("\n✅ 完成")
