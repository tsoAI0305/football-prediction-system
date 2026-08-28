# coding=utf8
"""Fetch full squad roster with detailed positions from SofaScore.

Outputs: data/full_squads_std.csv
Columns: league, team, team_id, team_std, player_name, player_id,
         position_category, detailed_position, goals, assists, rating, is_injured

Run:
    python scripts/fetch_full_squad_data.py
"""
import csv
import json
import re
import time
import random
from pathlib import Path

from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUT_CSV  = DATA_DIR / "full_squads_std.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
}

MAX_RETRIES      = 3
REQUEST_TIMEOUT  = 60_000  # ms

LEAGUES = [
    {"name": "EPL",        "tournament_id": 17,  "season_id": 76986},
    {"name": "LaLiga",     "tournament_id": 8,   "season_id": 77559},
    {"name": "Bundesliga", "tournament_id": 35,  "season_id": 77333},
    {"name": "Serie A",    "tournament_id": 23,  "season_id": 76457},
    {"name": "Ligue 1",    "tournament_id": 34,  "season_id": 77356},
]

OUTPUT_FIELDS = [
    "league", "team", "team_id", "team_std",
    "player_name", "player_id",
    "position_category", "detailed_position",
    "goals", "assists", "rating", "is_injured",
]


# ── Normalisation ─────────────────────────────────────────────────────────────

def _std(name: str) -> str:
    try:
        from unidecode import unidecode
        name = unidecode(str(name))
    except ImportError:
        pass
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _p(msg: str) -> None:
    """Print with non-ASCII chars replaced to avoid cp950 console errors."""
    print(msg.encode("ascii", errors="replace").decode("ascii"))


def api_get(url: str) -> dict:
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as p:
                ctx = p.request.new_context(extra_http_headers=HEADERS)
                try:
                    r = ctx.get(url, timeout=REQUEST_TIMEOUT)
                    if r.status != 200:
                        raise RuntimeError(f"HTTP {r.status}: {url}")
                    return r.json()
                finally:
                    ctx.dispose()
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                _p(f"  [retry {attempt + 1}] {type(exc).__name__}: waiting {wait}s...")
                time.sleep(wait)
    raise last_exc


# ── SofaScore API helpers ─────────────────────────────────────────────────────

def fetch_teams(tournament_id: int, season_id: int) -> list[dict]:
    url = (f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}"
           f"/season/{season_id}/teams")
    data = api_get(url)
    return [{"id": t["id"], "name": t["name"]} for t in data.get("teams", [])]


def _extract_detailed_position(player_obj: dict) -> tuple[str, str]:
    """Return (position_category, detailed_position) from a SofaScore player dict.

    SofaScore player objects include:
      - positionCategory: "G" / "D" / "M" / "F"
      - position: string like "G", or dict {"abbrevation": "GK", ...}
      - specificPosition: dict {"abbrevation": "CB", ...}  (not always present)
      - userDefinedType: sometimes carries detailed position
    """
    # Broad category
    broad = str(player_obj.get("positionCategory") or "").upper().strip()
    if not broad:
        pos_raw = player_obj.get("position")
        if isinstance(pos_raw, dict):
            broad = str(pos_raw.get("abbrevation") or pos_raw.get("name") or "").upper()[:2]
        else:
            broad = str(pos_raw or "").upper()[:2]

    # Detailed position — try specificPosition first, then position dict
    detail = ""
    for field in ("specificPosition", "position"):
        raw = player_obj.get(field)
        if isinstance(raw, dict):
            abbr = str(raw.get("abbrevation") or raw.get("abbreviation") or "").upper().strip()
            if abbr and abbr != broad:
                detail = abbr
                break

    # If still no detail, use the broad category as-is
    if not detail:
        detail = broad

    return broad, detail


def fetch_squad(team_id: int) -> list[dict]:
    """Return list of {player_id, player_name, position_category, detailed_position}."""
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/players"
    data = api_get(url)
    result = []
    for item in data.get("players", []):
        p = item.get("player", {}) or {}
        pid = p.get("id")
        if not pid:
            continue
        broad, detail = _extract_detailed_position(p)
        result.append({
            "player_id":         str(pid),
            "player_name":       p.get("name", ""),
            "position_category": broad,
            "detailed_position": detail,
        })
    return result


def load_existing_player_cache(league_name: str) -> dict:
    """Merge existing player cache (from fetch_top5_leagues_top_players_sofascore.py)
    into the stats lookup so GKs and reserve players have their ratings."""
    cache_file = DATA_DIR / f"player_cache_{league_name.lower()}.json"
    if not cache_file.exists():
        return {}
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        # Cache format: {player_id: {goals, assists, rating}}
        return {str(k): v for k, v in data.items()}
    except Exception:
        return {}


def fetch_league_stats(tournament_id: int, season_id: int, league_name: str = "") -> dict:
    """Build {player_id → {goals, assists, rating}} from league stats API.
    Also merges existing player caches so GKs and reserve players have ratings."""
    # Start from existing cache (covers GKs not in top-500 outfield stats)
    lookup: dict[str, dict] = load_existing_player_cache(league_name)

    for order, limit in [("-rating", 500), ("-goals", 300), ("-assists", 300)]:
        url = (
            f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}"
            f"/season/{season_id}/statistics"
            f"?limit={limit}&order={order}&accumulation=total&fields=goals,assists,rating"
        )
        try:
            data = api_get(url)
        except Exception as exc:
            _p(f"  WARN: stats fetch failed ({order}): {exc}")
            continue
        for item in data.get("results", []):
            p = item.get("player", {}) or {}
            pid = str(p.get("id", ""))
            if not pid:
                continue
            prev = lookup.get(pid, {})
            lookup[pid] = {
                "goals":   item.get("goals",   prev.get("goals",   0)) or 0,
                "assists": item.get("assists", prev.get("assists", 0)) or 0,
                "rating":  item.get("rating",  prev.get("rating",  0)) or 0,
            }
    return lookup


# ── Injury cross-reference ────────────────────────────────────────────────────

def build_injured_set() -> set[str]:
    """Build normalised set of injured player names from local CSV files."""
    injured: set[str] = set()
    for f in DATA_DIR.glob("*_teams_injuries_sportsgambler.csv"):
        try:
            import csv as _csv
            with open(f, encoding="utf-8") as fh:
                for row in _csv.DictReader(fh):
                    name = str(row.get("player", "") or "").strip()
                    if name and name not in ("", "Name"):
                        injured.add(_std(name))
        except Exception:
            pass
    return injured


# ── Checkpoint helpers ────────────────────────────────────────────────────────

def _ckpt_path(league_name: str) -> Path:
    return DATA_DIR / f"_ckpt_full_squad_{league_name.lower().replace(' ', '_')}.json"


def load_ckpt(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done_team_ids": [], "rows": []}


def save_ckpt(ckpt: dict, path: Path) -> None:
    path.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Main fetch loop ───────────────────────────────────────────────────────────

def fetch_league(league: dict, injured_set: set[str]) -> list[dict]:
    name          = league["name"]
    tournament_id = league["tournament_id"]
    season_id     = league["season_id"]
    ckpt_file     = _ckpt_path(name)

    _p(f"\n=== {name} ===")
    _p("Fetching teams...")
    teams = fetch_teams(tournament_id, season_id)
    _p(f"Found {len(teams)} teams")

    _p("Building stats lookup...")
    stats = fetch_league_stats(tournament_id, season_id, league_name=name)

    ckpt = load_ckpt(ckpt_file)
    done = set(str(t) for t in ckpt["done_team_ids"])
    rows: list[dict] = list(ckpt["rows"])

    for team in teams:
        tid   = str(team["id"])
        tname = team["name"]

        if tid in done:
            continue

        time.sleep(random.uniform(0.5, 1.5))

        try:
            squad = fetch_squad(team["id"])
        except Exception as exc:
            _p(f"  WARN: squad fetch failed for {tname}: {exc}")
            done.add(tid)
            ckpt["done_team_ids"] = list(done)
            save_ckpt(ckpt, ckpt_file)
            continue

        team_std = _std(tname)
        for sp in squad:
            pid   = sp["player_id"]
            pname = sp["player_name"]
            s     = stats.get(pid, {"goals": 0, "assists": 0, "rating": 0})
            rows.append({
                "league":            name,
                "team":              tname,
                "team_id":           tid,
                "team_std":          tname,  # mapped later via top5_leagues_top_players_std.py style
                "player_name":       pname,
                "player_id":         pid,
                "position_category": sp["position_category"],
                "detailed_position": sp["detailed_position"],
                "goals":             s.get("goals",   0),
                "assists":           s.get("assists", 0),
                "rating":            round(float(s.get("rating", 0) or 0), 2),
                "is_injured":        1 if _std(pname) in injured_set else 0,
            })

        done.add(tid)
        ckpt["done_team_ids"] = list(done)
        ckpt["rows"] = rows
        save_ckpt(ckpt, ckpt_file)
        _p(f"  OK {tname} ({len(done)}/{len(teams)})  [{len(squad)} players]")

    if ckpt_file.exists():
        ckpt_file.unlink()

    return rows


def apply_team_name_map(rows: list[dict]) -> list[dict]:
    """Resolve team_std using team_name_map.json (same logic as top_players_std.py)."""
    map_file = DATA_DIR / "team_name_map.json"
    name_map: dict = {}
    if map_file.exists():
        try:
            name_map = json.loads(map_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    for row in rows:
        row["team_std"] = name_map.get(row["team"], row["team"])
    return rows


def main() -> None:
    _p("Building injury cross-reference...")
    injured_set = build_injured_set()
    _p(f"  {len(injured_set)} injured players indexed")

    all_rows: list[dict] = []
    for league in LEAGUES:
        all_rows.extend(fetch_league(league, injured_set))

    all_rows = apply_team_name_map(all_rows)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    _p(f"\nSaved {OUT_CSV} ({len(all_rows)} player-rows across {len(LEAGUES)} leagues)")


if __name__ == "__main__":
    main()
