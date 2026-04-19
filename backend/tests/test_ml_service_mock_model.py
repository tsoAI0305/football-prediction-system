import numpy as np
import pandas as pd
from app.services.ml_service import MLService

class DummyModel:
    def predict_proba(self, X):
        n = X.shape[0]
        return np.tile(np.array([0.6,0.3,0.1]), (n,1))


def test_predict_with_mock_model():
    svc = MLService(model_path='nonexist.pkl')
    svc.model = DummyModel()
    df = pd.DataFrame({
        'match_id':['m1','m2'],
        'feature1':[1.0,2.0],
        'odds_home':[2.0,1.5],
        'odds_draw':[3.0,3.5],
        'odds_away':[4.0,6.0]
    })
    out = svc.predict_from_dataframe(df, model_name='dummy-v1')
    assert out['model_version'].iloc[0] == 'dummy-v1'
    assert abs(out['predicted_home_win_prob'].iloc[0] - 0.6) < 1e-6
