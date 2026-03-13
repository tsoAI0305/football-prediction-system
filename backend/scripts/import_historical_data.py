"""Import historical match data from football-data.co.uk CSV files."""
import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.match import Match

DATABASE_URL = "postgresql://football_user:football_pass@db:5432/football_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# 聯賽映射
LEAGUE_MAP = {
    'E0': 'Premier League',
    'E1': 'Championship',
    'SP1': 'La Liga',
    'SP2': 'La Liga 2',
    'D1': 'Bundesliga',
    'D2': 'Bundesliga 2',
    'I1': 'Serie A',
    'I2': 'Serie B',
    'F1': 'Ligue 1',
    'F2': 'Ligue 2',
}

def parse_date(date_str):
    """Parse date from DD/MM/YY or DD/MM/YYYY format."""
    try:
        return datetime.strptime(str(date_str), '%d/%m/%Y')
    except:
        try:
            return datetime.strptime(str(date_str), '%d/%m/%y')
        except:
            print(f"⚠️  Could not parse date: {date_str}")
            return None

def import_csv_file(file_path, league_code):
    """Import single CSV file."""
    db = SessionLocal()
    
    try:
        print(f"\n📥 Reading {file_path.name}...")
        df = pd.read_csv(file_path, encoding='latin1')
        
        league_name = LEAGUE_MAP.get(league_code, league_code)
        imported = 0
        skipped = 0
        
        for _, row in df.iterrows():
            # 檢查必要欄位
            if pd.isna(row.get('HomeTeam')) or pd.isna(row.get('AwayTeam')):
                continue
            
            # 解析日期
            match_date = parse_date(row['Date'])
            if not match_date:
                continue
            
            # 檢查是否已存在
            existing = db.query(Match).filter_by(
                home_team=str(row['HomeTeam']),
                away_team=str(row['AwayTeam']),
                match_date=match_date
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # 建立比賽記錄
            match = Match(
                home_team=str(row['HomeTeam']),
                away_team=str(row['AwayTeam']),
                league=league_name,
                match_date=match_date,
                status='finished',
                home_score=int(row['FTHG']) if not pd.isna(row.get('FTHG')) else None,
                away_score=int(row['FTAG']) if not pd.isna(row.get('FTAG')) else None,
                # 統計數據
                home_shots=int(row['HS']) if not pd.isna(row.get('HS')) else None,
                away_shots=int(row['AS']) if not pd.isna(row.get('AS')) else None,
                home_shots_on_target=int(row['HST']) if not pd.isna(row.get('HST')) else None,
                away_shots_on_target=int(row['AST']) if not pd.isna(row.get('AST')) else None,
                home_corners=int(row['HC']) if not pd.isna(row.get('HC')) else None,
                away_corners=int(row['AC']) if not pd.isna(row.get('AC')) else None,
                home_fouls=int(row['HF']) if not pd.isna(row.get('HF')) else None,
                away_fouls=int(row['AF']) if not pd.isna(row.get('AF')) else None,
                home_yellow=int(row['HY']) if not pd.isna(row.get('HY')) else None,
                away_yellow=int(row['AY']) if not pd.isna(row.get('AY')) else None,
                home_red=int(row['HR']) if not pd.isna(row.get('HR')) else None,
                away_red=int(row['AR']) if not pd.isna(row.get('AR')) else None,
                # 賠率數據
                b365_home=float(row['B365H']) if not pd.isna(row.get('B365H')) else None,
                b365_draw=float(row['B365D']) if not pd.isna(row.get('B365D')) else None,
                b365_away=float(row['B365A']) if not pd.isna(row.get('B365A')) else None,
            )
            
            db.add(match)
            imported += 1
            
            if imported % 50 == 0:
                db.commit()
                print(f"  ⏳ Imported {imported} matches...")
        
        db.commit()
        print(f"  ✅ {league_name}: Imported {imported} matches, Skipped {skipped} duplicates")
        return imported
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0
    finally:
        db.close()

def import_all_data():
    """Import all CSV files from data directory."""
    data_dir = Path(__file__).parent.parent / 'data'
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("Please create 'backend/data/' and download CSV files")
        return
    
    csv_files = list(data_dir.glob('*.csv'))
    
    # 排除 .gitkeep
    csv_files = [f for f in csv_files if f.name != '.gitkeep']
    
    if not csv_files:
        print("❌ No CSV files found in data directory")
        print(f"Please download CSV from https://www.football-data.co.uk/")
        return
    
    print(f"🚀 Found {len(csv_files)} CSV files\n")
    
    total_imported = 0
    for csv_file in csv_files:
        # 從檔名推測聯賽代碼
        league_code = csv_file.stem.upper()
        
        # 檢查是否為已知聯賽
        matched = False
        for code in LEAGUE_MAP.keys():
            if code in league_code:
                total_imported += import_csv_file(csv_file, code)
                matched = True
                break
        
        if not matched:
            print(f"⚠️  Skipping {csv_file.name} (unknown league code)")
    
    print(f"\n🎉 Import completed! Total: {total_imported} matches")
    
    # 顯示統計
    db = SessionLocal()
    total_matches = db.query(Match).count()
    finished_matches = db.query(Match).filter_by(status='finished').count()
    db.close()
    
    print(f"\n📊 Database Statistics:")
    print(f"  Total matches: {total_matches}")
    print(f"  Finished matches: {finished_matches}")

if __name__ == "__main__":
    print("📚 Football Historical Data Importer\n")
    import_all_data()