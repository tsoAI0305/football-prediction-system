"""
As-of feature engineering.

Standings, form, Elo, rest days, H2H and shot rates use only matches
strictly before each row's match_date. Latest standings/injury CSVs are
not used for training (they leak the present into the past).
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

ELO_START = 1500.0
ELO_HOME_ADV = 60.0
ELO_K = 20.0


def _std_name(name: str) -> str:
    try:
        from unidecode import unidecode
        name = unidecode(str(name))
    except ImportError:
        name = str(name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


def add_diff_features(df: pd.DataFrame) -> pd.DataFrame:
    if "home_rank" in df.columns and "away_rank" in df.columns:
        df["rank_diff"] = df["home_rank"] - df["away_rank"]
        df["points_diff"] = df["home_points"] - df["away_points"]
        df["gd_diff"] = df["home_goal_diff"] - df["away_goal_diff"]
    if "home_elo" in df.columns and "away_elo" in df.columns:
        df["elo_diff"] = df["home_elo"] - df["away_elo"]
    if "home_shots_pg" in df.columns and "away_shots_pg" in df.columns:
        df["shots_diff"] = df["home_shots_pg"] - df["away_shots_pg"]
    return df


def implied_probs(oh, od, oa) -> tuple[float, float, float]:
    try:
        ph = 1.0 / float(oh) if oh and float(oh) > 0 else 0.0
        pd_ = 1.0 / float(od) if od and float(od) > 0 else 0.0
        pa = 1.0 / float(oa) if oa and float(oa) > 0 else 0.0
    except (TypeError, ValueError):
        ph = pd_ = pa = 0.0
    total = ph + pd_ + pa
    if total <= 0:
        return 0.33, 0.34, 0.33
    return ph / total, pd_ / total, pa / total


@dataclass
class _TeamSeason:
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def gd(self) -> int:
        return self.gf - self.ga


@dataclass
class _TeamHist:
    results: list = field(default_factory=list)  # (date, win 0/1, is_home, shots, opp_std)


@dataclass
class AsOfState:
    elo: Dict[str, float] = field(default_factory=lambda: defaultdict(lambda: ELO_START))
    hist: Dict[str, _TeamHist] = field(default_factory=lambda: defaultdict(_TeamHist))
    season: Dict[tuple, _TeamSeason] = field(default_factory=lambda: defaultdict(_TeamSeason))

    def snapshot(self, home: str, away: str, league: str, season: str, when: datetime) -> dict:
        hs, as_ = _std_name(home), _std_name(away)
        home_st = self._standings(league, season, hs)
        away_st = self._standings(league, season, as_)
        hh, ha = self.hist[hs], self.hist[as_]
        rest_h = _rest_days(hh.results, when)
        rest_a = _rest_days(ha.results, when)
        h2h = [r for r in hh.results if r[4] == as_][-8:]
        impl = (0.33, 0.34, 0.33)
        return {
            "home_rank": home_st["rank"],
            "home_points": home_st["points"],
            "home_goal_diff": home_st["gd"],
            "home_wins": home_st["wins"],
            "home_draws": home_st["draws"],
            "home_losses": home_st["losses"],
            "home_played": home_st["played"],
            "home_goals_for": home_st["gf"],
            "home_goals_against": home_st["ga"],
            "away_rank": away_st["rank"],
            "away_points": away_st["points"],
            "away_goal_diff": away_st["gd"],
            "away_wins": away_st["wins"],
            "away_draws": away_st["draws"],
            "away_losses": away_st["losses"],
            "away_played": away_st["played"],
            "away_goals_for": away_st["gf"],
            "away_goals_against": away_st["ga"],
            "home_home_win_rate": _rate([r[1] for r in hh.results if r[2]][-10:]),
            "home_away_win_rate": _rate([r[1] for r in hh.results if not r[2]][-10:]),
            "home_recent_form": _rate([r[1] for r in hh.results[-5:]]),
            "away_home_win_rate": _rate([r[1] for r in ha.results if r[2]][-10:]),
            "away_away_win_rate": _rate([r[1] for r in ha.results if not r[2]][-10:]),
            "away_recent_form": _rate([r[1] for r in ha.results[-5:]]),
            "home_elo": self.elo[hs],
            "away_elo": self.elo[as_],
            "home_rest_days": rest_h,
            "away_rest_days": rest_a,
            "h2h_home_win_rate": _rate([r[1] for r in h2h]),
            "h2h_games": len(h2h),
            "home_shots_pg": _mean([r[3] for r in hh.results[-8:] if r[3] is not None]),
            "away_shots_pg": _mean([r[3] for r in ha.results[-8:] if r[3] is not None]),
            "implied_home": impl[0],
            "implied_draw": impl[1],
            "implied_away": impl[2],
        }

    def _standings(self, league: str, season: str, team_std: str) -> dict:
        table = {
            k[2]: v
            for k, v in self.season.items()
            if k[0] == league and k[1] == season
        }
        if team_std not in table:
            table[team_std] = _TeamSeason()
        ranked = sorted(
            table.items(),
            key=lambda kv: (kv[1].points, kv[1].gd, kv[1].gf),
            reverse=True,
        )
        rank = 1
        for i, (name, _) in enumerate(ranked, start=1):
            if name == team_std:
                rank = i
                break
        st = table[team_std]
        return {
            "rank": rank,
            "points": st.points,
            "gd": st.gd,
            "wins": st.wins,
            "draws": st.draws,
            "losses": st.losses,
            "played": st.played,
            "gf": st.gf,
            "ga": st.ga,
        }

    def apply(self, row: dict) -> None:
        hs, as_ = row["home_std"], row["away_std"]
        hg, ag = row["home_score"], row["away_score"]
        eh, ea = self.elo[hs], self.elo[as_]
        exp_h = 1.0 / (1.0 + 10 ** ((ea - (eh + ELO_HOME_ADV)) / 400.0))
        if hg > ag:
            actual, hw, aw = 1.0, 1, 0
        elif hg < ag:
            actual, hw, aw = 0.0, 0, 1
        else:
            actual, hw, aw = 0.5, 0, 0
        self.elo[hs] = eh + ELO_K * (actual - exp_h)
        self.elo[as_] = ea + ELO_K * ((1.0 - actual) - (1.0 - exp_h))

        key_h = (row["league"], row["season"], hs)
        key_a = (row["league"], row["season"], as_)
        sh, sa = self.season[key_h], self.season[key_a]
        sh.played += 1
        sa.played += 1
        sh.gf += hg
        sh.ga += ag
        sa.gf += ag
        sa.ga += hg
        if hw:
            sh.wins += 1
            sa.losses += 1
        elif aw:
            sa.wins += 1
            sh.losses += 1
        else:
            sh.draws += 1
            sa.draws += 1

        when = row["match_date"]
        self.hist[hs].results.append((when, hw, True, row.get("home_shots"), as_))
        self.hist[as_].results.append((when, aw, False, row.get("away_shots"), hs))


def _rate(values: List[int]) -> float:
    if not values:
        return 0.5
    return round(sum(values) / len(values), 3)


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _rest_days(results: list, when: datetime) -> float:
    if not results or when is None:
        return 7.0
    last = results[-1][0]
    if last is None:
        return 7.0
    days = (when - last).total_seconds() / 86400.0
    return float(min(30.0, max(1.0, days)))


def _finished_rows(db: Session) -> List[dict]:
    from app.models.match import Match, MatchStatus

    matches = (
        db.query(Match)
        .filter(
            Match.status == MatchStatus.FINISHED.value,
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
            Match.home_team.isnot(None),
            Match.away_team.isnot(None),
        )
        .order_by(Match.match_date.asc(), Match.id.asc())
        .all()
    )
    rows = []
    for m in matches:
        rows.append(
            {
                "match_id": m.id,
                "match_date": m.match_date,
                "league": m.league or "",
                "season": m.season or "",
                "home_team": m.home_team,
                "away_team": m.away_team,
                "home_std": _std_name(m.home_team),
                "away_std": _std_name(m.away_team),
                "home_score": int(m.home_score),
                "away_score": int(m.away_score),
                "home_shots": m.home_shots,
                "away_shots": m.away_shots,
                "b365_home": m.b365_home,
                "b365_draw": m.b365_draw,
                "b365_away": m.b365_away,
            }
        )
    return rows


def build_feature_matrix(
    fixtures_df: pd.DataFrame,
    db: Optional[Session] = None,
    options: Dict = None,
    finished_rows: Optional[Iterable[dict]] = None,
) -> pd.DataFrame:
    """
    fixtures_df needs home_team, away_team, and match_date (or date).
    Pass finished_rows in tests to avoid a live DB.
    """
    opts = options or {}
    df = fixtures_df.copy()
    if "home" in df.columns and "home_team" not in df.columns:
        df = df.rename(columns={"home": "home_team", "away": "away_team"})
    if "match_id" not in df.columns:
        df["match_id"] = df.index.astype(str)
    if "match_date" not in df.columns and "date" in df.columns:
        df["match_date"] = pd.to_datetime(df["date"])
    df["match_date"] = pd.to_datetime(df["match_date"], utc=False)
    df["home_std"] = df["home_team"].map(_std_name)
    df["away_std"] = df["away_team"].map(_std_name)

    history = list(finished_rows) if finished_rows is not None else (
        _finished_rows(db) if db is not None else []
    )
    history.sort(key=lambda r: (r["match_date"] or datetime.min, r.get("match_id") or 0))

    state = AsOfState()
    hi = 0
    work = df.reset_index(drop=True)
    order = list(work.sort_values(["match_date", "match_id"]).index)
    feat_by_pos: Dict[int, dict] = {}

    for pos in order:
        row = work.loc[pos]
        when = row["match_date"]
        if pd.isna(when):
            when = datetime.min
        else:
            when = pd.Timestamp(when).to_pydatetime()
            if getattr(when, "tzinfo", None):
                when = when.replace(tzinfo=None)

        while hi < len(history):
            past = history[hi]
            past_dt = past["match_date"]
            if past_dt is not None and getattr(past_dt, "tzinfo", None):
                past_dt = past_dt.replace(tzinfo=None)
            if past_dt is not None and past_dt < when:
                state.apply(past)
                hi += 1
                continue
            break

        snap = state.snapshot(
            str(row["home_team"]),
            str(row["away_team"]),
            str(row.get("league") or ""),
            str(row.get("season") or ""),
            when,
        )
        oh = row.get("b365_home") if "b365_home" in work.columns else None
        od = row.get("b365_draw") if "b365_draw" in work.columns else None
        oa = row.get("b365_away") if "b365_away" in work.columns else None
        if (oh is None or (isinstance(oh, float) and math.isnan(oh))) and history:
            mid = row["match_id"]
            for past in history:
                if str(past.get("match_id")) == str(mid):
                    oh, od, oa = past.get("b365_home"), past.get("b365_draw"), past.get("b365_away")
                    break
        snap["implied_home"], snap["implied_draw"], snap["implied_away"] = implied_probs(oh, od, oa)
        feat_by_pos[pos] = snap

    feat_df = pd.DataFrame([feat_by_pos[i] for i in range(len(work))])
    out = pd.concat([work.reset_index(drop=True), feat_df], axis=1)
    out = add_diff_features(out)

    # Keep unused CSV slots at 0 so old model files still load if needed.
    if opts.get("include_snapshot_csv"):
        pass
    for col in (
        "home_inj_count", "away_inj_count",
        "home_key_inj_impact", "away_key_inj_impact",
        "home_top3_goals", "home_top3_assists", "home_top3_avg_rating",
        "away_top3_goals", "away_top3_assists", "away_top3_avg_rating",
    ):
        if col not in out.columns:
            out[col] = 0

    numeric_cols = out.select_dtypes(include="number").columns
    out[numeric_cols] = out[numeric_cols].fillna(0)
    return out
