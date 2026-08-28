# coding=utf8
import csv
import json
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
}

TOP_N_PER_TEAM = 3
MAX_RETRIES = 3
REQUEST_TIMEOUT_MS = 60000  # raised from 30000

STAT_CONFIGS = [
    {"label": "rating", "order": "-rating"},
    {"label": "goals", "order": "-goals"},
    {"label": "assists", "order": "-assists"},
]

LEAGUES = [
    {
        "name": "EPL",
        "filename": "epl_team_top_players_sofascore.csv",
        "tournament_id": 17,
        "season_id": 76986,
    },
    {
        "name": "LaLiga",
        "filename": "laliga_team_top_players_sofascore.csv",
        "tournament_id": 8,
        "season_id": 77559,
    },
    {
        "name": "Bundesliga",
        "filename": "bundesliga_team_top_players_sofascore.csv",
        "tournament_id": 35,
        "season_id": 77333,
    },
    {
        "name": "Serie A",
        "filename": "serie_a_team_top_players_sofascore.csv",
        "tournament_id": 23,
        "season_id": 76457,
    },
    {
        "name": "Ligue 1",
        "filename": "ligue_1_team_top_players_sofascore.csv",
        "tournament_id": 34,
        "season_id": 77356,
    }
]


def api_get(url):
    """Fetch URL via Playwright with retry + exponential backoff."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as p:
                ctx = p.request.new_context(extra_http_headers=HEADERS)
                try:
                    r = ctx.get(url, timeout=REQUEST_TIMEOUT_MS)
                    if r.status != 200:
                        raise RuntimeError(f"HTTP {r.status}: {url}")
                    return r.json()
                finally:
                    ctx.dispose()
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)  # 2s, 4s
                print(f"  [retry {attempt + 1}/{MAX_RETRIES - 1}] {type(exc).__name__}: waiting {wait}s…")
                time.sleep(wait)
    raise last_exc


def fetch_teams(tournament_id, season_id):
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/teams"
    data = api_get(url)
    return [{"id": t["id"], "name": t["name"]} for t in data.get("teams", [])]


def fetch_team_players(team_id):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/players"
    data = api_get(url)
    players = []
    for it in data.get("players", []):
        p = it.get("player", {}) or {}
        if not p.get("id"):
            continue
        pos_cat = (p.get("positionCategory") or p.get("position", {}) or {})
        if isinstance(pos_cat, dict):
            pos_cat = pos_cat.get("abbrevation", "") or pos_cat.get("name", "")
        position = str(pos_cat or "").upper().strip()[:2]
        players.append({
            "player_id":   str(p["id"]),
            "player_name": p.get("name", ""),
            "position":    position,
        })
    return players


def fetch_league_stats(tournament_id, season_id, order, limit=500):
    url = (
        f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/statistics"
        f"?limit={limit}&order={order}&accumulation=total&fields=goals,assists,rating"
    )
    data = api_get(url)
    return data.get("results", [])


def build_stats_lookup(tournament_id, season_id):
    lookup = {}
    for cfg in STAT_CONFIGS:
        results = fetch_league_stats(tournament_id, season_id, cfg["order"], limit=500)
        for item in results:
            p = item.get("player", {}) or {}
            t = item.get("team", {}) or {}
            pid = str(p.get("id", ""))
            if not pid:
                continue
            prev = lookup.get(pid, {})
            lookup[pid] = {
                "player_name": p.get("name", prev.get("player_name", "")),
                "team_id": str(t.get("id", prev.get("team_id", ""))),
                "team": t.get("name", prev.get("team", "")),
                "goals": item.get("goals", prev.get("goals", 0)) or 0,
                "assists": item.get("assists", prev.get("assists", 0)) or 0,
                "rating": item.get("rating", prev.get("rating", 0)) or 0,
            }
    return lookup


def top_n(rows, key, n=3):
    rows = sorted(rows, key=lambda x: float(x.get(key, 0) or 0), reverse=True)
    return rows[:n]


def format_row(row):
    _row = dict(row)
    try:
        _row["rating"] = "{:.2f}".format(float(_row["rating"]))
    except Exception:
        pass
    return _row


def load_cache(cache_file):
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache, cache_file):
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_player_overall_stats(player_id, tournament_id, season_id, player_cache, cache_file):
    if player_id in player_cache:
        return player_cache[player_id]
    url = (
        f"https://api.sofascore.com/api/v1/player/{player_id}"
        f"/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
    )
    try:
        data = api_get(url)
    except Exception:
        player_cache[player_id] = {"goals": 0, "assists": 0, "rating": 0}
        return player_cache[player_id]
    s = data.get("statistics", {}) or {}
    stats = {
        "goals": s.get("goals", 0) or 0,
        "assists": s.get("assists", 0) or 0,
        "rating": s.get("rating", 0) or 0,
    }
    player_cache[player_id] = stats
    if len(player_cache) % 10 == 0:
        save_cache(player_cache, cache_file)
    return stats


# ── Checkpoint helpers ────────────────────────────────────────────────────────

def _ckpt_path(out_dir, league_name):
    return out_dir / f"_checkpoint_{league_name.lower().replace(' ', '_')}.json"


def load_checkpoint(ckpt_file):
    if ckpt_file.exists():
        try:
            with open(ckpt_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"done_team_ids": [], "rows": []}


def save_checkpoint(ckpt, ckpt_file):
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)


def clear_checkpoint(ckpt_file):
    if ckpt_file.exists():
        ckpt_file.unlink()


# ─────────────────────────────────────────────────────────────────────────────

def fetch_and_write_league_top_players(league):
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / league["filename"]
    cache_file = out_dir / f"player_cache_{league['name'].lower()}.json"
    ckpt_file = _ckpt_path(out_dir, league["name"])
    tournament_id = league["tournament_id"]
    season_id = league["season_id"]

    print(f"\n=== {league['name']} ===")
    print("Fetching teams...")
    teams = fetch_teams(tournament_id, season_id)
    print(f"Found {len(teams)} teams")

    print("Building league stats lookup...")
    stats_lookup = build_stats_lookup(tournament_id, season_id)

    player_cache = load_cache(cache_file)
    ckpt = load_checkpoint(ckpt_file)
    done_ids = set(str(tid) for tid in ckpt["done_team_ids"])
    all_rows = list(ckpt["rows"])

    if done_ids:
        print(f"  Resuming: {len(done_ids)} teams already done, {len(teams) - len(done_ids)} remaining")

    for team in teams:
        tid = str(team["id"])
        tname = team["name"]

        if tid in done_ids:
            continue

        # Random delay between teams to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))

        try:
            squad = fetch_team_players(team["id"])
        except Exception as exc:
            print(f"  WARN: failed to fetch squad for {tname} — {exc}")
            continue

        enriched = []
        for sp in squad:
            pid = sp["player_id"]
            s = stats_lookup.get(pid, {})
            goals = s.get("goals", 0)
            assists = s.get("assists", 0)
            rating = s.get("rating", 0)
            if goals == 0 and assists == 0 and float(rating or 0) == 0:
                time.sleep(0.3)
                ps = fetch_player_overall_stats(pid, tournament_id, season_id, player_cache, cache_file)
                if ps:
                    goals = ps.get("goals", 0)
                    assists = ps.get("assists", 0)
                    rating = ps.get("rating", 0)
                print(f"fetch {pid} {sp['player_name']}: {goals} {assists} {rating}")
            enriched.append(
                {
                    "team":        tname,
                    "team_id":     tid,
                    "player_name": sp["player_name"],
                    "player_id":   pid,
                    "position":    sp.get("position", ""),
                    "goals":       goals,
                    "assists":     assists,
                    "rating":      rating,
                }
            )

        for stat_type, key in [("rating", "rating"), ("goals", "goals"), ("assists", "assists")]:
            tops = top_n(enriched, key, TOP_N_PER_TEAM)
            for i, r in enumerate(tops, start=1):
                all_rows.append(
                    {
                        "team":        r["team"],
                        "team_id":     r["team_id"],
                        "stat_type":   stat_type,
                        "rank":        i,
                        "player_name": r["player_name"],
                        "player_id":   r["player_id"],
                        "position":    r.get("position", ""),
                        "goals":       r["goals"],
                        "assists":     r["assists"],
                        "rating":      r["rating"],
                    }
                )

        done_ids.add(tid)
        ckpt["done_team_ids"] = list(done_ids)
        ckpt["rows"] = all_rows
        save_checkpoint(ckpt, ckpt_file)
        print(f"  ✓ {tname} ({len(done_ids)}/{len(teams)})")

    save_cache(player_cache, cache_file)

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["team", "team_id", "stat_type", "rank", "player_name", "player_id", "position", "goals", "assists", "rating"],
        )
        writer.writeheader()
        writer.writerows([format_row(r) for r in all_rows])

    clear_checkpoint(ckpt_file)
    print(f"✅ Saved: {out_csv} ({len(all_rows)} rows)")


if __name__ == "__main__":
    for league in LEAGUES:
        fetch_and_write_league_top_players(league)
