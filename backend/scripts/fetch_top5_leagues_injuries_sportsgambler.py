import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import json

LEAGUES = [
    {"key": "epl", "url": "https://www.sportsgambler.com/injuries/football/", "top_players_csv": "epl_team_top_players_sofascore_std.csv"},
    {"key": "laliga", "url": "https://www.sportsgambler.com/injuries/football/spain-la-liga/", "top_players_csv": "laliga_team_top_players_sofascore_std.csv"},
    {"key": "bundesliga", "url": "https://www.sportsgambler.com/injuries/football/germany-bundesliga/", "top_players_csv": "bundesliga_team_top_players_sofascore_std.csv"},
    {"key": "serie_a", "url": "https://www.sportsgambler.com/injuries/football/italy-serie-a/", "top_players_csv": "serie_a_team_top_players_sofascore_std.csv"},
    {"key": "ligue_1", "url": "https://www.sportsgambler.com/injuries/football/france-ligue-1/", "top_players_csv": "ligue_1_team_top_players_sofascore_std.csv"},
]

def build_sofa_lookup(team_top_players_sofascore_csv):
    lookup = {}
    with open(team_top_players_sofascore_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["player_name"].strip().lower(), row["team_std"].strip().lower())
            lookup[key] = row["player_id"]
    return lookup

def main():
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "team_name_map.json", "r", encoding="utf-8") as f:
        team_name_map = json.load(f)

    def map_team_name(team_name):
        return team_name_map.get(team_name, team_name)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9"
    }

    for league in LEAGUES:
        print(f"\n==== 抓取 {league['key']} 傷兵 ====")

        resp = requests.get(league["url"], headers=headers, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        top_players_csv = out_dir / league["top_players_csv"]
        if not top_players_csv.exists():
            print(f"❌ missing top_players: {top_players_csv}")
            continue

        sofa_lookup = build_sofa_lookup(str(top_players_csv))

        rows = []
        for block in soup.select("div.injury-block"):
            team_tag = block.find("h3")
            team = team_tag.get_text(strip=True) if team_tag else "Unknown"
            team_std = map_team_name(team).strip().lower()

            for container in block.select("div.inj-container"):
                player_name = container.select_one("span.inj-player")
                player_name = player_name.get_text(strip=True) if player_name else ""
                row = {
                    "team": team,
                    "team_std": team_std,
                    "type": container.select_one("span.inj-type").get_text(strip=True) if container.select_one("span.inj-type") else "",
                    "player": player_name,
                    "position": container.select_one("span.inj-position").get_text(strip=True) if container.select_one("span.inj-position") else "",
                    "games": container.select_one("span.inj-game").get_text(strip=True) if container.select_one("span.inj-game") else "",
                    "goals": container.select_one("span.inj-goals").get_text(strip=True) if container.select_one("span.inj-goals") else "",
                    "assists": container.select_one("span.inj-assist").get_text(strip=True) if container.select_one("span.inj-assist") else "",
                    "info": container.select_one("span.inj-info").get_text(strip=True) if container.select_one("span.inj-info") else "",
                    "expected_return": container.select_one("span.inj-return").get_text(strip=True) if container.select_one("span.inj-return") else "",
                }
                key = (player_name.strip().lower(), team_std)
                row["player_id"] = sofa_lookup.get(key, "")
                if row["player"]:
                    rows.append(row)

        if not rows:
            print(f"⚠️ No injuries found for {league['key']}.")
            continue

        injuries_csv = out_dir / f"{league['key']}_teams_injuries_sportsgambler.csv"
        with open(injuries_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"✅ Saved {len(rows)} injuries to {injuries_csv}")

if __name__ == "__main__":
    main()