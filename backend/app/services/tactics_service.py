"""Tactical analysis engine.

Classifies a team's playing style from standings + match-stat DB data,
then builds a formation-aware lineup board for the frontend.

Style taxonomy is derived from:
  • Plakias et al. 2023 — "Identifying Soccer Teams' Styles of Play"
  • Alfian Hakim 2024  — "Analysing BIG5 League Playing Styles" (Sofascore data)

Ten raw dimensions are condensed into five consumer-facing labels:
  Possession-Based | High-Pressing | Direct Play | Low Block | Counter-Attack
A 'Balanced' fallback is used when no strong signal is detected.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# ── Style catalogue ────────────────────────────────────────────────────────────

STYLE_INFO: dict[str, dict] = {
    "Possession-Based": {
        "label_zh":     "傳控型",
        "emoji":        "🎯",
        "badge_class":  "bg-blue-600 text-white border border-blue-700",
        "description_zh": "注重持球傳遞，耐心組織進攻",
    },
    "High-Pressing": {
        "label_zh":     "高位逼搶",
        "emoji":        "⚡",
        "badge_class":  "bg-orange-500 text-white border border-orange-600",
        "description_zh": "積極向前施壓，快速奪回球權",
    },
    "Direct Play": {
        "label_zh":     "直接打法",
        "emoji":        "🚀",
        "badge_class":  "bg-emerald-600 text-white border border-emerald-700",
        "description_zh": "快速縱深推進，簡練高效",
    },
    "Low Block": {
        "label_zh":     "低位防守",
        "emoji":        "🛡️",
        "badge_class":  "bg-slate-600 text-white border border-slate-700",
        "description_zh": "鞏固後防陣型，伺機快速反擊",
    },
    "Counter-Attack": {
        "label_zh":     "快速反擊",
        "emoji":        "💨",
        "badge_class":  "bg-amber-500 text-white border border-amber-600",
        "description_zh": "防守反擊為主，利用空間快攻",
    },
    "Balanced": {
        "label_zh":     "均衡型",
        "emoji":        "⚖️",
        "badge_class":  "bg-purple-600 text-white border border-purple-700",
        "description_zh": "攻守均衡，戰術靈活多變",
    },
}

# ── Position slot priority map ────────────────────────────────────────────────
# Each slot type → (primary_positions, secondary_positions)
# Primary match: score += 10.0   (ideally suited for the slot)
# Secondary match: score += 5.0  (adjacent/acceptable)
# No match: raw rating only        (fallback within category bucket)
POSITION_SLOT_PRIORITY: dict[str, tuple[list[str], list[str]]] = {
    "FW":     (["ST", "CF", "SS", "ATT"],              ["RW", "LW", "WF"]),
    "ADV_MF": (["AM", "AMC", "AMR", "AML", "CAM"],     ["CM", "SS", "RW", "LW"]),
    "DEF_MF": (["DM", "DMC", "CDM"],                   ["CM", "LM", "RM"]),
    "DF":     (["CB"],                                  ["LB", "RB", "LWB", "RWB", "SW"]),
    "GK":     (["GK", "G", "POR", "GKP"],               []),
}

# Formation → primary style hint (based on research literature)
_FORMATION_STYLE_MAP: dict[str, str] = {
    "4-3-3":   "High-Pressing",
    "4-2-3-1": "Possession-Based",
    "4-1-2-3": "Possession-Based",
    "4-3-2-1": "Possession-Based",
    "3-4-3":   "High-Pressing",
    "3-4-2-1": "High-Pressing",
    "3-2-4-1": "High-Pressing",
    "4-4-2":   "Direct Play",
    "4-4-1-1": "Direct Play",
    "3-5-2":   "Counter-Attack",
    "3-5-1-1": "Counter-Attack",
    "5-3-2":   "Low Block",
    "5-4-1":   "Low Block",
    "4-5-1":   "Low Block",
    "4-1-4-1": "Balanced",
    "4-3-1-2": "Balanced",
    "3-3-2-2": "Balanced",
}


# ── CSV helpers ───────────────────────────────────────────────────────────────

def _latest_csv(pattern: str) -> Optional[Path]:
    files = sorted(
        glob.glob(str(DATA_DIR / pattern)),
        key=os.path.getmtime,
        reverse=True,
    )
    return Path(files[0]) if files else None


# ── Formation loader ──────────────────────────────────────────────────────────

def load_formation_data(team_std: str) -> dict:
    """Return primary + alternate formations from tactical_formation_stats.csv."""
    f = _latest_csv("tactical_formation_stats.csv")
    if f is None:
        return {"primary_formation": "4-2-3-1", "alternate_formations": []}
    try:
        from app.utils.helpers import std_team as _std_team
        df = pd.read_csv(f)
        # Exact match first; fall back to alias-normalised match so that
        # CSVs written with un-resolved names (e.g. "borussiadortmund")
        # still match queries for the canonical form ("dortmund").
        team_df = df[df["team_std"] == team_std]
        if team_df.empty:
            df["_std_norm"] = df["team_std"].map(_std_team)
            team_df = df[df["_std_norm"] == team_std]
        if team_df.empty:
            return {"primary_formation": "4-2-3-1", "alternate_formations": []}

        primary    = team_df[team_df["is_primary"] == 1]
        alternates = team_df[team_df["is_primary"] == 0]

        primary_formation = (
            str(primary.iloc[0]["formation"]) if not primary.empty else "4-2-3-1"
        )
        alt_list = alternates["formation"].tolist()
        return {
            "primary_formation":    primary_formation,
            "alternate_formations": [str(f) for f in alt_list],
        }
    except Exception:
        return {"primary_formation": "4-2-3-1", "alternate_formations": []}


# ── DB match-stat aggregator ──────────────────────────────────────────────────

def _compute_match_stats(team_name: str, db: Session) -> dict:
    """Average shots / fouls / corners per game from the last 20 finished matches."""
    try:
        from app.models.match import Match
        from sqlalchemy import or_

        matches = (
            db.query(Match)
            .filter(
                or_(Match.home_team == team_name, Match.away_team == team_name),
                Match.status == "FINISHED",
            )
            .order_by(Match.match_date.desc())
            .limit(20)
            .all()
        )

        shots, sot, fouls, corners = [], [], [], []
        for m in matches:
            is_home = (m.home_team == team_name)
            if is_home:
                if m.home_shots            is not None: shots.append(m.home_shots)
                if m.home_shots_on_target  is not None: sot.append(m.home_shots_on_target)
                if m.home_fouls            is not None: fouls.append(m.home_fouls)
                if m.home_corners          is not None: corners.append(m.home_corners)
            else:
                if m.away_shots            is not None: shots.append(m.away_shots)
                if m.away_shots_on_target  is not None: sot.append(m.away_shots_on_target)
                if m.away_fouls            is not None: fouls.append(m.away_fouls)
                if m.away_corners          is not None: corners.append(m.away_corners)

        def _avg(lst: list) -> Optional[float]:
            return round(sum(lst) / len(lst), 1) if lst else None

        return {
            "shots_pg":   _avg(shots),
            "sot_pg":     _avg(sot),
            "fouls_pg":   _avg(fouls),
            "corners_pg": _avg(corners),
            "db_matches": len(matches),
        }
    except Exception:
        return {
            "shots_pg": None, "sot_pg": None,
            "fouls_pg": None, "corners_pg": None,
            "db_matches": 0,
        }


# ── Style classifier ──────────────────────────────────────────────────────────

def _classify_style(metrics: dict, formation: str) -> list[str]:
    """Return 1–2 style labels using a weighted vote across all indicators.

    Weights are calibrated against typical top-5 league distributions as
    described in Plakias 2023 and the Sofascore playing-style analysis.
    """
    gfpg    = metrics.get("goals_for_pg",     0) or 0
    gapg    = metrics.get("goals_against_pg", 0) or 0
    wr      = metrics.get("win_rate",          0) or 0
    dr      = metrics.get("draw_rate",         0) or 0
    ppg     = metrics.get("points_pg",         0) or 0
    shots   = metrics.get("shots_pg")
    sot     = metrics.get("sot_pg")
    fouls   = metrics.get("fouls_pg")
    corners = metrics.get("corners_pg")

    form_hint = _FORMATION_STYLE_MAP.get(formation, "Balanced")
    scores: dict[str, float] = {s: 0.0 for s in STYLE_INFO}

    # ── Possession-Based ──────────────────────────────────────────────────────
    if gfpg  >= 1.8:  scores["Possession-Based"] += 2.5
    elif gfpg >= 1.5: scores["Possession-Based"] += 1.0
    if gapg  <= 1.0:  scores["Possession-Based"] += 2.0
    elif gapg <= 1.2: scores["Possession-Based"] += 0.8
    if wr    >= 55:   scores["Possession-Based"] += 2.0
    elif wr  >= 45:   scores["Possession-Based"] += 1.0
    if corners and corners >= 5.5: scores["Possession-Based"] += 1.5
    elif corners and corners >= 5.0: scores["Possession-Based"] += 0.5
    if ppg   >= 2.0:  scores["Possession-Based"] += 0.8
    if form_hint == "Possession-Based": scores["Possession-Based"] += 2.0

    # ── High-Pressing ─────────────────────────────────────────────────────────
    if fouls and fouls >= 13:  scores["High-Pressing"] += 2.5
    elif fouls and fouls >= 11: scores["High-Pressing"] += 1.0
    if sot  and sot  >= 5.5:  scores["High-Pressing"] += 2.5
    elif sot and sot >= 4.5:  scores["High-Pressing"] += 1.0
    if gfpg >= 1.6:           scores["High-Pressing"] += 1.0
    if wr   >= 45:            scores["High-Pressing"] += 0.8
    if form_hint == "High-Pressing": scores["High-Pressing"] += 2.0

    # ── Direct Play ───────────────────────────────────────────────────────────
    if shots and shots >= 14:   scores["Direct Play"] += 2.0
    elif shots and shots >= 12: scores["Direct Play"] += 1.0
    if corners and corners >= 5.5: scores["Direct Play"] += 0.8
    # low shot-accuracy ratio = direct/speculative shots (research: Directness formula)
    if shots and sot and shots > 0:
        acc = sot / shots
        if acc < 0.33:   scores["Direct Play"] += 1.5
        elif acc < 0.38: scores["Direct Play"] += 0.5
    if gfpg >= 1.5 and gapg >= 1.3: scores["Direct Play"] += 1.5
    if form_hint == "Direct Play": scores["Direct Play"] += 2.0

    # ── Low Block ─────────────────────────────────────────────────────────────
    if gapg  <= 1.0:  scores["Low Block"] += 2.0
    elif gapg <= 1.2: scores["Low Block"] += 0.8
    if gfpg  <= 1.0:  scores["Low Block"] += 2.5
    elif gfpg <= 1.2: scores["Low Block"] += 1.0
    if shots and shots <= 10: scores["Low Block"] += 1.5
    if dr    >= 30:   scores["Low Block"] += 1.0   # many draws = passive/defensive
    if form_hint == "Low Block": scores["Low Block"] += 2.0

    # ── Counter-Attack ────────────────────────────────────────────────────────
    if wr >= 35 and gfpg >= 1.2 and gapg >= 1.2:
        scores["Counter-Attack"] += 1.5
    if sot and sot >= 4 and corners and corners <= 4.5:
        scores["Counter-Attack"] += 2.0
    if shots and shots >= 11 and corners and corners <= 4.5:
        scores["Counter-Attack"] += 1.0
    if form_hint == "Counter-Attack": scores["Counter-Attack"] += 2.0

    # ── Balanced (base weight) ────────────────────────────────────────────────
    scores["Balanced"] += 1.5
    if form_hint == "Balanced": scores["Balanced"] += 1.5

    # Select top 1–2 styles with score ≥ 3.0; skip Balanced if anything else qualifies
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result = [s for s, v in top if s != "Balanced" and v >= 3.0][:2]
    return result if result else ["Balanced"]


# ── Evidence generator ────────────────────────────────────────────────────────

def _generate_evidence(metrics: dict) -> list[str]:
    """Up to 5 human-readable data bullets explaining the style classification."""
    ev: list[str] = []
    gfpg    = metrics.get("goals_for_pg",     0) or 0
    gapg    = metrics.get("goals_against_pg", 0) or 0
    wr      = metrics.get("win_rate",          0) or 0
    shots   = metrics.get("shots_pg")
    sot     = metrics.get("sot_pg")
    fouls   = metrics.get("fouls_pg")
    corners = metrics.get("corners_pg")

    # Attacking
    if gfpg >= 1.8:
        ev.append(f"場均進球 {gfpg:.1f} 個 → 高攻擊效率")
    elif gfpg >= 1.5:
        ev.append(f"場均進球 {gfpg:.1f} 個 → 攻擊穩健")
    elif gfpg <= 1.0:
        ev.append(f"場均進球僅 {gfpg:.1f} 個 → 保守進攻策略")

    # Defensive
    if gapg <= 1.0:
        ev.append(f"場均失球僅 {gapg:.1f} 個 → 防守體系鐵壁")
    elif gapg >= 1.5:
        ev.append(f"場均失球 {gapg:.1f} 個 → 後防線待強化")

    # Win rate
    if wr >= 55:
        ev.append(f"勝率 {wr:.0f}% → 聯賽頂級強隊")
    elif wr >= 40:
        ev.append(f"勝率 {wr:.0f}% → 聯賽中上水準")
    elif wr <= 25:
        ev.append(f"勝率 {wr:.0f}% → 聯賽下游球隊")

    # Shot volume
    if shots is not None:
        if shots >= 14:
            ev.append(f"場均射門 {shots:.1f} 次 → 積極主動進攻")
        elif shots <= 9:
            ev.append(f"場均射門僅 {shots:.1f} 次 → 謹慎保守進攻")

    # Pressing proxy (fouls)
    if fouls is not None:
        if fouls >= 13:
            ev.append(f"場均犯規 {fouls:.1f} 次 → 高位積極逼搶")
        elif fouls <= 9:
            ev.append(f"場均犯規 {fouls:.1f} 次 → 技術型控球")

    # Corner proxy (possession width)
    if corners is not None:
        if corners >= 6.0:
            ev.append(f"場均角球 {corners:.1f} 個 → 陣地進攻頻繁")
        elif corners <= 3.5:
            ev.append(f"場均角球僅 {corners:.1f} 個 → 快速直接打法")

    # Shot accuracy
    if sot is not None and shots and shots > 0:
        acc = round(sot / shots * 100)
        if acc >= 40:
            ev.append(f"射正率 {acc}% → 射門精準高效")
        elif acc <= 28:
            ev.append(f"射正率 {acc}% → 積極出腳但精度待提升")

    return ev[:5]


def _generate_dna(styles: list[str], metrics: dict) -> str:
    """One-sentence tactical DNA summary."""
    gfpg = metrics.get("goals_for_pg", 0) or 0
    gapg = metrics.get("goals_against_pg", 0) or 0

    descs = [STYLE_INFO[s]["description_zh"] for s in styles if s in STYLE_INFO]
    base  = "，".join(descs) if descs else "攻守均衡"

    if gfpg >= 1.8 and gapg <= 1.1:
        suffix = "整體實力強勁，是本賽季奪冠有力競爭者。"
    elif gfpg >= 1.6:
        suffix = "進攻端有強大破壞力。"
    elif gapg <= 1.0:
        suffix = "防守體系嚴密，極難攻破。"
    else:
        suffix = "在技戰術執行上有著清晰的體系。"

    return f"該隊以「{base}」為核心戰術理念，{suffix}"


# ── Formation-board builder ───────────────────────────────────────────────────

def _row_label(row_index: int, total_rows: int) -> str:
    """Map a row index (0 = top/attack, last = GK) to a Chinese position label."""
    if row_index == 0:
        return "前鋒"
    if row_index == total_rows - 1:
        return "門將"
    if row_index == total_rows - 2:
        return "後衛"
    n_mid = total_rows - 3   # number of middle rows
    if n_mid <= 1:
        return "中場"
    mid_idx = row_index - 1  # 0-based among middle rows
    return "前場中場" if mid_idx < (n_mid + 1) // 2 else "後場中場"


def _pos_category(player: dict) -> str:
    """Map a player dict to a broad position category: GK / DF / MF / FW.

    Checks `detailed_position` first (from full_squads_std.csv), then `position`
    (G/D/M/F broad codes from top-players CSV), then stats heuristic.
    """
    for field in ("detailed_position", "position"):
        pos = str(player.get(field, "") or "").upper().strip()
        if pos:
            if pos in ("G", "GK", "POR", "GKP"):
                return "GK"
            if pos in ("D", "DF", "CB", "LB", "RB", "LWB", "RWB", "SW"):
                return "DF"
            if pos in ("M", "MF", "CM", "DM", "AM", "AMC", "AMR", "AML",
                       "CAM", "CDM", "DMC", "LM", "RM"):
                return "MF"
            if pos in ("F", "FW", "ST", "SS", "LW", "RW", "CF", "WF", "ATT"):
                return "FW"

    # Heuristic when no position field is available
    goals   = int(player.get("goals",   0) or 0)
    assists = int(player.get("assists", 0) or 0)
    rating  = float(player.get("rating", 0) or 0)

    if goals >= 8:
        return "FW"
    if goals >= 4 and assists >= 2:
        return "FW"
    if assists >= 6 and goals <= 3:
        return "MF"
    if goals == 0 and assists == 0:
        return "GK" if rating >= 7.2 else "DF"
    if goals <= 1 and assists <= 2:
        return "DF"
    return "MF"


def _row_slot_type(row_i: int, total_rows: int) -> str:
    """Return a fine-grained slot type for a row, distinguishing ADV_MF from DEF_MF."""
    if row_i == 0:
        return "FW"
    if row_i == total_rows - 1:
        return "GK"
    if row_i == total_rows - 2:
        return "DF"
    n_mid = total_rows - 3
    mid_idx = row_i - 1   # 0-based among middle rows
    # Top half of midfield rows = advanced (closer to attack)
    return "ADV_MF" if mid_idx < (n_mid + 1) // 2 else "DEF_MF"


_BROAD_SLOT_MATCH: dict[str, set[str]] = {
    "FW":     {"F"},
    "ADV_MF": {"M"},
    "DEF_MF": {"M"},
    "DF":     {"D"},
    "GK":     {"G"},
}


def _slot_score(player: dict, slot_type: str) -> float:
    """Rate a player for a specific slot using detailed-position priority.

    Primary specific position (+10):  e.g. ST/CF in FW slot, CB in DF slot.
    Secondary specific position (+7): e.g. LB/RB in DF slot, RW/LW in FW slot.
    Broad category match (+5):        e.g. broad "F" in FW slot (SofaScore
        returns G/D/M/F when sub-positions are unavailable).
    No match: raw rating only (fallback when category bucket is exhausted).

    Score hierarchy: primary(+10) > secondary-specific(+7) > broad(+5) > raw.
    This ensures a player with a matching specific sub-position (e.g., Grimaldo
    as LB) always beats a vague broad-category player (e.g., "D") in that slot.
    """
    rating = float(player.get("rating", 0) or 0)
    dp = str(
        player.get("detailed_position") or player.get("position", "") or ""
    ).upper().strip()
    primary, secondary = POSITION_SLOT_PRIORITY.get(slot_type, ([], []))
    if dp in primary:
        return rating + 10.0
    if dp in secondary:
        return rating + 7.0   # specific sub-position beats broad category
    if dp in _BROAD_SLOT_MATCH.get(slot_type, set()):
        return rating + 5.0   # broad category is the last resort before raw
    return rating


def build_lineup_by_formation(lineup: list[dict], formation: str) -> dict:
    """Arrange players into formation rows using strict category + detailed-position weighting.

    Algorithm:
    1. Lock GK slot first (only GK-category players; empty slot rather than use outfield).
    2. Fill DF → FW → MF in priority order so positionally strict roles claim
       their bucket before flexible MF rows consume via fallback.
    3. Within each category bucket, players are scored by detailed-position match
       to the specific slot type (FW/ADV_MF/DEF_MF/DF/GK) before raw rating.
       Primary detailed-position match: +10 bonus; secondary: +5 bonus.
    4. Cross-zone promotion (e.g. DF filling a FW row) only occurs via the
       adjacency fallback when a category bucket is exhausted.

    Returns::

        {
            "formation": "4-2-3-1",
            "rows": [
                {"label": "前鋒",    "count": 1, "players": [...]},
                {"label": "前場中場","count": 3, "players": [...]},
                {"label": "後場中場","count": 2, "players": [...]},
                {"label": "後衛",    "count": 4, "players": [...]},
                {"label": "門將",    "count": 1, "players": [...]},
            ],
        }
    """
    try:
        outfield = [int(x) for x in formation.split("-") if x.isdigit()]
    except (ValueError, AttributeError):
        outfield = [4, 2, 3, 1]

    gk_count = max(1, 11 - sum(outfield))
    display_groups = list(reversed(outfield)) + [gk_count]
    total_rows = len(display_groups)

    # ── Bucket players by broad category ─────────────────────────────────────
    buckets: dict[str, list[dict]] = {"GK": [], "DF": [], "MF": [], "FW": []}
    for p in lineup:
        buckets[_pos_category(p)].append(p)
    for cat in buckets:
        buckets[cat].sort(key=lambda p: float(p.get("rating", 0) or 0), reverse=True)

    # GK: strict — no adjacency fallback (empty slot is better than misplaced DF)
    # MF: prefer FW over DF in fallback so defenders stay in defensive rows
    _FALLBACK_ORDER: dict[str, list[str]] = {
        "GK": ["GK"],
        "DF": ["DF", "MF", "FW", "GK"],
        "MF": ["MF", "FW", "DF", "GK"],
        "FW": ["FW", "MF", "DF", "GK"],
    }

    def _row_cat(row_i: int) -> str:
        if row_i == 0:             return "FW"
        if row_i == total_rows - 1: return "GK"
        if row_i == total_rows - 2: return "DF"
        return "MF"

    used: set[str] = set()

    def _pick(cat: str, slot_type: str, count: int) -> list[dict]:
        """Pick `count` players for a slot using category fallback + position scoring."""
        picked: list[dict] = []
        for try_cat in _FALLBACK_ORDER[cat]:
            available = [
                p for p in buckets[try_cat]
                if p.get("player_name", "") not in used
            ]
            if not available:
                continue
            # Sub-sort by slot-specific detailed-position score
            available.sort(key=lambda p: _slot_score(p, slot_type), reverse=True)
            for p in available:
                if len(picked) >= count:
                    break
                name = p.get("player_name", "")
                if name not in used:
                    picked.append(p)
                    used.add(name)
            if len(picked) >= count:
                break
        return picked

    # Fill in priority order: GK → DF → FW → MF
    _FILL_PRIORITY = ["GK", "DF", "FW", "MF"]
    row_specs = [
        (row_i, count, _row_cat(row_i), _row_slot_type(row_i, total_rows))
        for row_i, count in enumerate(display_groups)
    ]
    row_specs_priority = sorted(row_specs, key=lambda x: _FILL_PRIORITY.index(x[2]))

    row_results: dict[int, list[dict]] = {}
    for row_i, count, cat, slot_type in row_specs_priority:
        row_results[row_i] = _pick(cat, slot_type, count)

    rows: list[dict] = []
    for row_i, count in enumerate(display_groups):
        rows.append({
            "label":   _row_label(row_i, total_rows),
            "count":   count,
            "players": row_results[row_i],
        })

    return {"formation": formation, "rows": rows}


# ── Public API ────────────────────────────────────────────────────────────────

_DEFAULT_PROFILE: dict = {
    "style_labels":         ["Balanced"],
    "style_info":           [{
        "key":         "Balanced",
        "label_zh":    "數據計算中",
        "emoji":       "⏳",
        "badge_class": "bg-gray-100 text-gray-600 border border-gray-300",
    }],
    "formation":            "4-2-3-1",
    "alternate_formations": [],
    "metrics":              {},
    "style_evidence":       [],
    "tactical_dna":         "戰術數據計算中，請稍後查看。",
    "status":               "calculating",
}


def compute_tactical_profile(
    team_std: str,
    team_name: str,
    standings: dict,
    db: Session,
) -> dict:
    """Compute a team's full tactical profile.

    Returns a default 'calculating' profile if any step fails so the
    API never raises a 500 error.

    Returns
    -------
    dict with keys:
        style_labels, style_info, formation, alternate_formations,
        metrics, style_evidence, tactical_dna
    """
    try:
        # 1. Formation (already has internal try-except)
        form_data = load_formation_data(team_std)
        formation = form_data["primary_formation"]
    except Exception:
        form_data = {"primary_formation": "4-2-3-1", "alternate_formations": []}
        formation = "4-2-3-1"

    try:
        # 2. DB match stats (shots / fouls / corners)
        db_stats = _compute_match_stats(team_name, db)
    except Exception:
        db_stats = {
            "shots_pg": None, "sot_pg": None,
            "fouls_pg": None, "corners_pg": None,
            "db_matches": 0,
        }

    try:
        # 3. Derived metrics
        played = max(standings.get("played", 1) or 1, 1)
        metrics: dict = {
            "goals_for_pg":     round((standings.get("goals_for",     0) or 0) / played, 2),
            "goals_against_pg": round((standings.get("goals_against", 0) or 0) / played, 2),
            "win_rate":         round((standings.get("wins",  0) or 0) / played * 100, 1),
            "draw_rate":        round((standings.get("draws", 0) or 0) / played * 100, 1),
            "points_pg":        round((standings.get("points", 0) or 0) / played, 2),
            **db_stats,
        }
    except Exception:
        metrics = {**db_stats}

    try:
        # 4. Classification + evidence + DNA
        styles   = _classify_style(metrics, formation)
        evidence = _generate_evidence(metrics)
        dna      = _generate_dna(styles, metrics)
    except Exception:
        styles   = ["Balanced"]
        evidence = []
        dna      = "戰術數據計算中，請稍後查看。"

    try:
        # 5. Frontend-ready style_info list
        style_info_list = [
            {
                "key":         s,
                "label_zh":    STYLE_INFO[s]["label_zh"],
                "emoji":       STYLE_INFO[s]["emoji"],
                "badge_class": STYLE_INFO[s]["badge_class"],
            }
            for s in styles
            if s in STYLE_INFO
        ]
    except Exception:
        style_info_list = []

    return {
        "style_labels":         styles,
        "style_info":           style_info_list,
        "formation":            formation,
        "alternate_formations": form_data["alternate_formations"],
        "metrics":              metrics,
        "style_evidence":       evidence,
        "tactical_dna":         dna,
    }
