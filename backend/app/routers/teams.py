"""Teams API endpoint — aggregates standings, DB stats, injuries, players, and
tactical profile from CSV files and the match database."""
import glob
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.helpers import std_team, std_player
from app.services.tactics_service import (
    compute_tactical_profile,
    build_lineup_by_formation,
)

router = APIRouter(tags=["Teams"])
logger = logging.getLogger(__name__)

DATA_DIR         = Path(__file__).resolve().parents[2] / "data"
PREDICTIONS_FILE = Path(__file__).resolve().parents[2] / "data" / "final_predictions.json"


# ── legacy helpers (kept for backward-compat with internal callers) ────────────

def _std(name: str) -> str:
    """Basic normalisation — use std_team() for cross-CSV lookups."""
    try:
        from unidecode import unidecode
        name = unidecode(str(name))
    except ImportError:
        name = str(name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _latest_csv(pattern: str) -> Optional[Path]:
    files = sorted(glob.glob(str(DATA_DIR / pattern)), key=os.path.getmtime, reverse=True)
    return Path(files[0]) if files else None


def _safe_float(v, default: float = 0.0) -> float:
    try:
        f = float(v)
        return round(f, 2) if f == f else default
    except (TypeError, ValueError):
        return default


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _inj_matches(query_std: str, row_std: str, row_team: str) -> bool:
    """Return True when an injury row belongs to the queried team.

    Both sides are passed through std_team() so that alias variants resolve
    to the same canonical key before comparison.
    """
    rs = std_team(str(row_std))
    rt = std_team(str(row_team))
    if query_std in (rs, rt):
        return True
    # substring safety net (handles e.g. "dortmund" ⊂ "borussiadortmund")
    for short, long in [(rs, query_std), (rt, query_std),
                        (query_std, rs), (query_std, rt)]:
        if len(short) >= 5 and short in long:
            return True
    return False


# ── data loaders ──────────────────────────────────────────────────────────────

def _load_standings(team_std: str) -> dict:
    try:
        f = _latest_csv("top5_standings_latest.csv") or _latest_csv("top5_standings_*.csv")
        if f is None:
            return {}
        df = pd.read_csv(f)
        # Use std_team on the CSV's team column so alias variants match
        df["_std"] = df["team"].map(std_team)
        row = df[df["_std"] == team_std]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            "league":        str(r.get("league", "")),
            "rank":          _safe_int(r.get("rank")),
            "points":        _safe_int(r.get("points")),
            "wins":          _safe_int(r.get("wins")),
            "draws":         _safe_int(r.get("draws")),
            "losses":        _safe_int(r.get("losses")),
            "goals_for":     _safe_int(r.get("goals_for")),
            "goals_against": _safe_int(r.get("goals_against")),
            "goal_diff":     _safe_int(r.get("goal_diff")),
            "played":        _safe_int(r.get("played")),
            "total_teams":   len(df[df["league"] == str(r.get("league", ""))]),
        }
    except Exception as exc:
        logger.warning("_load_standings failed for '%s': %s", team_std, exc)
        return {}


def _load_injuries(team_std: str) -> list:
    injuries = []
    for f in DATA_DIR.glob("*_teams_injuries_sportsgambler.csv"):
        try:
            df = pd.read_csv(f)
            if "player" not in df.columns:
                continue
            for _, row in df.iterrows():
                player = str(row.get("player", "")).strip()
                if not player or player in ("", "Name"):
                    continue
                row_std  = str(row.get("team_std", ""))
                row_team = str(row.get("team", ""))
                if _inj_matches(team_std, row_std, row_team):
                    injuries.append({
                        "player":          player,
                        "position":        str(row.get("position", "")).strip(),
                        "info":            str(row.get("info", "")).strip(),
                        "expected_return": str(row.get("expected_return", "")).strip(),
                    })
        except Exception:
            pass
    return injuries


def _load_top_players(team_std: str, injured_names: set | None = None) -> list:
    injured_names = injured_names or set()
    top = []
    seen: set[tuple] = set()
    for f in DATA_DIR.glob("*_team_top_players_sofascore_std.csv"):
        try:
            df = pd.read_csv(f)
            if "team_std" not in df.columns:
                continue
            df["_std"] = df["team_std"].map(std_team)
            team_df = df[df["_std"] == team_std]
            if team_df.empty:
                continue
            for stat in ("rating", "goals", "assists"):
                sub = team_df[team_df["stat_type"] == stat].sort_values("rank")
                sub = sub[~sub["player_name"].map(lambda n: std_player(str(n)) in injured_names)]
                sub = sub.head(1)
                for _, row in sub.iterrows():
                    name = str(row.get("player_name", "")).strip()
                    if not name:
                        continue
                    key = (name, stat)
                    if key in seen:
                        continue
                    seen.add(key)
                    top.append({
                        "player_name": name,
                        "stat_type":   stat,
                        "goals":       _safe_int(row.get("goals")),
                        "assists":     _safe_int(row.get("assists")),
                        "rating":      _safe_float(row.get("rating")),
                        "position":    str(row.get("position", "") or "").upper().strip(),
                    })
        except Exception:
            pass
    return top


def _build_projected_lineup(team_std: str, injured_names: set) -> list:
    """Available players for lineup building (injured excluded).

    Reads full_squads_std.csv first (has detailed_position); falls back to
    *_team_top_players_sofascore_std.csv. Returns all healthy players so that
    build_lineup_by_formation() can pick the optimal 11 using slot-priority scoring.
    """
    players: dict[str, dict] = {}

    # ── Primary: full squad CSV with detailed positions ───────────────────────
    full_squad_csv = _latest_csv("full_squads_std.csv")
    if full_squad_csv:
        try:
            df = pd.read_csv(full_squad_csv)
            if "team_std" in df.columns:
                df["_std"] = df["team_std"].map(std_team)
                team_df = df[df["_std"] == team_std]
                for _, row in team_df.iterrows():
                    name = str(row.get("player_name", "")).strip()
                    if not name or std_player(name) in injured_names:
                        continue
                    if row.get("is_injured", 0):
                        continue
                    rating = _safe_float(row.get("rating"))
                    if name not in players or rating > players[name]["rating"]:
                        players[name] = {
                            "player_name":      name,
                            "goals":            _safe_int(row.get("goals")),
                            "assists":          _safe_int(row.get("assists")),
                            "rating":           rating,
                            "position":         str(row.get("position_category", "") or "").upper().strip(),
                            "detailed_position": str(row.get("detailed_position", "") or "").upper().strip(),
                        }
        except Exception:
            pass

    # ── Fallback: top-players CSV (broad G/D/M/F positions only) ─────────────
    if not players:
        for f in DATA_DIR.glob("*_team_top_players_sofascore_std.csv"):
            try:
                df = pd.read_csv(f)
                if "team_std" not in df.columns:
                    continue
                df["_std"] = df["team_std"].map(std_team)
                team_df = df[df["_std"] == team_std]
                if team_df.empty:
                    continue
                for _, row in team_df.iterrows():
                    name = str(row.get("player_name", "")).strip()
                    if not name or std_player(name) in injured_names:
                        continue
                    rating = _safe_float(row.get("rating"))
                    position = str(row.get("position", "") or "").upper().strip()
                    if name not in players or rating > players[name]["rating"]:
                        players[name] = {
                            "player_name":      name,
                            "goals":            _safe_int(row.get("goals")),
                            "assists":          _safe_int(row.get("assists")),
                            "rating":           rating,
                            "position":         position,
                            "detailed_position": "",
                        }
            except Exception:
                pass

    return sorted(players.values(), key=lambda p: p["rating"], reverse=True)


def _db_stats_empty() -> dict:
    return {
        "recent_form":    "",
        "home_win_rate":  0.0,
        "away_win_rate":  0.0,
        "avg_goals":      0.0,
        "upcoming_matches": 0,
    }


def _compute_db_stats(team_name: str, db: Session) -> dict:
    """Recent form string and win-rate stats from DB finished matches.

    Returns empty defaults when the database is unavailable (e.g. PostgreSQL
    is not running in the current environment).
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        from app.models.match import Match
        from sqlalchemy import or_

        home_q = (
            db.query(Match)
            .filter(Match.home_team == team_name, Match.status == "FINISHED",
                    Match.home_score.isnot(None), Match.away_score.isnot(None))
            .order_by(Match.match_date.desc())
            .limit(15).all()
        )
        away_q = (
            db.query(Match)
            .filter(Match.away_team == team_name, Match.status == "FINISHED",
                    Match.home_score.isnot(None), Match.away_score.isnot(None))
            .order_by(Match.match_date.desc())
            .limit(15).all()
        )

        events: list[tuple] = []
        for m in home_q:
            r = "W" if m.home_score > m.away_score else ("D" if m.home_score == m.away_score else "L")
            events.append((m.match_date, r, m.home_score or 0))
        for m in away_q:
            r = "W" if m.away_score > m.home_score else ("D" if m.away_score == m.home_score else "L")
            events.append((m.match_date, r, m.away_score or 0))

        events.sort(key=lambda x: x[0], reverse=True)
        last6 = events[:6]
        recent_form = "".join(r for _, r, _ in reversed(last6))

        home_wins     = sum(1 for m in home_q if m.home_score > m.away_score)
        home_win_rate = round(home_wins / len(home_q) * 100, 1) if home_q else 0.0

        away_wins     = sum(1 for m in away_q if m.away_score > m.home_score)
        away_win_rate = round(away_wins / len(away_q) * 100, 1) if away_q else 0.0

        home_scored = sum(m.home_score or 0 for m in home_q)
        away_scored = sum(m.away_score or 0 for m in away_q)
        total_games = len(home_q) + len(away_q)
        avg_goals   = round((home_scored + away_scored) / total_games, 2) if total_games else 0.0

        upcoming = (
            db.query(Match)
            .filter(
                or_(Match.home_team == team_name, Match.away_team == team_name),
                Match.status == "SCHEDULED",
            )
            .count()
        )

        return {
            "recent_form":    recent_form,
            "home_win_rate":  home_win_rate,
            "away_win_rate":  away_win_rate,
            "avg_goals":      avg_goals,
            "upcoming_matches": upcoming,
        }

    except Exception as exc:
        # DB is unavailable (PostgreSQL not running, wrong credentials, etc.)
        # Log once at WARNING level — no traceback, no 500.
        log.warning("DB unavailable for team '%s', returning empty stats: %s", team_name, exc)
        return _db_stats_empty()


def _find_league_from_predictions(team_std: str) -> Optional[str]:
    try:
        if not PREDICTIONS_FILE.exists():
            return None
        with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
            preds = json.load(f)
        match = next(
            (p for p in preds
             if std_team(p.get("home_team", "")) == team_std
             or std_team(p.get("away_team", "")) == team_std),
            None,
        )
        return match["league"] if match else None
    except Exception as exc:
        logger.warning("_find_league_from_predictions failed for '%s': %s", team_std, exc)
        return None


# ── endpoint ──────────────────────────────────────────────────────────────────

@router.get("/{team_name}")
async def get_team_details(team_name: str, db: Session = Depends(get_db)):
    """Return rich team profile: standings, form, injuries, players,
    tactical DNA, and a formation-aware lineup board."""

    # std_team() resolves aliases so "Man Utd" → "manunited", etc.
    team_std = std_team(team_name)

    # 1. Standings
    standings = _load_standings(team_std)
    league = standings.get("league") or _find_league_from_predictions(team_std)
    if not league:
        raise HTTPException(status_code=404, detail=f"找不到球隊: {team_name}")

    # 2. DB stats (form, win rates, avg goals, upcoming)
    db_stats = _compute_db_stats(team_name, db)

    # 3. Injuries (must be ready before player selection)
    injuries = _load_injuries(team_std)
    injured_names = {std_player(inj["player"]) for inj in injuries}

    # 4. Top players and projected lineup
    top_players = _load_top_players(team_std, injured_names)
    lineup      = _build_projected_lineup(team_std, injured_names)

    # 5. Tactical profile + formation board
    try:
        tactical_profile = compute_tactical_profile(
            team_std=team_std,
            team_name=team_name,
            standings=standings,
            db=db,
        )
        formation           = tactical_profile.get("formation", "4-2-3-1")
        lineup_by_formation = build_lineup_by_formation(lineup, formation)
    except Exception as exc:
        logger.warning("tactical profile failed for '%s': %s", team_name, exc)
        tactical_profile = {
            "style_labels":         [],
            "style_info":           [],
            "formation":            "4-2-3-1",
            "alternate_formations": [],
            "metrics":              {},
            "style_evidence":       [],
            "tactical_dna":         "",
            "status":               "Calculating",
        }
        try:
            lineup_by_formation = build_lineup_by_formation(lineup, "4-2-3-1")
        except Exception:
            lineup_by_formation = None

    # 6. Composite ranking scores (0–100 scale)
    rank        = standings.get("rank", 0)
    total_teams = standings.get("total_teams", 20)
    rank_score  = round((total_teams - rank + 1) / total_teams * 100, 1) if rank else 0.0
    home_score  = round(db_stats["home_win_rate"], 1)
    away_score  = round(db_stats["away_win_rate"], 1)
    total_score = round(rank_score * 0.6 + home_score * 0.25 + away_score * 0.15, 1)

    return {
        # identity
        "team_name": team_name,
        "league":    league,
        # standings
        "rank":          standings.get("rank", 0),
        "points":        standings.get("points", 0),
        "wins":          standings.get("wins", 0),
        "draws":         standings.get("draws", 0),
        "losses":        standings.get("losses", 0),
        "goals_for":     standings.get("goals_for", 0),
        "goals_against": standings.get("goals_against", 0),
        "goal_diff":     standings.get("goal_diff", 0),
        "played":        standings.get("played", 0),
        # form & rates
        "recent_form":    db_stats["recent_form"],
        "home_win_rate":  db_stats["home_win_rate"],
        "away_win_rate":  db_stats["away_win_rate"],
        "avg_goals":      db_stats["avg_goals"],
        # composite scores
        "total_score":     total_score,
        "home_score":      home_score,
        "away_score":      away_score,
        "overall_ranking": rank,
        "total_teams":     total_teams,
        "upcoming_matches": db_stats["upcoming_matches"],
        # enriched player data
        "injuries":    injuries,
        "top_players": top_players,
        "lineup":      lineup,
        # ── Phase 3 additions ──────────────────────────────────────────────
        "tactical_profile":    tactical_profile,
        "lineup_by_formation": lineup_by_formation,
    }
