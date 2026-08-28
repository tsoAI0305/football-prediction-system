# coding=utf8
"""Fetch detailed sub-positions for all squads using SofaScore Starting Lineup API.

Strategy (per team, in priority order):
  1. GET /api/v1/team/{team_id}/events/last/0  → get most recent event_id
  2. GET /api/v1/event/{event_id}/lineups      → starting 11 with detailed position
  3. GET /api/v1/player/{player_id}            → bench player profile fallback
  4. formationPosition + formation string      → geometric fallback

Outputs: data/full_squads_std.csv  (updates detailed_position column in-place)

Teams where lineup fetch fails = their rows are marked with broad category only
and NOT overwritten (existing broad G/D/M/F is kept).

Run:
    python scripts/fetch_real_squad_positions.py
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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.sofascore.com/",
}

MAX_RETRIES     = 3
REQUEST_TIMEOUT = 60_000

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

# ── Verbose position name → abbreviated code ──────────────────────────────────
# Keys are lowercased partial matches; checked in order (longest first at runtime)
_POSITION_NAME_MAP: dict[str, str] = {
    # Goalkeepers
    "goalkeeper":             "GK",
    # Centre-back variants
    "centre-back":            "CB",
    "center-back":            "CB",
    "central defender":       "CB",
    "centre back":            "CB",
    "center back":            "CB",
    # Full-backs
    "left back":              "LB",
    "left-back":              "LB",
    "right back":             "RB",
    "right-back":             "RB",
    # Wing-backs
    "left wing-back":         "LWB",
    "left wingback":          "LWB",
    "right wing-back":        "RWB",
    "right wingback":         "RWB",
    # Defensive midfielders
    "defensive midfielder":   "DM",
    "central defensive":      "DM",
    # Central midfielders
    "central midfielder":     "CM",
    "centre midfielder":      "CM",
    "box-to-box":             "CM",
    # Wide midfielders
    "left midfielder":        "LM",
    "right midfielder":       "RM",
    # Attacking midfielders
    "attacking midfielder":   "AM",
    "second striker":         "SS",
    # Wingers
    "left wing":              "LW",
    "left winger":            "LW",
    "right wing":             "RW",
    "right winger":           "RW",
    # Forwards
    "centre-forward":         "ST",
    "center-forward":         "ST",
    "centre forward":         "ST",
    "center forward":         "ST",
    "striker":                "ST",
    "forward":                "ST",
}

# Build a sorted list (longest match first) for greedy matching
_SORTED_POSITION_KEYS = sorted(_POSITION_NAME_MAP, key=len, reverse=True)

# ── Formation position number → sub-position code ────────────────────────────
# Numbers run: 1=GK, then bottom-to-top rows, left-to-right within each row.
# Only the most common formations are listed; others fall back to broad category.
_FP_MAP: dict[str, dict[int, str]] = {
    "4-3-3":   {1:"GK", 2:"LB",  3:"CB",  4:"CB",  5:"RB",
                6:"DM", 7:"CM",  8:"CM",
                9:"LW", 10:"ST", 11:"RW"},
    "4-2-3-1": {1:"GK", 2:"LB",  3:"CB",  4:"CB",  5:"RB",
                6:"DM", 7:"DM",
                8:"LW", 9:"AM",  10:"RW",
                11:"ST"},
    "4-1-2-3": {1:"GK", 2:"LB",  3:"CB",  4:"CB",  5:"RB",
                6:"DM",
                7:"CM", 8:"CM",
                9:"LW", 10:"ST", 11:"RW"},
    "4-4-2":   {1:"GK", 2:"LB",  3:"CB",  4:"CB",  5:"RB",
                6:"LM", 7:"CM",  8:"CM",  9:"RM",
                10:"ST", 11:"ST"},
    "4-4-1-1": {1:"GK", 2:"LB",  3:"CB",  4:"CB",  5:"RB",
                6:"LM", 7:"CM",  8:"CM",  9:"RM",
                10:"SS", 11:"ST"},
    "3-4-3":   {1:"GK", 2:"CB",  3:"CB",  4:"CB",
                5:"LWB",6:"DM",  7:"DM",  8:"RWB",
                9:"LW", 10:"ST", 11:"RW"},
    "3-4-2-1": {1:"GK", 2:"CB",  3:"CB",  4:"CB",
                5:"LWB",6:"DM",  7:"DM",  8:"RWB",
                9:"LW", 10:"RW",
                11:"ST"},
    "3-5-2":   {1:"GK", 2:"CB",  3:"CB",  4:"CB",
                5:"LWB",6:"DM",  7:"CM",  8:"CM",  9:"RWB",
                10:"ST",11:"ST"},
    "3-3-2-2": {1:"GK", 2:"CB",  3:"CB",  4:"CB",
                5:"DM", 6:"CM",  7:"CM",
                8:"LW", 9:"RW",
                10:"ST",11:"ST"},
    "5-3-2":   {1:"GK", 2:"LWB", 3:"CB",  4:"CB",  5:"CB",  6:"RWB",
                7:"DM", 8:"CM",  9:"CM",
                10:"ST",11:"ST"},
    "5-4-1":   {1:"GK", 2:"LWB", 3:"CB",  4:"CB",  5:"CB",  6:"RWB",
                7:"LM", 8:"CM",  9:"CM",  10:"RM",
                11:"ST"},
}

# Abbreviated code → broad category (for position_category column)
_CODE_TO_BROAD: dict[str, str] = {
    "GK":"G",
    "CB":"D", "LB":"D", "RB":"D", "LWB":"D", "RWB":"D", "SW":"D",
    "DM":"M", "CM":"M", "LM":"M", "RM":"M", "AM":"M", "CAM":"M",
    "LW":"F", "RW":"F", "ST":"F", "CF":"F", "SS":"F", "WF":"F",
}


# ── Utility ───────────────────────────────────────────────────────────────────

def _p(msg: str) -> None:
    print(msg.encode("ascii", errors="replace").decode("ascii"))


def _std(name: str) -> str:
    try:
        from unidecode import unidecode
        name = unidecode(str(name))
    except ImportError:
        pass
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _map_verbose(text: str) -> str:
    """Convert verbose position name to abbreviated code, or return empty string."""
    t = text.lower().strip()
    for key in _SORTED_POSITION_KEYS:
        if key in t:
            return _POSITION_NAME_MAP[key]
    return ""


def _extract_position_from_player_obj(p: dict) -> tuple[str, str]:
    """Extract (position_category, detailed_position) from a SofaScore player dict.

    Priority:
      1. specificPosition.abbrevation  → "ST", "CB", "LB" etc.
      2. position dict abbrevation/name → try verbose mapping
      3. positionCategory → broad G/D/M/F
    """
    # specificPosition
    sp = p.get("specificPosition")
    if isinstance(sp, dict):
        abbr = str(sp.get("abbrevation") or sp.get("abbreviation") or "").upper().strip()
        if abbr:
            broad = _CODE_TO_BROAD.get(abbr, "")
            if not broad:
                broad = str(p.get("positionCategory") or "").upper()[:1]
            return broad, abbr

    # position field
    pos_raw = p.get("position")
    if isinstance(pos_raw, dict):
        abbr = str(pos_raw.get("abbrevation") or pos_raw.get("abbreviation") or "").upper().strip()
        name_str = str(pos_raw.get("name") or "").strip()
        code = _map_verbose(name_str) if name_str else _map_verbose(abbr.lower())
        if code:
            broad = _CODE_TO_BROAD.get(code, "")
            return broad, code
    elif isinstance(pos_raw, str) and len(pos_raw) > 2:
        code = _map_verbose(pos_raw)
        if code:
            broad = _CODE_TO_BROAD.get(code, "")
            return broad, code

    # Broad fallback
    broad = str(p.get("positionCategory") or p.get("position") or "").upper()[:1]
    return broad, broad


# ── HTTP helper ───────────────────────────────────────────────────────────────

def api_get(url: str) -> dict:
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as pw:
                ctx = pw.request.new_context(extra_http_headers=HEADERS)
                try:
                    r = ctx.get(url, timeout=REQUEST_TIMEOUT)
                    if r.status == 404:
                        return {}
                    if r.status != 200:
                        raise RuntimeError(f"HTTP {r.status}: {url}")
                    return r.json()
                finally:
                    ctx.dispose()
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                _p(f"  [retry {attempt+1}] {type(exc).__name__}: waiting {wait}s...")
                time.sleep(wait)
    raise last_exc


# ── SofaScore lineup fetcher ──────────────────────────────────────────────────

def fetch_last_event_id(team_id: int) -> int | None:
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0"
    data = api_get(url)
    events = data.get("events", [])
    if not events:
        return None
    return events[-1].get("id")  # last event in list = most recent


def fetch_lineup_positions(event_id: int, team_id: int) -> dict[str, tuple[str, str]]:
    """Return {player_id: (broad_category, detailed_position)} for starting 11.

    Uses the lineup entry's own `position` string (verbose) and the player's
    `specificPosition.abbrevation` as primary sources.  Falls back to
    `formationPosition` + formation name.
    """
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/lineups"
    data = api_get(url)
    result: dict[str, tuple[str, str]] = {}

    for side_key in ("home", "away"):
        side = data.get(side_key, {}) or {}
        side_team_id = (side.get("team") or {}).get("id")
        if side_team_id and str(side_team_id) != str(team_id):
            continue

        formation_str = str(side.get("formation") or "")
        fp_map = _FP_MAP.get(formation_str, {})

        for entry in side.get("players", []):
            player_obj = entry.get("player") or {}
            pid = str(player_obj.get("id", ""))
            if not pid:
                continue
            if entry.get("substitute"):
                continue  # only process starting 11 here

            # Try verbose position from the lineup entry itself
            entry_pos = str(entry.get("position") or "")
            code = _map_verbose(entry_pos) if len(entry_pos) > 2 else ""

            if code:
                broad = _CODE_TO_BROAD.get(code, "")
                result[pid] = (broad, code)
                continue

            # Try specificPosition / position from player object
            broad, code = _extract_position_from_player_obj(player_obj)
            if code and code != broad:   # real sub-position found
                result[pid] = (broad, code)
                continue

            # Try formationPosition lookup
            fp = entry.get("formationPosition")
            if fp and fp in fp_map:
                code = fp_map[fp]
                broad = _CODE_TO_BROAD.get(code, broad)
                result[pid] = (broad, code)
                continue

            # Keep broad category
            if broad:
                result[pid] = (broad, broad)

    return result


def fetch_player_position(player_id: int) -> tuple[str, str]:
    """Fetch single player profile to get specificPosition."""
    url = f"https://api.sofascore.com/api/v1/player/{player_id}"
    try:
        data = api_get(url)
        p = data.get("player") or {}
        return _extract_position_from_player_obj(p)
    except Exception:
        return ("", "")


# ── Per-team update ───────────────────────────────────────────────────────────

def update_team_positions(team_id: int, team_name: str,
                          rows: list[dict]) -> tuple[bool, int]:
    """Update `detailed_position` and `position_category` in rows for this team.

    Returns (success, updated_count).  Rows are modified in-place.
    """
    try:
        event_id = fetch_last_event_id(team_id)
        if not event_id:
            _p(f"  DISQUALIFIED (no events): {team_name}")
            return False, 0
    except Exception as exc:
        _p(f"  DISQUALIFIED (event fetch failed): {team_name}: {exc}")
        return False, 0

    time.sleep(random.uniform(0.4, 1.0))

    try:
        lineup_pos = fetch_lineup_positions(event_id, team_id)
    except Exception as exc:
        _p(f"  DISQUALIFIED (lineup fetch failed): {team_name}: {exc}")
        return False, 0

    if not lineup_pos:
        _p(f"  DISQUALIFIED (empty lineup): {team_name}")
        return False, 0

    # For bench players not in starting lineup, hit the player profile endpoint
    bench_ids = {
        r["player_id"] for r in rows
        if r["player_id"] not in lineup_pos
    }

    bench_pos: dict[str, tuple[str, str]] = {}
    for pid in bench_ids:
        time.sleep(random.uniform(0.15, 0.4))
        broad, detail = fetch_player_position(int(pid))
        if detail and detail != broad:
            bench_pos[pid] = (broad, detail)

    # Apply updates
    updated = 0
    for row in rows:
        pid = row["player_id"]
        pos = lineup_pos.get(pid) or bench_pos.get(pid)
        if pos:
            new_broad, new_detail = pos
            if new_detail and new_detail not in ("", row["detailed_position"]):
                row["position_category"] = new_broad or row["position_category"]
                row["detailed_position"] = new_detail
                updated += 1

    return True, updated


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not OUT_CSV.exists():
        _p(f"ERROR: {OUT_CSV} not found. Run fetch_full_squad_data.py first.")
        return

    _p(f"Reading {OUT_CSV}...")
    with open(OUT_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    _p(f"  {len(all_rows)} rows loaded")

    # Index by (team_id, league) → rows
    team_index: dict[str, list[dict]] = {}
    for row in all_rows:
        key = row.get("team_id", "")
        team_index.setdefault(key, []).append(row)

    disqualified: list[str] = []
    total_updated = 0

    for league in LEAGUES:
        _p(f"\n=== {league['name']} ===")
        league_rows = [r for r in all_rows if r["league"] == league["name"]]
        team_ids = sorted({r["team_id"]: r["team"] for r in league_rows}.items())

        for tid, tname in team_ids:
            rows_for_team = [r for r in league_rows if r["team_id"] == tid]
            time.sleep(random.uniform(0.5, 1.2))

            ok, cnt = update_team_positions(int(tid), tname, rows_for_team)
            if ok:
                _p(f"  OK {tname}: {cnt} positions updated")
                total_updated += cnt
            else:
                disqualified.append(tname)

    # Remove disqualified teams from output
    final_rows = [r for r in all_rows
                  if r["team"] not in disqualified]
    removed = len(all_rows) - len(final_rows)

    # Write back
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(final_rows)

    _p(f"\nDone. {total_updated} detailed positions updated.")
    _p(f"Disqualified: {len(disqualified)} teams removed ({removed} rows dropped).")
    _p(f"Saved: {OUT_CSV} ({len(final_rows)} rows)")

    if disqualified:
        _p("\nDisqualified teams (need re-fetch):")
        for t in disqualified:
            _p(f"  - {t}")


if __name__ == "__main__":
    main()
