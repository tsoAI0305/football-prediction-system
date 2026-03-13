"""Real upcoming fixtures from FlashScore (2026-03-14 to 2026-03-17)."""
import json
import os

# 根據 FlashScore 截圖的真實賽程
REAL_FIXTURES = [
    # ========== Premier League - Round 30 ==========
    {
        'date': '2026-03-14',
        'time': '23:00',
        'league': 'Premier League',
        'home_team': 'Burnley',
        'away_team': 'Bournemouth',
    },
    {
        'date': '2026-03-14',
        'time': '23:00',
        'league': 'Premier League',
        'home_team': 'Sunderland',
        'away_team': 'Brighton',
    },
    {
        'date': '2026-03-15',
        'time': '01:30',
        'league': 'Premier League',
        'home_team': 'Arsenal',
        'away_team': 'Everton',
    },
    {
        'date': '2026-03-15',
        'time': '01:30',
        'league': 'Premier League',
        'home_team': 'Chelsea',
        'away_team': 'Newcastle',
    },
    {
        'date': '2026-03-15',
        'time': '04:00',
        'league': 'Premier League',
        'home_team': 'West Ham',
        'away_team': 'Man City',
    },
    {
        'date': '2026-03-15',
        'time': '22:00',
        'league': 'Premier League',
        'home_team': 'Crystal Palace',
        'away_team': 'Leeds',
    },
    {
        'date': '2026-03-15',
        'time': '22:00',
        'league': 'Premier League',
        'home_team': 'Man United',
        'away_team': 'Aston Villa',
    },
    {
        'date': '2026-03-15',
        'time': '22:00',
        'league': 'Premier League',
        'home_team': 'Nottm Forest',
        'away_team': 'Fulham',
    },
    {
        'date': '2026-03-16',
        'time': '00:30',
        'league': 'Premier League',
        'home_team': 'Liverpool',
        'away_team': 'Tottenham',
    },
    {
        'date': '2026-03-17',
        'time': '04:00',
        'league': 'Premier League',
        'home_team': 'Brentford',
        'away_team': 'Wolves',
    },
    
    # ========== La Liga - Round 28 ==========
    {
        'date': '2026-03-14',
        'time': '04:00',
        'league': 'La Liga',
        'home_team': 'Alaves',
        'away_team': 'Villarreal',
    },
    {
        'date': '2026-03-14',
        'time': '21:00',
        'league': 'La Liga',
        'home_team': 'Girona',
        'away_team': 'Ath Bilbao',
    },
    {
        'date': '2026-03-14',
        'time': '23:15',
        'league': 'La Liga',
        'home_team': 'Ath Madrid',
        'away_team': 'Getafe',
    },
    {
        'date': '2026-03-15',
        'time': '01:30',
        'league': 'La Liga',
        'home_team': 'Oviedo',
        'away_team': 'Valencia',
    },
    {
        'date': '2026-03-15',
        'time': '04:00',
        'league': 'La Liga',
        'home_team': 'Real Madrid',
        'away_team': 'Elche',
    },
    {
        'date': '2026-03-15',
        'time': '21:00',
        'league': 'La Liga',
        'home_team': 'Mallorca',
        'away_team': 'Espanol',
    },
    {
        'date': '2026-03-15',
        'time': '23:15',
        'league': 'La Liga',
        'home_team': 'Barcelona',
        'away_team': 'Sevilla',
    },
    {
        'date': '2026-03-16',
        'time': '01:30',
        'league': 'La Liga',
        'home_team': 'Betis',
        'away_team': 'Celta',
    },
    {
        'date': '2026-03-16',
        'time': '04:00',
        'league': 'La Liga',
        'home_team': 'Sociedad',
        'away_team': 'Osasuna',
    },
    {
        'date': '2026-03-17',
        'time': '04:00',
        'league': 'La Liga',
        'home_team': 'Vallecano',
        'away_team': 'Levante',
    },
    
    # ========== Bundesliga - Round 26 ==========
    {
        'date': '2026-03-14',
        'time': '03:30',
        'league': 'Bundesliga',
        'home_team': 'M\'gladbach',
        'away_team': 'St Pauli',
    },
    {
        'date': '2026-03-14',
        'time': '22:30',
        'league': 'Bundesliga',
        'home_team': 'Leverkusen',
        'away_team': 'Bayern Munich',
    },
    {
        'date': '2026-03-14',
        'time': '22:30',
        'league': 'Bundesliga',
        'home_team': 'Dortmund',
        'away_team': 'Augsburg',
    },
    {
        'date': '2026-03-14',
        'time': '22:30',
        'league': 'Bundesliga',
        'home_team': 'Ein Frankfurt',
        'away_team': 'Heidenheim',
    },
    {
        'date': '2026-03-14',
        'time': '22:30',
        'league': 'Bundesliga',
        'home_team': 'Hoffenheim',
        'away_team': 'Wolfsburg',
    },
    {
        'date': '2026-03-15',
        'time': '01:30',
        'league': 'Bundesliga',
        'home_team': 'Hamburg',
        'away_team': 'FC Koln',
    },
    {
        'date': '2026-03-15',
        'time': '22:30',
        'league': 'Bundesliga',
        'home_team': 'Werder Bremen',
        'away_team': 'Mainz',
    },
    {
        'date': '2026-03-16',
        'time': '00:30',
        'league': 'Bundesliga',
        'home_team': 'Freiburg',
        'away_team': 'Union Berlin',
    },
    {
        'date': '2026-03-16',
        'time': '02:30',
        'league': 'Bundesliga',
        'home_team': 'Stuttgart',
        'away_team': 'RB Leipzig',
    },
    
    # ========== Serie A - Round 29 ==========
    {
        'date': '2026-03-14',
        'time': '03:45',
        'league': 'Serie A',
        'home_team': 'Torino',
        'away_team': 'Parma',
    },
    {
        'date': '2026-03-14',
        'time': '22:00',
        'league': 'Serie A',
        'home_team': 'Inter',
        'away_team': 'Atalanta',
    },
    {
        'date': '2026-03-15',
        'time': '01:00',
        'league': 'Serie A',
        'home_team': 'Napoli',
        'away_team': 'Lecce',
    },
    {
        'date': '2026-03-15',
        'time': '03:45',
        'league': 'Serie A',
        'home_team': 'Udinese',
        'away_team': 'Juventus',
    },
    {
        'date': '2026-03-15',
        'time': '19:30',
        'league': 'Serie A',
        'home_team': 'Verona',
        'away_team': 'Genoa',
    },
    {
        'date': '2026-03-15',
        'time': '22:00',
        'league': 'Serie A',
        'home_team': 'Pisa',
        'away_team': 'Cagliari',
    },
    {
        'date': '2026-03-15',
        'time': '22:00',
        'league': 'Serie A',
        'home_team': 'Sassuolo',
        'away_team': 'Bologna',
    },
    {
        'date': '2026-03-16',
        'time': '01:00',
        'league': 'Serie A',
        'home_team': 'Como',
        'away_team': 'AS Roma',
    },
    {
        'date': '2026-03-16',
        'time': '03:45',
        'league': 'Serie A',
        'home_team': 'Lazio',
        'away_team': 'AC Milan',
    },
    {
        'date': '2026-03-17',
        'time': '03:45',
        'league': 'Serie A',
        'home_team': 'Cremonese',
        'away_team': 'Fiorentina',
    },
    
    # ========== Ligue 1 - Round 26 ==========
    {
        'date': '2026-03-14',
        'time': '03:45',
        'league': 'Ligue 1',
        'home_team': 'Marseille',
        'away_team': 'Auxerre',
    },
    {
        'date': '2026-03-15',
        'time': '00:00',
        'league': 'Ligue 1',
        'home_team': 'Lorient',
        'away_team': 'Lens',
    },
    {
        'date': '2026-03-15',
        'time': '02:00',
        'league': 'Ligue 1',
        'home_team': 'Angers',
        'away_team': 'Nice',
    },
    {
        'date': '2026-03-15',
        'time': '04:05',
        'league': 'Ligue 1',
        'home_team': 'Monaco',
        'away_team': 'Stade Brestois 29',
    },
    {
        'date': '2026-03-15',
        'time': '22:00',
        'league': 'Ligue 1',
        'home_team': 'Strasbourg',
        'away_team': 'Paris Saint Germain',
    },
    {
        'date': '2026-03-16',
        'time': '00:15',
        'league': 'Ligue 1',
        'home_team': 'Le Havre',
        'away_team': 'Lyon',
    },
    {
        'date': '2026-03-16',
        'time': '00:15',
        'league': 'Ligue 1',
        'home_team': 'Metz',
        'away_team': 'Toulouse',
    },
    {
        'date': '2026-03-16',
        'time': '03:45',
        'league': 'Ligue 1',
        'home_team': 'Rennes',
        'away_team': 'Lille',
    },
]

# 儲存
os.makedirs('data', exist_ok=True)
with open('data/real_fixtures.json', 'w', encoding='utf-8') as f:
    json.dump(REAL_FIXTURES, f, ensure_ascii=False, indent=2)

print("✅ 已載入真實賽程")
print("="*70)
print(f"📊 總共 {len(REAL_FIXTURES)} 場比賽")

# 統計
by_league = {}
by_date = {}
for f in REAL_FIXTURES:
    league = f['league']
    date = f['date']
    by_league[league] = by_league.get(league, 0) + 1
    by_date[date] = by_date.get(date, 0) + 1

print("\n📋 各聯賽賽程:")
for league, count in sorted(by_league.items()):
    print(f"   {league}: {count} 場")

print("\n📅 各日期賽程:")
for date, count in sorted(by_date.items()):
    print(f"   {date}: {count} 場")

print("\n📁 已儲存到 data/real_fixtures.json")
print("="*70)
print("\n💡 下一步: 執行預測")
print("   docker compose exec api python scripts/predict_real_fixtures.py")
