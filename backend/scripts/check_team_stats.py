"""Check team stats."""
import json

with open('data/team_stats.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

# 檢查重要球隊
teams_to_check = [
    'Man City', 'Manchester City',
    'Liverpool', 'Arsenal', 'Chelsea',
    'Barcelona', 'Real Madrid',
    'Bayern Munich', 'Paris Saint Germain'
]

print("="*70)
print("⚽ 主要球隊最新狀態")
print("="*70)

found = []
for team in teams_to_check:
    if team in stats:
        if team not in found:  # 避免重複
            found.append(team)
            s = stats[team]
            print(f"\n{team}:")
            print(f"  近期狀態: {s.get('recent_form', 'N/A')}")
            print(f"  總場次: {s.get('total_matches', 0)}")
            print(f"  主場勝率: {s.get('home_win_rate', 0)*100:.1f}%")
            print(f"  客場勝率: {s.get('away_win_rate', 0)*100:.1f}%")
            print(f"  主場場均進球: {s.get('avg_goals_scored_home', 0)}")
            print(f"  客場場均進球: {s.get('avg_goals_scored_away', 0)}")

print("\n" + "="*70)
print(f"✅ 找到 {len(found)} 支球隊的統計資料")
print("="*70)
