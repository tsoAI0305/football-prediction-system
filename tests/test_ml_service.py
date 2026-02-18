from app.services.ml_predictor import MLPredictionService


def test_ml_predictor_initialization():
    """Test ML predictor service initialization"""
    ml_service = MLPredictionService()
    assert ml_service is not None
    assert ml_service.is_trained is False


def test_heuristic_prediction():
    """Test heuristic prediction when models are not trained"""
    ml_service = MLPredictionService()
    
    home_stats = {
        'wins': 15,
        'draws': 3,
        'losses': 2,
        'goals_for': 48,
        'goals_against': 18,
        'points': 48,
        'games_played': 20
    }
    
    away_stats = {
        'wins': 10,
        'draws': 5,
        'losses': 5,
        'goals_for': 35,
        'goals_against': 25,
        'points': 35,
        'games_played': 20
    }
    
    home_win, draw, away_win, features = ml_service.predict_match_outcome(
        home_stats, away_stats
    )
    
    # Check probabilities sum to 1
    total_prob = home_win + draw + away_win
    assert abs(total_prob - 1.0) < 0.01
    
    # Check all probabilities are between 0 and 1
    assert 0 <= home_win <= 1
    assert 0 <= draw <= 1
    assert 0 <= away_win <= 1
    
    # Home team should have higher probability given better stats
    assert home_win > away_win


def test_score_prediction():
    """Test score prediction"""
    ml_service = MLPredictionService()
    
    home_stats = {
        'goals_for': 48,
        'goals_against': 18,
        'games_played': 20
    }
    
    away_stats = {
        'goals_for': 35,
        'goals_against': 25,
        'games_played': 20
    }
    
    home_score, away_score = ml_service.predict_score(home_stats, away_stats)
    
    # Check scores are positive
    assert home_score >= 0
    assert away_score >= 0
    
    # Check scores are reasonable (typically 0-5 goals per game)
    assert home_score <= 10
    assert away_score <= 10


def test_extract_features():
    """Test feature extraction"""
    ml_service = MLPredictionService()
    
    home_stats = {
        'wins': 15,
        'draws': 3,
        'losses': 2,
        'goals_for': 48,
        'goals_against': 18,
        'points': 48,
        'games_played': 20
    }
    
    away_stats = {
        'wins': 10,
        'draws': 5,
        'losses': 5,
        'goals_for': 35,
        'goals_against': 25,
        'points': 35,
        'games_played': 20
    }
    
    features = ml_service.extract_features(home_stats, away_stats)
    
    # Check feature array shape
    assert features.shape == (1, 12)
    
    # Check all features are numeric
    assert all(isinstance(f, (int, float)) for f in features[0])
