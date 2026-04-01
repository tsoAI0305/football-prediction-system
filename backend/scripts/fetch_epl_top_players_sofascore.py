"""Fetch EPL top players by rating and goals from Sofascore API.

Sofascore season IDs (2024/25):
  Premier League  tournament_id=17  season_id=76986

Usage:
    python fetch_epl_top_players_sofascore.py

Output:
    epl_top_players_sofascore.csv
    Columns: rank, stat_type, player_name, player_id, team, team_id,
             goals, assists, rating
"""

import csv

from playwright.sync_api import sync_playwright

EPL_TOURNAMENT_ID = 17
EPL_SEASON_ID = 76986
TOP_N = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

# Each entry: label used in CSV and the sort order field for Sofascore
STAT_CONFIGS = [
    {"label": "rating", "order": "-rating"},
    {"label": "goals", "order": "-goals"},
]


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


def fetch_top_players(stat_label, order, limit=TOP_N):
    """Return a list of dicts for the top-N EPL players sorted by *order*."""
    url = (
        f"https://api.sofascore.com/api/v1/unique-tournament/{EPL_TOURNAMENT_ID}"
        f"/season/{EPL_SEASON_ID}/statistics"
        f"?limit={limit}&order={order}&accumulation=total"
        f"&fields=goals,assists,rating"
    )
    data = fetch_sofascore_json_api(url)
    rows = []
    for rank, item in enumerate(data.get("results", []), start=1):
        player = item.get("player", {})
        team = item.get("team", {})
        rows.append({
            "rank": rank,
            "stat_type": stat_label,
            "player_name": player.get("name", ""),
            "player_id": player.get("id", ""),
            "team": team.get("name", ""),
            "team_id": team.get("id", ""),
            "goals": item.get("goals", 0),
            "assists": item.get("assists", 0),
            "rating": item.get("rating", ""),
        })
    return rows


def save_top_players_csv(rows, filename="epl_top_players_sofascore.csv"):
    fieldnames = [
        "rank", "stat_type", "player_name", "player_id",
        "team", "team_id", "goals", "assists", "rating",
    ]
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved: {filename} ({len(rows)} rows)")


if __name__ == "__main__":
    all_rows = []
    for cfg in STAT_CONFIGS:
        print(f"\n--- Fetching top {TOP_N} by {cfg['label']} ---")
        rows = fetch_top_players(cfg["label"], cfg["order"])
        all_rows.extend(rows)
        print(f"  {len(rows)} players fetched")
    save_top_players_csv(all_rows)
