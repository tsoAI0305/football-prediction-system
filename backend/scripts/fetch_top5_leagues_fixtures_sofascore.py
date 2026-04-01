from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

# Sofascore top5 major leagues資訊
LEAGUES = [
    {
        "name": "Premier League",
        "tournament_id": 17,
        "season_id": 76986,
        "round_max": 38,
    },
    {
        "name": "LaLiga",
        "tournament_id": 8,
        "season_id": 77559,
        "round_max": 38,
    },
    {
        "name": "Bundesliga",
        "tournament_id": 35,
        "season_id": 77333,
        "round_max": 34,
    },
    {
        "name": "Serie A",
        "tournament_id": 23,
        "season_id": 76457,
        "round_max": 38,
    },
    {
        "name": "Ligue 1",
        "tournament_id": 34,
        "season_id": 77356,
        "round_max": 34,
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

def fetch_sofascore_json_api(api_url):
    with sync_playwright() as p:
        request_context = p.request.new_context(extra_http_headers=HEADERS)
        response = request_context.get(api_url)
        data = response.json()
        request_context.dispose()
        return data

def save_fixtures_to_csv(league_name, fixtures):
    import csv, os
    fname = f"{league_name.replace(' ', '_').lower()}_fixtures_sofascore.csv"
    with open(fname, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['round', 'time_utc', 'time_tw', 'home', 'away', 'status'])
        writer.writeheader()
        writer.writerows(fixtures)
    print(f"✅ {league_name} saved: {fname}")

if __name__ == "__main__":
    for league in LEAGUES:
        allrows = []
        print(f"\n=== {league['name']} ===")
        for rnd in range(1, league['round_max']+1):
            url = (
                f"https://api.sofascore.com/api/v1/unique-tournament/"
                f"{league['tournament_id']}/season/{league['season_id']}/events/round/{rnd}"
            )
            try:
                data = fetch_sofascore_json_api(url)
                for ev in data.get('events', []):
                    start_utc = datetime.utcfromtimestamp(ev["startTimestamp"])
                    start_tw = start_utc + timedelta(hours=8)  # 台灣時區
                    allrows.append({
                        'round': rnd,
                        'time_utc': start_utc.strftime('%Y-%m-%d %H:%M:%S'),
                        'time_tw': start_tw.strftime('%Y-%m-%d %H:%M:%S'),
                        'home': ev["homeTeam"]["name"],
                        'away': ev["awayTeam"]["name"],
                        'status': ev["status"]["type"]
                })
                print(f"Round {rnd:2d}: {len(data.get('events', []))} matches")
            except Exception as e:
                print(f"Round {rnd:2d} error: {e}")

        print(f"{league['name']} total matches: {len(allrows)}")
        save_fixtures_to_csv(league['name'], allrows)