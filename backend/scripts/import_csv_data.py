"""Import historical data from Football-Data.co.uk CSV."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from app.database import SessionLocal
from app.models.match import Match

def import_csv_season(url, league_name):
    """從 CSV 匯入一個賽季的資料."""
    db = SessionLocal()
    imported = 0
    
    try:
        print(f"\n📥 下載 {league_name}...")
        df = pd.read_csv(url)
        print(f"   找到 {len(df)} 場比賽")
        
        for _, row in df.iterrows():
            # 解析日期
            try:
                match_date = pd.to_datetime(row['Date'], format='%d/%m/%Y')
            except:
                try:
                    match_date = pd.to_datetime(row['Date'], format='%d/%m/%y')
                except:
                    continue
            
            # 檢查是否已存在
            existing = db.query(Match).filter(
                Match.home_team == row['HomeTeam'],
                Match.away_team == row['AwayTeam'],
                Match.match_date == match_date
            ).first()
            
            if existing:
                continue
            
            # 建立新記錄
            new_match = Match(
                league=league_name,
                match_date=match_date,
                home_team=row['HomeTeam'],
                away_team=row['AwayTeam'],
                home_score=int(row['FTHG']) if pd.notna(row['FTHG']) else None,
                away_score=int(row['FTAG']) if pd.notna(row['FTAG']) else None,
                status='finished',
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

if __name__ == "__main__":
    print("🚀 匯入 Football-Data.co.uk CSV 資料")
    print("="*60)
    
    # 定義要匯入的賽季
    seasons = [
        ('https://www.football-data.co.uk/mmz4281/2223/E0.csv', 'Premier League'),
        ('https://www.football-data.co.uk/mmz4281/2223/SP1.csv', 'La Liga'),
        ('https://www.football-data.co.uk/mmz4281/2223/D1.csv', 'Bundesliga'),
        ('https://www.football-data.co.uk/mmz4281/2223/I1.csv', 'Serie A'),
        ('https://www.football-data.co.uk/mmz4281/2223/F1.csv', 'Ligue 1'),
    ]
    
    total = 0
    for url, name in seasons:
        count = import_csv_season(url, name)
        total += count
    
    print("\n" + "="*60)
    print(f"🎉 總共匯入 {total} 場比賽")
    
    # 統計
    db = SessionLocal()
    print(f"📊 資料庫總比賽數: {db.query(Match).count()}")
    db.close()
