import numpy as np
from typing import Dict, Tuple, Optional
import xgboost as xgb
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
import os
import pickle


class MLPredictionService:
    """
    ML Prediction Service using XGBoost and LightGBM for football match predictions
    """
    
    def __init__(self):
        self.xgb_model = None
        self.lgb_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def load_models(self, xgb_path: Optional[str] = None, lgb_path: Optional[str] = None):
        """Load pre-trained models from disk"""
        try:
            if xgb_path and os.path.exists(xgb_path):
                self.xgb_model = xgb.Booster()
                self.xgb_model.load_model(xgb_path)
            
            if lgb_path and os.path.exists(lgb_path):
                self.lgb_model = lgb.Booster(model_file=lgb_path)
            
            self.is_trained = True
        except Exception as e:
            print(f"Error loading models: {e}")
            self.is_trained = False
    
    def extract_features(self, home_team_stats: Dict, away_team_stats: Dict) -> np.ndarray:
        """
        Extract features from team statistics for prediction
        
        Args:
            home_team_stats: Dictionary with home team statistics
            away_team_stats: Dictionary with away team statistics
        
        Returns:
            Feature array for prediction
        """
        features = []
        
        # Home team features
        home_goals_per_game = home_team_stats.get('goals_for', 0) / max(home_team_stats.get('games_played', 1), 1)
        home_goals_against_per_game = home_team_stats.get('goals_against', 0) / max(home_team_stats.get('games_played', 1), 1)
        home_win_rate = home_team_stats.get('wins', 0) / max(home_team_stats.get('games_played', 1), 1)
        home_points_per_game = home_team_stats.get('points', 0) / max(home_team_stats.get('games_played', 1), 1)
        
        # Away team features
        away_goals_per_game = away_team_stats.get('goals_for', 0) / max(away_team_stats.get('games_played', 1), 1)
        away_goals_against_per_game = away_team_stats.get('goals_against', 0) / max(away_team_stats.get('games_played', 1), 1)
        away_win_rate = away_team_stats.get('wins', 0) / max(away_team_stats.get('games_played', 1), 1)
        away_points_per_game = away_team_stats.get('points', 0) / max(away_team_stats.get('games_played', 1), 1)
        
        # Relative features
        goals_diff = home_goals_per_game - away_goals_per_game
        defensive_diff = away_goals_against_per_game - home_goals_against_per_game
        form_diff = home_win_rate - away_win_rate
        points_diff = home_points_per_game - away_points_per_game
        
        features = [
            home_goals_per_game, home_goals_against_per_game, home_win_rate, home_points_per_game,
            away_goals_per_game, away_goals_against_per_game, away_win_rate, away_points_per_game,
            goals_diff, defensive_diff, form_diff, points_diff
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict_match_outcome(
        self,
        home_team_stats: Dict,
        away_team_stats: Dict,
        use_ensemble: bool = True
    ) -> Tuple[float, float, float, Dict]:
        """
        Predict match outcome probabilities
        
        Args:
            home_team_stats: Home team statistics
            away_team_stats: Away team statistics
            use_ensemble: Use ensemble of both models if True
        
        Returns:
            Tuple of (home_win_prob, draw_prob, away_win_prob, features_dict)
        """
        features = self.extract_features(home_team_stats, away_team_stats)
        
        # If models are not trained, use a simple heuristic
        if not self.is_trained:
            return self._heuristic_prediction(home_team_stats, away_team_stats)
        
        # XGBoost prediction
        xgb_probs = self._predict_xgboost(features) if self.xgb_model else None
        
        # LightGBM prediction
        lgb_probs = self._predict_lightgbm(features) if self.lgb_model else None
        
        # Ensemble prediction
        if use_ensemble and xgb_probs is not None and lgb_probs is not None:
            home_win = (xgb_probs[0] + lgb_probs[0]) / 2
            draw = (xgb_probs[1] + lgb_probs[1]) / 2
            away_win = (xgb_probs[2] + lgb_probs[2]) / 2
        elif xgb_probs is not None:
            home_win, draw, away_win = xgb_probs
        elif lgb_probs is not None:
            home_win, draw, away_win = lgb_probs
        else:
            return self._heuristic_prediction(home_team_stats, away_team_stats)
        
        # Create features dictionary for transparency
        features_dict = {
            'home_goals_per_game': float(features[0][0]),
            'away_goals_per_game': float(features[0][4]),
            'home_win_rate': float(features[0][2]),
            'away_win_rate': float(features[0][6]),
            'points_difference': float(features[0][11])
        }
        
        return home_win, draw, away_win, features_dict
    
    def _predict_xgboost(self, features: np.ndarray) -> Tuple[float, float, float]:
        """Predict using XGBoost model"""
        # Placeholder - would use actual trained model
        dmatrix = xgb.DMatrix(features)
        pred = self.xgb_model.predict(dmatrix)
        
        # Assuming 3-class output (home, draw, away)
        if len(pred.shape) == 1:
            pred = pred.reshape(-1, 3)
        
        return float(pred[0][0]), float(pred[0][1]), float(pred[0][2])
    
    def _predict_lightgbm(self, features: np.ndarray) -> Tuple[float, float, float]:
        """Predict using LightGBM model"""
        # Placeholder - would use actual trained model
        pred = self.lgb_model.predict(features)
        
        # Assuming 3-class output (home, draw, away)
        if len(pred.shape) == 1:
            pred = pred.reshape(-1, 3)
        
        return float(pred[0][0]), float(pred[0][1]), float(pred[0][2])
    
    def _heuristic_prediction(
        self,
        home_team_stats: Dict,
        away_team_stats: Dict
    ) -> Tuple[float, float, float, Dict]:
        """
        Simple heuristic prediction based on team statistics
        Used when ML models are not available
        """
        # Calculate basic metrics
        home_games = max(home_team_stats.get('games_played', 1), 1)
        away_games = max(away_team_stats.get('games_played', 1), 1)
        
        home_points_per_game = home_team_stats.get('points', 0) / home_games
        away_points_per_game = away_team_stats.get('points', 0) / away_games
        
        # Home advantage factor
        home_advantage = 0.15
        
        # Calculate strength difference
        strength_diff = home_points_per_game - away_points_per_game
        
        # Base probabilities
        base_home = 0.35
        base_draw = 0.30
        base_away = 0.35
        
        # Adjust based on strength difference
        if strength_diff > 0.5:
            home_win = base_home + 0.2 + home_advantage
            draw = base_draw - 0.1
            away_win = base_away - 0.1
        elif strength_diff < -0.5:
            home_win = base_home - 0.1 + home_advantage
            draw = base_draw - 0.05
            away_win = base_away + 0.15
        else:
            home_win = base_home + home_advantage
            draw = base_draw
            away_win = base_away - home_advantage
        
        # Normalize probabilities
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total
        
        features_dict = {
            'home_points_per_game': home_points_per_game,
            'away_points_per_game': away_points_per_game,
            'strength_difference': strength_diff,
            'prediction_method': 'heuristic'
        }
        
        return home_win, draw, away_win, features_dict
    
    def predict_score(
        self,
        home_team_stats: Dict,
        away_team_stats: Dict
    ) -> Tuple[float, float]:
        """
        Predict expected goals for both teams
        
        Returns:
            Tuple of (predicted_home_goals, predicted_away_goals)
        """
        home_games = max(home_team_stats.get('games_played', 1), 1)
        away_games = max(away_team_stats.get('games_played', 1), 1)
        
        # Expected goals based on historical performance
        home_attack = home_team_stats.get('goals_for', 0) / home_games
        away_defense = away_team_stats.get('goals_against', 0) / away_games
        
        away_attack = away_team_stats.get('goals_for', 0) / away_games
        home_defense = home_team_stats.get('goals_against', 0) / home_games
        
        # Adjust for home advantage
        predicted_home_goals = (home_attack + away_defense) / 2 * 1.1  # 10% home advantage
        predicted_away_goals = (away_attack + home_defense) / 2 * 0.95  # 5% away disadvantage
        
        return round(predicted_home_goals, 2), round(predicted_away_goals, 2)
