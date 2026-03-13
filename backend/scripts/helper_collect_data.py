"""Helper to collect recent match data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from app.database import SessionLocal
from app.models.match import Match

print("="*70)
print("📋 資料收集指南")
print("="*70)

# 讀取下週賽程，找出需要更新的球隊
fixtures_file = 'data/real_fixtures.json'

if os.path.exists(fixtures_file):
    with open(fixtures_file, 'r', encoding='utf-8') as f:
        fixtures = json.load(f)
    
    # 收集所有球隊
    teams_needed = set()
    for f in fixtures:
        teams_needed.add(f['home_team'])
        teams_needed.add(f['away_team'])
    
    print(f"\n🎯 下週有比賽的球隊 (共 {len(teams_needed)} 支):\n")
    
    # 按聯賽分組
    by_league = {}
    for f in fixtures:
        league = f['league']
        if league not in by_league:
            by_league[league] = set()
        by_league[league].add(f['home_team'])
        by_league[league].add(f['away_team'])
    
    for league in sorted(by_league.keys()):
        print(f"\n{league}:")
        for team in sorted(by_league[league]):
            print(f"   - {team}")
    
    print("\n" + "="*70)
    print("📝 任務: 為這些球隊收集最近 3-5 場比賽")
    print("="*70)
    
else:
    print("\n⚠️ 找不到賽程檔案！請先執行:")
    print("   docker compose exec api python scripts/load_real_fixtures.py")

print("\n" + "="*70)
print("🌐 資料來源:")
print("="*70)
print("   FlashScore: https://www.flashscore.com/")
print("   BBC Sport:  https://www.bbc.com/sport/football/scores-fixtures")
print("   ESPN:       https://www.espn.com/soccer/")

print("\n" + "="*70)
print("📋 資料格式範例:")
print("="*70)
print("""
    {
        'date': '2026-03-08',
        'league': 'Premier League',
        'home_team': 'Tottenham',
        'away_team': 'Crystal Palace',
        'home_score': 1,
        'away_score': 1,
    },
""")

print("\n💡 球隊名稱必須完全一致！")

# 顯示資料庫中的球隊名稱
if os.path.exists('data/team_stats.json'):
    with open('data/team_stats.json', 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    print("\n" + "="*70)
    print("📊 資料庫中的正確球隊名稱:")
    print("="*70)
    
    db = SessionLocal()
    
    for league in ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1']:
        teams = set()
        matches = db.query(Match).filter(Match.league == league).limit(100).all()
        for m in matches:
            if m.home_team in stats:
                teams.add(m.home_team)
            if m.away_team in stats:
                teams.add(m.away_team)
        
        if teams:
            print(f"\n{league}:")
            for team in sorted(teams):
                print(f"   {team}")
    
    db.close()

print("\n" + "="*70)
print("✅ 下一步:")
print("="*70)
print("1. 訪問 FlashScore 查詢上述球隊的最近比賽")
print("2. 編輯 scripts/import_recent_results.py")
print("3. 填入 RECENT_RESULTS_2026 = [ ... ]")
print("4. 執行匯入")
print("="*70)
