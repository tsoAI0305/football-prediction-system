"""Fix team names in fixtures."""
import json

with open('data/real_fixtures.json', 'r', encoding='utf-8') as f:
    fixtures = json.load(f)

# 修正球隊名稱
fixes = {
    'Man City': 'Manchester City',
    'Man United': 'Manchester United',
    'Stade Brestois 29': 'Brest',
    'Paris Saint Germain': 'Paris SG',
    'Ath Madrid': 'Atletico Madrid',
    'Ath Bilbao': 'Athletic Bilbao',
    'AS Roma': 'Roma',
    'AC Milan': 'Milan',
}

count = 0
for f in fixtures:
    if f['home_team'] in fixes:
        print(f"修正: {f['home_team']} → {fixes[f['home_team']]}")
        f['home_team'] = fixes[f['home_team']]
        count += 1
    if f['away_team'] in fixes:
        print(f"修正: {f['away_team']} → {fixes[f['away_team']]}")
        f['away_team'] = fixes[f['away_team']]
        count += 1

# 儲存
with open('data/real_fixtures.json', 'w', encoding='utf-8') as f:
    json.dump(fixtures, f, ensure_ascii=False, indent=2)

print(f"\n✅ 修正 {count} 個球隊名稱")
