"""
scripts/ingest_tactical_data.py

Phase 2 — Tactical data pipeline.

How it works (confirmed via HTML diagnostics)
---------------------------------------------
1. GET https://www.sportsgambler.com/lineups/football/<league-slug>/
   → server-side rendered; plain requests works fine.
   → Each match is a .lineup-row containing:
       .fxs-team (x2)           — home / away team names
       .lineups-toggle-button   — id attribute = Sportsgambler match id

2. For each match, GET /lineups/lineups-load2.php?id={match_id}
   → returns HTML fragment injected into #modify{id} by jQuery.
   → Formation lives in: span.lineups-toggle-formation  (one per team)

3. Formations are appended to data/tactical_formation_history.csv and
   matched against data/final_predictions.json to produce
   data/tactical_predicted_formations.csv.

4. Recency-weighted frequency (exponential decay, half-life = 10 matches)
   is written to data/tactical_formation_stats.csv.

Usage
-----
    python scripts/ingest_tactical_data.py
    python scripts/ingest_tactical_data.py --dry-run
"""

import argparse
import csv
import json
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, APIRequestContext

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Force UTF-8 stdout so accented team names (e.g. Atlético, Górnik) don't crash
# the preview on Windows terminals that default to CP950 / CP1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREDICTIONS_FILE = DATA_DIR / "final_predictions.json"
HISTORY_FILE     = DATA_DIR / "tactical_formation_history.csv"
PREDICTED_FILE   = DATA_DIR / "tactical_predicted_formations.csv"
STATS_FILE       = DATA_DIR / "tactical_formation_stats.csv"

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── tunables ──────────────────────────────────────────────────────────────────
HALF_LIFE_MATCHES  = 10     # exponential decay: weight halves every N matches
AJAX_DELAY_S       = 0.8    # pause between per-match AJAX calls (polite crawl)
LEAGUE_DELAY_S     = 2.0    # pause between league pages
REQUEST_TIMEOUT    = 30

BASE_URL  = "https://www.sportsgambler.com"
AJAX_PATH = "/lineups/lineups-load2.php"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{BASE_URL}/lineups/football/",
    "X-Requested-With": "XMLHttpRequest",
}

FORMATION_RE = re.compile(r"\b(\d-\d-\d(?:-\d)?)\b")

LEAGUES = [
    {
        "key":   "epl",
        "label": "Premier League",
        "url":   f"{BASE_URL}/lineups/football/england-premier-league/",
    },
    {
        "key":   "laliga",
        "label": "La Liga",
        "url":   f"{BASE_URL}/lineups/football/spain-la-liga/",
    },
    {
        "key":   "bundesliga",
        "label": "Bundesliga",
        "url":   f"{BASE_URL}/lineups/football/germany-bundesliga/",
    },
    {
        "key":   "serie_a",
        "label": "Serie A",
        "url":   f"{BASE_URL}/lineups/football/italy-serie-a/",
    },
    {
        "key":   "ligue_1",
        "label": "Ligue 1",
        "url":   f"{BASE_URL}/lineups/football/france-ligue-1/",
    },
]

# ── CSV schema ────────────────────────────────────────────────────────────────
HISTORY_FIELDS   = ["scraped_date", "team", "team_std", "league_key",
                    "formation", "match_date"]
PREDICTED_FIELDS = ["match_id", "league", "match_date", "home_team", "away_team",
                    "home_formation", "away_formation", "scraped_at"]
STATS_FIELDS     = ["team_std", "team", "formation", "weighted_count",
                    "raw_count", "pct", "is_primary"]


# ── name normalisation ────────────────────────────────────────────────────────

def _std(name: str) -> str:
    """Unidecode → lowercase → strip non-alphanum."""
    try:
        from unidecode import unidecode
        name = unidecode(str(name))
    except ImportError:
        name = str(name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ── CSV I/O ───────────────────────────────────────────────────────────────────

def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _save_history(rows: list[dict]) -> None:
    seen: dict[tuple, dict] = {}
    for r in rows:
        key = (r["team_std"], r.get("match_date", ""), r["formation"])
        seen[key] = r
    deduped = sorted(seen.values(),
                     key=lambda r: (r["team_std"], r.get("match_date", "")))
    with open(HISTORY_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        w.writeheader()
        w.writerows(deduped)
    log.info("History → %d rows  (%s)", len(deduped), HISTORY_FILE.name)


def _save_predicted(rows: list[dict]) -> None:
    with open(PREDICTED_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PREDICTED_FIELDS)
        w.writeheader()
        w.writerows(rows)
    log.info("Predicted → %d rows  (%s)", len(rows), PREDICTED_FILE.name)


def _save_stats(rows: list[dict]) -> None:
    with open(STATS_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=STATS_FIELDS)
        w.writeheader()
        w.writerows(rows)
    log.info("Stats → %d rows  (%s)", len(rows), STATS_FILE.name)


# ── recency-weighted frequency ────────────────────────────────────────────────

def _compute_formation_stats(history: list[dict]) -> list[dict]:
    """
    w_i = 0.5 ^ (rank_i / HALF_LIFE_MATCHES), rank_i = 0 for most recent match.
    Capturing tactical drift: a formation abandoned 10+ games ago counts half
    as much as the current one.
    """
    team_rows: dict[str, list[dict]] = defaultdict(list)
    for r in history:
        team_rows[r["team_std"]].append(r)

    out: list[dict] = []
    for team_std, matches in team_rows.items():
        matches.sort(key=lambda r: r.get("match_date", ""), reverse=True)
        team_name = matches[0].get("team", team_std)

        w_sum: dict[str, float] = defaultdict(float)
        raw:   dict[str, int]   = defaultdict(int)
        for rank, m in enumerate(matches):
            formation = m.get("formation", "").strip()
            if not formation:
                continue
            w_sum[formation] += 0.5 ** (rank / HALF_LIFE_MATCHES)
            raw[formation]   += 1

        total = sum(w_sum.values()) or 1.0
        sorted_f = sorted(w_sum.items(), key=lambda x: -x[1])
        primary = sorted_f[0][0] if sorted_f else ""

        for formation, w in sorted_f:
            out.append({
                "team_std":       team_std,
                "team":           team_name,
                "formation":      formation,
                "weighted_count": round(w, 4),
                "raw_count":      raw[formation],
                "pct":            round(w / total * 100, 1),
                "is_primary":     int(formation == primary),
            })
    return out


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(ctx: APIRequestContext, url: str, params: Optional[dict] = None) -> Optional[str]:
    """GET with retry (max 3 attempts). Returns response text or None."""
    for attempt in range(1, 4):
        try:
            r = ctx.get(url, params=params, timeout=REQUEST_TIMEOUT * 1000)
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            return r.text()
        except Exception as exc:
            log.warning("Attempt %d failed %s — %s", attempt, url, exc)
            if attempt < 3:
                time.sleep(2 ** attempt)
    return None


# ── fixture index ─────────────────────────────────────────────────────────────

def _build_fixture_lookup() -> dict[tuple[str, str], dict]:
    if not PREDICTIONS_FILE.exists():
        log.warning("final_predictions.json not found — predicted CSV will be empty.")
        return {}
    with open(PREDICTIONS_FILE, encoding="utf-8") as f:
        preds = json.load(f)
    lookup = {}
    for p in preds:
        if p.get("match_id") is None:
            continue
        lookup[(_std(p["home_team"]), _std(p["away_team"]))] = p
    return lookup


# ── date extraction ───────────────────────────────────────────────────────────

def _extract_date(tag, fallback: str) -> str:
    for attr in ("data-date", "data-match-date", "datetime"):
        val = (tag.get(attr) or "").strip()
        if re.match(r"\d{4}-\d{2}-\d{2}", val):
            return val[:10]
    text = tag.get_text(" ", strip=True)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return fallback


# ── main-page parser: one row per match ───────────────────────────────────────

def _parse_lineup_rows(html: str, confirmed_only: bool = True) -> list[dict]:
    """
    Parse the main league lineup page.

    confirmed_only=True (default): only return rows where the lineup button
    is green ("Confirmed Lineups"), skipping yellow "Predicted Lineups" rows
    that have no formation data yet — avoids wasted AJAX calls.

    Returns list of:
        {sg_id, home_team, away_team, home_std, away_std, match_time, confirmed}
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for row in soup.select(".lineup-row"):
        btn = row.select_one(".lineups-toggle-button")
        teams = row.select(".fxs-team")
        if not btn or len(teams) < 2:
            continue
        sg_id = (btn.get("id") or "").strip()
        if not sg_id:
            continue
        btn_classes  = " ".join(btn.get("class", []))
        is_confirmed = "green-button" in btn_classes
        if confirmed_only and not is_confirmed:
            continue
        home_team = teams[0].get_text(strip=True)
        away_team = teams[1].get_text(strip=True)
        time_tag  = row.select_one(".fxs-time")
        results.append({
            "sg_id":      sg_id,
            "home_team":  home_team,
            "away_team":  away_team,
            "home_std":   _std(home_team),
            "away_std":   _std(away_team),
            "match_time": time_tag.get_text(strip=True) if time_tag else "",
            "confirmed":  is_confirmed,
        })
    return results


# ── AJAX parser: formation per match ─────────────────────────────────────────

def _fetch_formations(ctx: APIRequestContext, sg_id: str) -> tuple[str, str]:
    """
    Call Sportsgambler's AJAX endpoint for one match.
    Returns (home_formation, away_formation).  Either may be "" if not yet available.

    Confirmed selector: span.lineups-toggle-formation  (appears once per team)
    """
    html = _get(ctx, f"{BASE_URL}{AJAX_PATH}", params={"id": sg_id})
    if not html:
        return "", ""
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.select("span.lineups-toggle-formation")
    home_form = tags[0].get_text(strip=True) if len(tags) >= 1 else ""
    away_form = tags[1].get_text(strip=True) if len(tags) >= 2 else ""
    # Validate — must match formation pattern
    if home_form and not FORMATION_RE.match(home_form):
        home_form = ""
    if away_form and not FORMATION_RE.match(away_form):
        away_form = ""
    return home_form, away_form


# ── per-league scraper ────────────────────────────────────────────────────────

def _scrape_league(
    league_key: str,
    label: str,
    url: str,
    fixture_lookup: dict,
    today: str,
    ctx: APIRequestContext,
) -> tuple[list[dict], list[dict]]:
    log.info("── %s  %s", label, url)
    html = _get(ctx, url)
    if html is None:
        log.error("%s: failed to fetch main page", league_key)
        return [], []

    # confirmed_only=False: also include "Predicted Lineups" (yellow button) so
    # we can link next-week fixtures to formations before lineups are confirmed.
    # History recording is still restricted to confirmed-only rows (see below).
    rows = _parse_lineup_rows(html, confirmed_only=False)
    confirmed_count = sum(1 for r in rows if r["confirmed"])
    log.info("%s: %d matches on page (%d confirmed, %d predicted)",
             league_key, len(rows), confirmed_count, len(rows) - confirmed_count)

    new_history: list[dict] = []
    predicted:   list[dict] = []
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    for row in rows:
        time.sleep(AJAX_DELAY_S)
        home_form, away_form = _fetch_formations(ctx, row["sg_id"])

        if not home_form and not away_form:
            log.debug("%s: %s vs %s — no formation available yet (sg_id=%s)",
                      league_key, row["home_team"], row["away_team"], row["sg_id"])
            continue

        log.debug("%s: %s %s vs %s %s",
                  league_key,
                  row["home_team"], home_form,
                  row["away_team"], away_form)

        match_date = today

        # Only confirmed lineups go into history (higher reliability).
        if row["confirmed"]:
            if home_form:
                new_history.append({
                    "scraped_date": today,
                    "team":         row["home_team"],
                    "team_std":     row["home_std"],
                    "league_key":   league_key,
                    "formation":    home_form,
                    "match_date":   match_date,
                })
            if away_form:
                new_history.append({
                    "scraped_date": today,
                    "team":         row["away_team"],
                    "team_std":     row["away_std"],
                    "league_key":   league_key,
                    "formation":    away_form,
                    "match_date":   match_date,
                })

        fixture = (fixture_lookup.get((row["home_std"], row["away_std"]))
                   or fixture_lookup.get((row["away_std"], row["home_std"])))
        if fixture and (home_form or away_form):
            predicted.append({
                "match_id":       fixture["match_id"],
                "league":         fixture.get("league", label),
                "match_date":     match_date,
                "home_team":      row["home_team"],
                "away_team":      row["away_team"],
                "home_formation": home_form,
                "away_formation": away_form,
                "scraped_at":     scraped_at,
            })

    log.info("%s: %d confirmed→history, %d linked to predictions",
             league_key,
             len(new_history) // 2,
             len(predicted))
    return new_history, predicted


# ── main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    today = date.today().isoformat()
    log.info("=== ingest_tactical_data — %s%s ===",
             today, "  [DRY RUN]" if dry_run else "")

    fixture_lookup = _build_fixture_lookup()
    log.info("Fixture lookup: %d upcoming matches", len(fixture_lookup))

    existing_history = _load_history()
    log.info("Existing history: %d rows", len(existing_history))

    all_new_history: list[dict] = []
    all_predicted:   list[dict] = []

    with sync_playwright() as playwright:
        ctx = playwright.request.new_context(extra_http_headers=HEADERS)
        try:
            for league in LEAGUES:
                time.sleep(LEAGUE_DELAY_S)
                new_hist, predicted = _scrape_league(
                    league["key"], league["label"], league["url"],
                    fixture_lookup, today, ctx,
                )
                all_new_history.extend(new_hist)
                all_predicted.extend(predicted)
        finally:
            ctx.dispose()

    merged_history = existing_history + all_new_history
    stats = _compute_formation_stats(merged_history)

    log.info(
        "Summary: %d predicted | %d new history | %d total history | %d stat rows",
        len(all_predicted), len(all_new_history), len(merged_history), len(stats),
    )

    if dry_run:
        log.info("Dry run — no files written.")
        _print_preview(all_predicted, stats, all_new_history)
        return

    _save_history(merged_history)
    _save_predicted(all_predicted)
    _save_stats(stats)
    log.info("Done.")


def _print_preview(
    predicted: list[dict],
    stats: list[dict],
    new_history: list[dict],
) -> None:
    print("\n── All scraped formations (this run) ──")
    seen_teams: set[str] = set()
    for r in new_history:
        key = r["team_std"]
        if key not in seen_teams:
            seen_teams.add(key)
            print(f"  {r['team']:<28} {r['formation']}  [{r['league_key']}]")
    if not new_history:
        print("  (none — lineups may not be confirmed yet for upcoming matches)")

    print("\n── Predicted formations for upcoming fixtures ──")
    for row in predicted:
        print(f"  [{row['league']}]  "
              f"{row['home_team']} ({row['home_formation']}) vs "
              f"{row['away_team']} ({row['away_formation']})")
    if not predicted:
        print("  (none — no overlap between scraped matches and final_predictions.json)")

    print("\n── Primary formations (recency-weighted) ──")
    primaries = [r for r in stats if r.get("is_primary")]
    for row in primaries[:20]:
        print(f"  {row['team']:<28} {row['formation']:<8}  {row['pct']:>5}%"
              f"  (n={row['raw_count']})")
    if not primaries:
        print("  (none)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest tactical formation data.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Scrape and compute but do not write any CSV files.",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
