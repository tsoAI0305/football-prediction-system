"""Fetch matches by date range instead of season."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime, timedelta
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

def fetch_matches_by_date(league_id, league_name, from_date, to_date):
    """使用日期範圍抓取比賽."""
    db = SessionLocal()
    imported = 0
    
    try:
        headers = {'x-apisports-key': API_KEY}
        params = {
            'league': league_id,
            'from': from_date,
            'to': to_date,
        }
        
        print(f"\n📡 {league_name}: {from_date} ~ {to_date}")
        
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
        print(f"   找到 {len(fixtures)} 場比賽")
        
        for fixture_data in fixtures:
            fixture = fixture_data['fixture']
            teams = fixture_data['teams']
            goals = fixture_data.get('goals', {})
            
            # 檢查是否已存在
            existing = db.query(Match).filter(
                Match.api_fixture_id == fixture['id']
            ).first()
            
            if existing:
                # 更新比分
                if fixture['status']['short'] in ['FT', 'AET', 'PEN']:
                    existing.home_score = goals.get('home')
                    existing.away_score = goals.get('away')
                    existing.status = 'finished'
                continue
            
            # 建立新記錄
            match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
            
            status_map = {
                'FT': 'finished', 'AET': 'finished', 'PEN': 'finished',
                '1H': 'live', '2H': 'live', 'HT': 'live', 'LIVE': 'live',
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
            
            if imported % 50 == 0:
                db.commit()
        
        db.commit()
        print(f"   ✅ 匯入 {imported} 場新比賽")
        
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()
    
    return imported

def fetch_season_data():
    """抓取整個賽季的資料（分批抓取）."""
    # 2025/26 賽季：2025-08-15 ~ 2026-05-24
    # 分成多個時間段，避免一次查詢太多
    
    date_ranges = []
    
    # 從賽季開始到現在，每 30 天一批
    start_date = datetime(2025, 8, 15)
    end_date = datetime.now()
    
    current = start_date
    while current < end_date:
        next_date = current + timedelta(days=30)
        if next_date > end_date:
            next_date = end_date
        
        date_ranges.append((
            current.strftime('%Y-%m-%d'),
            next_date.strftime('%Y-%m-%d')
        ))
        current = next_date
    
    # 加上未來 30 天
    future_end = datetime.now() + timedelta(days=30)
    date_ranges.append((
        datetime.now().strftime('%Y-%m-%d'),
        future_end.strftime('%Y-%m-%d')
    ))
    
    print("🚀 抓取 2025/26 賽季資料")
    print("="*60)
    print(f"時間範圍: 2025-08-15 ~ {future_end.strftime('%Y-%m-%d')}")
    print(f"分成 {len(date_ranges)} 批查詢")
    print("="*60)
    
    total = 0
    for from_date, to_date in date_ranges:
        print(f"\n📅 查詢期間: {from_date} ~ {to_date}")
        
        for league_id, league_name in LEAGUES.items():
            count = fetch_matches_by_date(league_id, league_name, from_date, to_date)
            total += count
    
    print("\n" + "="*60)
    print(f"🎉 總共匯入 {total} 場比賽")
    
    # 統計
    db = SessionLocal()
    total_matches = db.query(Match).count()
    latest = db.query(Match).order_by(Match.match_date.desc()).first()
    print(f"📊 資料庫總比賽數: {total_matches}")
    if latest:
        print(f"📅 最新比賽: {latest.match_date.date()} - {latest.home_team} vs {latest.away_team}")
    db.close()

if __name__ == "__main__":
    fetch_season_data()