import pandas as pd
from app.services.feature_engineer import build_feature_matrix


def test_build_feature_matrix_injury_counts():
    fixtures = pd.DataFrame({
        'match_id': ['m1'],
        'date': ['2026-01-01'],
        'home_team': ['TeamA'],
        'away_team': ['TeamB']
    })
    fixtures['date'] = pd.to_datetime(fixtures['date'])
    injuries = pd.DataFrame({
        'team_std': ['TeamA','TeamA','TeamB'],
        'player_id': ['p1','p2','p3']
    })
    out = build_feature_matrix(fixtures, None, None, injuries)
    assert 'home_inj_count' in out.columns
    assert out.loc[0,'home_inj_count'] == 2
    assert out.loc[0,'away_inj_count'] == 1
