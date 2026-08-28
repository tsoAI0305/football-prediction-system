"""Fetch upcoming fixtures from API-Football."""
import sys
import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.match import Match

DATABASE_URL = "postgresql://football_user:football_pass@localhost:5432/football_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# API-Football 設定（從環境變數讀取，勿把 key 寫進 repo）
API_KEY = os.getenv("FOOTBALL_API_KEY") or os.getenv("football_api_key")
API_BASE = os.getenv("FOOTBALL_API_BASE_URL", "https://v3.football.api-sports.io")

# 要抓取的聯賽 ID（Premier League: 39, La Liga: 140, etc.）
LEAGUE_IDS = [39, 140, 61, 78, 135]  # 英超、西甲、法甲、德甲、意甲

def fetch_fixtures():
    """Fetch fixtures from API."""
    if not API_KEY:
        raise SystemExit(
            "缺少 FOOTBALL_API_KEY。請在 backend/.env 設定後再執行。"
        )
    db = SessionLocal()
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        for league_id in LEAGUE_IDS:
            print(f"📥 Fetching fixtures for league {league_id}...")
            
            url = f"{API_BASE}/fixtures"
            params = {
                'league': league_id,
                'season': 2025,  # 當前賽季
                'from': today,
                'to': end_date,
                'status': 'NS'  # Not Started
            }
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if data.get('response'):
                for fixture in data['response']:
                    fixture_data = fixture['fixture']
                    teams = fixture['teams']
                    league = fixture['league']
                    
                    # 檢查是否已存在
                    existing = db.query(Match).filter_by(
                        home_team=teams['home']['name'],
                        away_team=teams['away']['name'],
                        match_date=datetime.fromisoformat(fixture_data['date'].replace('Z', '+00:00'))
                    ).first()
                    
                    if not existing:
                        match = Match(
                            home_team=teams['home']['name'],
                            away_team=teams['away']['name'],
                            league=league['name'],
                            match_date=datetime.fromisoformat(fixture_data['date'].replace('Z', '+00:00')),
                            status='upcoming',
                            api_fixture_id=fixture_data['id']  # 儲存 API ID 供後續更新
                        )
                        db.add(match)
                        print(f"  ✅ {teams['home']['name']} vs {teams['away']['name']}")
        
        db.commit()
        print(f"\n🎉 Fixtures imported successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_fixtures()