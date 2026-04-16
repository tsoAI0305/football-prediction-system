import pandas as pd
from app.services.ml_service import MLService


def test_predict_from_dataframe_odds_fallback():
    svc = MLService(model_path='nonexistent_model.pkl')
    df = pd.DataFrame({
        'match_id': ['m1','m2'],
        'odds_home': [1.5, 2.0],
        'odds_draw': [3.5, 3.2],
        'odds_away': [6.0, 4.0]
    })
    out = svc.predict_from_dataframe(df)
    assert 'match_id' in out.columns
    assert out.shape[0] == 2
    # probabilities should sum close to 1
    s = out['predicted_home_win_prob'] + out['predicted_draw_prob'] + out['predicted_away_win_prob']
    assert all(abs(v - 1.0) < 0.01 for v in s)
