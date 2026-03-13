"""Import data from Football-Data Excel/CSV."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from app.database import SessionLocal
from app.models.match import Match

# 聯賽映射
LEAGUE_MAPPING = {
    'E0': 'Premier League',
    'E1': 'Championship',
    'SP1': 'La Liga',
    'D1': 'Bundesliga',
    'I1': 'Serie A',
    'F1': 'Ligue 1',
}

# 球隊名稱映射（CSV 中的簡稱 → 資料庫完整名稱）
TEAM_MAPPING = {
    'Man United': 'Manchester United',
    'Man City': 'Manchester City',
    "Nott'm Forest": 'Nottm Forest',
    'Nottm Forest': 'Nottm Forest',
    'Newcastle': 'Newcastle',
    'West Ham': 'West Ham',
    'Ath Madrid': 'Atletico Madrid',
    'Ath Bilbao': 'Athletic Bilbao',
}

def normalize_team_name(name):
    """標準化球隊名稱."""
    name = str(name).strip()
    return TEAM_MAPPING.get(name, name)

def import_csv_file(file_path, league_code):
    """匯入單個 CSV 檔案."""
    
    league_name = LEAGUE_MAPPING.get(league_code)
    if not league_name:
        print(f"❌ 未知聯賽代碼: {league_code}")
        return 0
    
    if not os.path.exists(file_path):
        print(f"⚠️  找不到檔案: {file_path}")
        return 0
    
    db = SessionLocal()
    
    print(f"\n📥 匯入 {league_name} ({os.path.basename(file_path)})...")
    
    try:
        # 讀取 CSV
        df = pd.read_csv(file_path, encoding='utf-8')
        
        print(f"   總行數: {len(df)}")
        
        imported = 0
        updated = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            # 檢查必要欄位
            if pd.isna(row.get('Date')):
                continue
            if pd.isna(row.get('HomeTeam')) or pd.isna(row.get('AwayTeam')):
                continue
            
            # 只處理已完成的比賽 (有比分)
            if pd.isna(row.get('FTHG')) or pd.isna(row.get('FTAG')):
                continue
            
            # 解析日期
            try:
                date_str = str(row['Date']).strip()
                # 嘗試多種日期格式
                if '/' in date_str:
                    match_date = pd.to_datetime(date_str, format='%Y/%m/%d')
                elif '-' in date_str:
                    match_date = pd.to_datetime(date_str, format='%Y-%m-%d')
                else:
                    match_date = pd.to_datetime(date_str)
            except Exception as e:
                print(f"   ⚠️  第 {idx+2} 行日期解析失敗: {row.get('Date')}")
                continue
            
            # 標準化球隊名稱
            home_team = normalize_team_name(row['HomeTeam'])
            away_team = normalize_team_name(row['AwayTeam'])
            
            # 檢查是否已存在
            existing = db.query(Match).filter(
                Match.home_team == home_team,
                Match.away_team == away_team,
                Match.match_date >= match_date,
                Match.match_date < match_date + pd.Timedelta(days=1)
            ).first()
            
            if existing:
                # 更新比分
                try:
                    new_home_score = int(float(row['FTHG']))
                    new_away_score = int(float(row['FTAG']))
                    
                    if existing.home_score != new_home_score or existing.away_score != new_away_score:
                        existing.home_score = new_home_score
                        existing.away_score = new_away_score
                        existing.status = 'finished'
                        updated += 1
                    else:
                        skipped += 1
                except:
                    skipped += 1
            else:
                # 新增
                try:
                    new_match = Match(
                        league=league_name,
                        match_date=match_date,
                        home_team=home_team,
                        away_team=away_team,
                        home_score=int(float(row['FTHG'])),
                        away_score=int(float(row['FTAG'])),
                        status='finished',
                    )
                    db.add(new_match)
                    imported += 1
                    
                    # 每 50 筆提交一次
                    if imported % 50 == 0:
                        db.commit()
                except Exception as e:
                    print(f"   ⚠️  第 {idx+2} 行新增失敗: {e}")
        
        db.commit()
        print(f"   ✅ 新增: {imported} | 更新: {updated} | 跳過: {skipped}")
        
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0
    finally:
        db.close()
    
    return imported + updated

def import_all_leagues():
    """匯入所有聯賽."""
    
    print("🚀 匯入 Football-Data CSV 資料")
    print("="*70)
    
    # CSV 檔案路徑
    csv_files = {
        'E0': 'data/E0_2526.csv',
        'SP1': 'data/SP1_2526.csv',
        'D1': 'data/D1_2526.csv',
        'I1': 'data/I1_2526.csv',
        'F1': 'data/F1_2526.csv',
    }
    
    total = 0
    found_files = 0
    
    for code, path in csv_files.items():
        if os.path.exists(path):
            found_files += 1
            count = import_csv_file(path, code)
            total += count
        else:
            print(f"\n⚠️  找不到: {path}")
    
    print("\n" + "="*70)
    print(f"📊 匯入統計")
    print("="*70)
    print(f"✅ 找到檔案: {found_files}/5")
    print(f"✅ 總共處理: {total} 場比賽")
    
    if total > 0:
        # 檢查最新資料
        db = SessionLocal()
        
        latest = db.query(Match).order_by(Match.match_date.desc()).first()
        oldest = db.query(Match).order_by(Match.match_date.asc()).first()
        total_matches = db.query(Match).count()
        
        if latest:
            print(f"\n📅 最新比賽: {latest.match_date.date()}")
            print(f"   {latest.league}: {latest.home_team} {latest.home_score}-{latest.away_score} {latest.away_team}")
        if oldest:
            print(f"📅 最舊比賽: {oldest.match_date.date()}")
        
        print(f"📊 資料庫總比賽數: {total_matches}")
        
        db.close()
        
        print("\n" + "="*70)
        print("💡 下一步: 重新計算球隊統計")
        print("   執行: docker compose exec api python scripts/calculate_team_stats.py")
    else:
        print("\n⚠️  請檢查:")
        print("   1. CSV 檔案是否存在於 data/ 資料夾")
        print("   2. 檔案名稱是否正確 (E0_2526.csv, SP1_2526.csv, 等)")
    
    print("="*70)

if __name__ == "__main__":
    import_all_leagues()
