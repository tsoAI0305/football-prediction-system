from datetime import datetime, timedelta

from app.services.feature_engineer import (
    ELO_START,
    AsOfState,
    build_feature_matrix,
    implied_probs,
)


def _row(mid, day, home, away, hg, ag, league="PL", season="2425"):
    return {
        "match_id": mid,
        "match_date": datetime(2024, 8, 1) + timedelta(days=day),
        "league": league,
        "season": season,
        "home_team": home,
        "away_team": away,
        "home_std": home.lower(),
        "away_std": away.lower(),
        "home_score": hg,
        "away_score": ag,
        "home_shots": 10,
        "away_shots": 8,
        "b365_home": 2.0,
        "b365_draw": 3.2,
        "b365_away": 3.8,
    }


def test_implied_probs_normalize():
    ph, pd_, pa = implied_probs(2.0, 4.0, 4.0)
    assert abs(ph + pd_ + pa - 1.0) < 1e-9
    assert ph > pd_


def test_asof_form_does_not_use_future_result():
    finished = [
        _row(1, 0, "Alpha", "Beta", 2, 0),
        _row(2, 10, "Alpha", "Gamma", 1, 0),
    ]
    import pandas as pd

    fixtures = pd.DataFrame(
        [
            {
                "match_id": 1,
                "home_team": "Alpha",
                "away_team": "Beta",
                "league": "PL",
                "season": "2425",
                "match_date": finished[0]["match_date"],
                "result": "H",
            },
            {
                "match_id": 2,
                "home_team": "Alpha",
                "away_team": "Gamma",
                "league": "PL",
                "season": "2425",
                "match_date": finished[1]["match_date"],
                "result": "H",
            },
        ]
    )
    out = build_feature_matrix(fixtures, db=None, finished_rows=finished)
    # First match: no prior games → form stays prior 0.5
    assert abs(out.loc[0, "home_recent_form"] - 0.5) < 1e-6
    # Second match: Alpha already beat Beta → form 1.0, and must not include match 2
    assert out.loc[1, "home_recent_form"] == 1.0
    assert out.loc[1, "home_played"] == 1
    assert out.loc[1, "home_points"] == 3


def test_elo_moves_after_apply():
    state = AsOfState()
    before = state.elo["alpha"]
    state.apply(_row(1, 0, "Alpha", "Beta", 3, 0))
    assert state.elo["alpha"] > before
    assert state.elo["beta"] < ELO_START
