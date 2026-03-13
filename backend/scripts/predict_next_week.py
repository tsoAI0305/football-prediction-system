"""Predict all matches in next week."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from scripts.predict_match import predict_match

# 手動輸入未來賽程（使用正確的球隊名稱）
NEXT_WEEK_FIXTURES = [
    # Premier League
    {
        'date': '2026-03-14',
        'league': 'Premier League',
        'home_team': 'Manchester City',
        'away_team': 'Liverpool',
    },
    {
        'date': '2026-03-14',
        'league': 'Premier League',
        'home_team': 'Arsenal',
        'away_team': 'Chelsea',
    },
    {
        'date': '2026-03-14',
        'league': 'Premier League',
        'home_team': 'Manchester United',
        'away_team': 'Tottenham',
    },
    {
        'date': '2026-03-15',
        'league': 'Premier League',
        'home_team': 'Newcastle',
        'away_team': 'Aston Villa',
    },
    
    # La Liga
    {
        'date': '2026-03-15',
        'league': 'La Liga',
        'home_team': 'Barcelona',
        'away_team': 'Real Madrid',
    },
    {
        'date': '2026-03-15',
        'league': 'La Liga',
        'home_team': 'Atletico Madrid',
        'away_team': 'Sevilla',
    },
    {
        'date': '2026-03-15',
        'league': 'La Liga',
        'home_team': 'Valencia',
        'away_team': 'Villarreal',
    },
    
    # Bundesliga
    {
        'date': '2026-03-15',
        'league': 'Bundesliga',
        'home_team': 'Bayern Munich',
        'away_team': 'Dortmund',
    },
    {
        'date': '2026-03-15',
        'league': 'Bundesliga',
        'home_team': 'RB Leipzig',
        'away_team': 'Leverkusen',
    },
    
    # Serie A
    {
        'date': '2026-03-15',
        'league': 'Serie A',
        'home_team': 'Inter',
        'away_team': 'AC Milan',
    },
    {
        'date': '2026-03-15',
        'league': 'Serie A',
        'home_team': 'Juventus',
        'away_team': 'Napoli',
    },
    {
        'date': '2026-03-15',
        'league': 'Serie A',
        'home_team': 'Roma',
        'away_team': 'Lazio',
    },
    
    # Ligue 1
    {
        'date': '2026-03-16',
        'league': 'Ligue 1',
        'home_team': 'Paris Saint Germain',  # 使用完整名稱
        'away_team': 'Marseille',
    },
    {
        'date': '2026-03-16',
        'league': 'Ligue 1',
        'home_team': 'Lyon',
        'away_team': 'Monaco',
    },
    {
        'date': '2026-03-16',
        'league': 'Ligue 1',
        'home_team': 'Lille',
        'away_team': 'Lens',
    },
]

def predict_next_week():
    """預測下週所有比賽."""
    
    print("🚀 預測未來一週賽事")
    print("="*70)
    print(f"總共 {len(NEXT_WEEK_FIXTURES)} 場比賽\n")
    
    predictions = []
    success = 0
    failed = 0
    failed_matches = []
    
    for fixture in NEXT_WEEK_FIXTURES:
        print(f"\n📅 {fixture['date']} | {fixture['league']}")
        print(f"⚽ {fixture['home_team']} vs {fixture['away_team']}")
        print("-"*70)
        
        result = predict_match(fixture['home_team'], fixture['away_team'])
        
        if 'error' in result:
            print(f"   ❌ {result['error']}")
            failed += 1
            failed_matches.append(f"{fixture['home_team']} vs {fixture['away_team']}")
        else:
            # 預測結果
            pred_map = {
                'home_win': f"✅ {fixture['home_team']} 獲勝",
                'away_win': f"✅ {fixture['away_team']} 獲勝",
                'draw': '🤝 平局'
            }
            print(f"   🎯 預測: {pred_map[result['prediction']]} (信心度: {result['confidence']}%)")
            print(f"   📊 機率: 主 {result['probabilities']['home_win']}% | "
                  f"和 {result['probabilities']['draw']}% | "
                  f"客 {result['probabilities']['away_win']}%")
            print(f"   ⚽ 預測比分: {result['expected_score']}")
            print(f"   📈 {fixture['home_team']}: {result['analysis']['home_form']} "
                  f"(主場勝率 {result['analysis']['home_win_rate']}%)")
            print(f"   📈 {fixture['away_team']}: {result['analysis']['away_form']} "
                  f"(客場勝率 {result['analysis']['away_win_rate']}%)")
            
            predictions.append({
                'date': fixture['date'],
                'league': fixture['league'],
                'home_team': fixture['home_team'],
                'away_team': fixture['away_team'],
                'prediction': result,
            })
            success += 1
    
    # 儲存結果
    os.makedirs('data', exist_ok=True)
    with open('data/predictions.json', 'w', encoding='utf-8') as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print(f"📊 預測統計")
    print("="*70)
    print(f"✅ 成功預測: {success} 場")
    print(f"❌ 失敗: {failed} 場")
    
    if failed_matches:
        print(f"\n⚠️ 無法預測的比賽（找不到球隊資料）:")
        for match in failed_matches:
            print(f"   - {match}")
    
    print(f"\n📁 預測結果已儲存到 data/predictions.json")
    print("="*70)
    
    # 按聯賽統計
    by_league = {}
    for p in predictions:
        league = p['league']
        if league not in by_league:
            by_league[league] = {'home_win': 0, 'draw': 0, 'away_win': 0}
        by_league[league][p['prediction']['prediction']] += 1
    
    print("\n📊 各聯賽預測分布:")
    for league, stats in sorted(by_league.items()):
        total = sum(stats.values())
        print(f"\n{league} ({total} 場):")
        print(f"   主勝: {stats['home_win']} | 和局: {stats['draw']} | 客勝: {stats['away_win']}")
    
    return predictions

if __name__ == "__main__":
    predict_next_week()
