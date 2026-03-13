"""Fetch complete 2024/25 season data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime
from app.database import SessionLocal
from app.models.match import Match
from app.config import settings

API_KEY = settings.football_api_key
BASE_URL = settings.football_api_base_url

LEAGUES = {
    39: 'Premier League',
    140: 'La Liga',
    78: 'Bundesliga',
    135: 'Serie A',
    61: 'Ligue 1',
}

def fetch_league_season(league_id, league_name, season=2024):
    """抓取指定聯賽的完整賽季."""
    db = SessionLocal()
    imported = 0
    
    try:
        headers = {'x-apisports-key': API_KEY}
        params = {
            'league': league_id,
            'season': season,
        }
        
        print(f"\n📡 {league_name} ({season}/{season+1})...")
        
        response = requests.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   ❌ 錯誤: {response.status_code}")
            return 0
        
        data = response.json()
        fixtures = data.get('response', [])
        print(f"   找到 {len(fixtures)} 場")
        
        for fixture_data in fixtures:
            fixture = fixture_data['fixture']
            teams = fixture_data['teams']
            goals = fixture_data.get('goals', {})
            
            # 檢查是否已存在
            existing = db.query(Match).filter(
                Match.api_fixture_id == fixture['id']
            ).first()
            
            if existing:
                continue
            
            # 建立新記錄
            match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
            
            status_map = {
                'FT': 'finished', 'AET': 'finished', 'PEN': 'finished',
                '1H': 'live', '2H': 'live', 'HT': 'live',
                'NS': 'scheduled', 'TBD': 'scheduled',
            }
            status = status_map.get(fixture['status']['short'], 'cancelled')
            
            new_match = Match(
                league=league_name,
                match_date=match_date,
                home_team=teams['home']['name'],
                away_team=teams['away']['name'],
                home_score=goals.get('home'),
                away_score=goals.get('away'),
                status=status,
                api_fixture_id=fixture['id'],
            )
            
            db.add(new_match)
            imported += 1
            
            if imported % 100 == 0:
                db.commit()
                print(f"   已匯入 {imported}...")
        
        db.commit()
        print(f"   ✅ 匯入 {imported} 場新比賽")
        
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()
    
    return imported

if __name__ == "__main__":
    print("🚀 抓取 2024/25 賽季完整資料")
    print("="*60)
    
    total = 0
    for league_id, league_name in LEAGUES.items():
        count = fetch_league_season(league_id, league_name, 2024)
        total += count
    
    print("\n" + "="*60)
    print(f"🎉 總共匯入 {total} 場新比賽")
    
    # 統計
    db = SessionLocal()
    total_matches = db.query(Match).count()
    latest = db.query(Match).order_by(Match.match_date.desc()).first()
    oldest = db.query(Match).order_by(Match.match_date.asc()).first()
    
    print(f"📊 資料庫總比賽數: {total_matches}")
    if latest:
        print(f"📅 最新: {latest.match_date.date()} - {latest.home_team} vs {latest.away_team}")
    if oldest:
        print(f"📅 最舊: {oldest.match_date.date()}")
    
    db.close()
