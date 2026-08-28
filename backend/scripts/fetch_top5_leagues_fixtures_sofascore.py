"""
scripts/fetch_top5_leagues_fixtures_sofascore.py

爬取五大聯賽完整賽程 + 比分 + 賽果
- finished: 有比分、勝負結果
- scheduled: 只有時間，無比分
"""

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from pathlib import Path
import csv

LEAGUES = [
    {"name": "Premier League", "tournament_id": 17,  "season_id": 76986, "round_max": 38},
    {"name": "LaLiga",         "tournament_id": 8,   "season_id": 77559, "round_max": 38},
    {"name": "Bundesliga",     "tournament_id": 35,  "season_id": 77333, "round_max": 34},
    {"name": "Serie A",        "tournament_id": 23,  "season_id": 76457, "round_max": 38},
    {"name": "Ligue 1",        "tournament_id": 34,  "season_id": 77356, "round_max": 34},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

FIELDNAMES = [
    "round", "time_utc", "time_tw",
    "home", "away",
    "home_score", "away_score",   # ← 新增
    "result",                      # ← H / D / A / None
    "status",
    "sofascore_id",               # ← 方便日後補爬詳細數據
]

def fetch_json(api_url: str) -> dict:
    with sync_playwright() as p:
        ctx = p.request.new_context(extra_http_headers=HEADERS)
        resp = ctx.get(api_url)
        data = resp.json()
        ctx.dispose()
    return data

def parse_result(home_score, away_score) -> str | None:
    """回傳 H / D / A，未完賽回傳 None"""
    if home_score is None or away_score is None:
        return None
    if home_score > away_score:
        return "H"
    elif home_score < away_score:
        return "A"
    return "D"

def parse_event(ev: dict, rnd: int) -> dict:
    start_utc = datetime.utcfromtimestamp(ev["startTimestamp"])
    start_tw  = start_utc + timedelta(hours=8)

    status_type = ev.get("status", {}).get("type", "scheduled")

    # 比分：只有 finished / inprogress 才有
    home_score = away_score = None
    score_data = ev.get("homeScore") or {}
    away_data  = ev.get("awayScore") or {}

    if status_type in ("finished", "inprogress"):
        # current 優先，沒有才用 normaltime
        home_score = score_data.get("current") or score_data.get("normaltime")
        away_score = away_data.get("current")  or away_data.get("normaltime")

    return {
        "round":       rnd,
        "time_utc":    start_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "time_tw":     start_tw.strftime("%Y-%m-%d %H:%M:%S"),
        "home":        ev["homeTeam"]["name"],
        "away":        ev["awayTeam"]["name"],
        "home_score":  home_score if home_score is not None else "",
        "away_score":  away_score if away_score is not None else "",
        "result":      parse_result(home_score, away_score) or "",
        "status":      status_type,
        "sofascore_id": ev.get("id", ""),
    }

def save_csv(league_name: str, rows: list[dict]) -> None:
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f"{league_name.replace(' ', '_').lower()}_fixtures_sofascore.csv"

    with open(fname, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    finished  = sum(1 for r in rows if r["status"] == "finished")
    scheduled = sum(1 for r in rows if r["status"] != "finished")
    print(f"  💾 儲存至 {fname}")
    print(f"     已完賽: {finished}  未來賽程: {scheduled}  合計: {len(rows)}")

def fetch_league(league: dict) -> list[dict]:
    all_rows = []
    print(f"\n=== {league['name']} (season {league['season_id']}) ===")

    for rnd in range(1, league["round_max"] + 1):
        url = (
            f"https://api.sofascore.com/api/v1/unique-tournament/"
            f"{league['tournament_id']}/season/{league['season_id']}"
            f"/events/round/{rnd}"
        )
        try:
            data = fetch_json(url)
            events = data.get("events", [])
            for ev in events:
                all_rows.append(parse_event(ev, rnd))
            print(f"  Round {rnd:2d}: {len(events)} 場", end="")
            # 顯示本輪有比分的場數
            scored = sum(
                1 for ev in events
                if ev.get("status", {}).get("type") == "finished"
            )
            print(f"  (有比分: {scored})")
        except Exception as e:
            print(f"  Round {rnd:2d} error: {e}")

    return all_rows

if __name__ == "__main__":
    for league in LEAGUES:
        rows = fetch_league(league)
        if rows:
            save_csv(league["name"], rows)
        print(f"{league['name']} 共 {len(rows)} 場")
