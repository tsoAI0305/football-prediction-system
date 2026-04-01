"""Fetch EPL team-level top players by rating, goals, and assists from Sofascore API.

Sofascore season IDs (2024/25):
  Premier League  tournament_id=17  season_id=76986

Usage:
    python fetch_epl_top_players_sofascore.py

Output:
    backend/data/epl_team_top_players_sofascore.csv
    Columns: team, team_id, stat_type, rank, player_name, player_id,
             goals, assists, rating
"""

import csv
from pathlib import Path

from playwright.sync_api import sync_playwright

EPL_TOURNAMENT_ID = 17
EPL_SEASON_ID = 76986
TOP_N_PER_TEAM = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

STAT_CONFIGS = [
    {"label": "rating", "order": "-rating"},
    {"label": "goals", "order": "-goals"},
    {"label": "assists", "order": "-assists"},
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

def fetch_epl_teams():
    url = (
        f"https://api.sofascore.com/api/v1/unique-tournament/{EPL_TOURNAMENT_ID}"
        f"/season/{EPL_SEASON_ID}/teams"
    )
    data = fetch_sofascore_json_api(url)
    teams = [{"id": t["id"], "name": t["name"]} for t in data.get("teams", [])]
    return teams

def fetch_players_for_stat(order, limit=500):
    url = (
        f"https://api.sofascore.com/api/v1/unique-tournament/{EPL_TOURNAMENT_ID}"
        f"/season/{EPL_SEASON_ID}/statistics"
        f"?limit={limit}&order={order}&accumulation=total"
        f"&fields=goals,assists,rating"
    )
    data = fetch_sofascore_json_api(url)
    return data.get("results", [])

def build_team_top_rows(teams, results, stat_label, top_n=TOP_N_PER_TEAM):
    counts = {str(t["id"]): 0 for t in teams}
    rows = []

    for item in results:
        team = item.get("team", {}) or {}
        team_id = str(team.get("id", ""))
        if not team_id:
            continue
        if team_id not in counts:
            counts[team_id] = 0
        if counts[team_id] >= top_n:
            continue

        counts[team_id] += 1
        player = item.get("player", {}) or {}
        rows.append(
            {
                "team": team.get("name", ""),
                "team_id": team_id,
                "stat_type": stat_label,
                "rank": counts[team_id],
                "player_name": player.get("name", ""),
                "player_id": player.get("id", ""),
                "goals": item.get("goals", 0),
                "assists": item.get("assists", 0),
                "rating": item.get("rating", ""),
            }
        )

    missing = [t for t in teams if counts.get(str(t["id"]), 0) < top_n]
    if missing:
        missing_names = ", ".join(t["name"] for t in missing)
        print(
            f"⚠️  Missing top {top_n} players for: {missing_names}. "
            "Try increasing the API limit if this persists."
        )
    return rows

def save_csv(rows, filename):
    fieldnames = [
        "team",
        "team_id",
        "stat_type",
        "rank",
        "player_name",
        "player_id",
        "goals",
        "assists",
        "rating",
    ]
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved: {filename} ({len(rows)} rows)")

if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parents[1] / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "epl_team_top_players_sofascore.csv"

    print("Fetching EPL teams...")
    teams = fetch_epl_teams()
    print(f"Found {len(teams)} teams")

    all_rows = []
    for cfg in STAT_CONFIGS:
        print(f"\n--- Fetching team top {TOP_N_PER_TEAM} by {cfg['label']} ---")
        results = fetch_players_for_stat(cfg["order"], limit=500)
        rows = build_team_top_rows(teams, results, cfg["label"], TOP_N_PER_TEAM)
        all_rows.extend(rows)
        print(f"  {len(rows)} rows added")

    save_csv(all_rows, output_path)