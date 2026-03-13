"""Fetch 2025/26 season matches from API-Football."""
import os
import sys
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.match import Match
from app.config import settings  # ← 加這行

DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

API_KEY = settings.football_api_key  # ← 改這行
BASE_URL = settings.football_api_base_url  # ← 改這行

# 聯賽 ID
LEAGUES = {
    39: 'Premier League',
    140: 'La Liga',
    78: 'Bundesliga',
}

def fetch_season_matches(league_id, league_name):
    """抓取整個賽季的比賽."""
    db = SessionLocal()
    
    try:
        headers = {'x-apisports-key': API_KEY}
        params = {
            'league': league_id,
            'season': 2025,  # 2025/26 賽季
            'timezone': 'Asia/Taipei'
        }
        
        print(f"\n📡 Fetching {league_name} (2025/26)...")
        
        response = requests.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params=params,
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"  ❌ Error: {response.status_code}")
            return 0
        
        data = response.json()
        fixtures = data.get('response', [])
        
        imported = 0
        for fixture in fixtures:
            fixture_id = fixture['fixture']['id']
            status = fixture['fixture']['status']['short']
            
            # 檢查是否已存在
            existing = db.query(Match).filter_by(
                api_fixture_id=fixture_id
            ).first()
            
            if existing:
                continue
            
            # 解析日期
            match_date = datetime.fromisoformat(
                fixture['fixture']['date'].replace('Z', '+00:00')
            )
            
            # 判斷狀態
            if status in ['FT', 'AET', 'PEN']:
                match_status = 'finished'
                home_score = fixture['goals']['home']
                away_score = fixture['goals']['away']
            elif status in ['NS', 'TBD']:
                match_status = 'upcoming'
                home_score = None
                away_score = None
            else:
                match_status = 'live'
                home_score = fixture['goals']['home']
                away_score = fixture['goals']['away']
            
            # 建立記錄
            match = Match(
                home_team=fixture['teams']['home']['name'],
                away_team=fixture['teams']['away']['name'],
                league=league_name,
                match_date=match_date,
                status=match_status,
                home_score=home_score,
                away_score=away_score,
                api_fixture_id=fixture_id,
            )
            
            db.add(match)
            imported += 1
        
        db.commit()
        print(f"  ✅ Imported {imported} matches")
        return imported
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def main():
    """主函數."""
    if not API_KEY:
        print("❌ FOOTBALL_API_KEY not found")
        print("Please add it to .env file")
        return
    
    print("🚀 Fetching 2025/26 season from API-Football\n")
    
    total = 0
    for league_id, league_name in LEAGUES.items():
        total += fetch_season_matches(league_id, league_name)
    
    print(f"\n🎉 Total imported: {total} matches")
    
    # 統計
    db = SessionLocal()
    current_season = db.query(Match).filter(
        Match.match_date >= datetime(2025, 8, 1)
    ).count()
    db.close()
    
    print(f"📊 Total 2025/26 matches: {current_season}")

if __name__ == "__main__":
    main()