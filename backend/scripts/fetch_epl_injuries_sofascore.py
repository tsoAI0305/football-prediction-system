"""Fetch EPL team injury lists from Sofascore API.

For each team in the current EPL season the script retrieves the full squad
list and filters for players flagged as injured or doubtful.

Sofascore season IDs (2024/25):
  Premier League  tournament_id=17  season_id=76986

Usage:
    python fetch_epl_injuries_sofascore.py

Output:
    epl_injuries_sofascore.csv
    Columns: team, team_id, player_name, player_id, position, injury_reason
"""

import csv

from playwright.sync_api import sync_playwright

EPL_TOURNAMENT_ID = 17
EPL_SEASON_ID = 76986

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
        try:
            response = request_context.get(api_url)
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status} for {api_url}")
            data = response.json()
        finally:
            request_context.dispose()
        return data


def fetch_epl_teams():
    """Return a list of {id, name} dicts for all EPL teams this season."""
    url = (
        f"https://api.sofascore.com/api/v1/unique-tournament/{EPL_TOURNAMENT_ID}"
        f"/season/{EPL_SEASON_ID}/teams"
    )
    data = fetch_sofascore_json_api(url)
    return [{"id": t["id"], "name": t["name"]} for t in data.get("teams", [])]


def fetch_team_injuries(team_id):
    """Return injured/doubtful players for *team_id* as a list of dicts."""
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/players"
    data = fetch_sofascore_json_api(url)
    injured = []
    for item in data.get("players", []):
        player = item.get("player", {})
        # Sofascore marks injured / doubtful players with `injured=True`
        # or a non-empty `injuryReason` string.
        if item.get("injured") or item.get("injuryReason"):
            injured.append({
                "player_id": player.get("id", ""),
                "player_name": player.get("name", ""),
                "position": player.get("position", ""),
                "injury_reason": item.get("injuryReason") or "Injury (reason unspecified)",
            })
    return injured


def save_injuries_csv(rows, filename="epl_injuries_sofascore.csv"):
    fieldnames = ["team", "team_id", "player_name", "player_id", "position", "injury_reason"]
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved: {filename} ({len(rows)} rows)")


if __name__ == "__main__":
    print("Fetching EPL teams...")
    teams = fetch_epl_teams()
    print(f"Found {len(teams)} teams")

    all_injured = []
    for team in teams:
        print(f"  {team['name']} (id={team['id']})...", end=" ", flush=True)
        try:
            injured = fetch_team_injuries(team["id"])
            for player in injured:
                player["team"] = team["name"]
                player["team_id"] = team["id"]
            all_injured.extend(injured)
            print(f"{len(injured)} injured/doubtful")
        except Exception as e:
            print(f"error: {e}")

    print(f"\nTotal injured/doubtful: {len(all_injured)}")
    save_injuries_csv(all_injured)
