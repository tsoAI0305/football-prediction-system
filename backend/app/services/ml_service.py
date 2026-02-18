"""Machine Learning service for match predictions."""
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


class MLService:
    """ML service for predicting match outcomes."""
    
    def __init__(self):
        """Initialize ML service and load model if available."""
        self.model = self._load_model()
    
    def _load_model(self):
        """
        Load trained ML model from disk.
        
        Returns:
            Model object or None if not available
        """
        model_path = Path("models/ensemble_model.pkl")
        if model_path.exists():
            try:
                return joblib.load(model_path)
            except Exception as e:
                print(f"Error loading model: {e}")
                return None
        return None
    
    def predict_match(self, match) -> Dict:
        """
        Predict match outcome using ML model or odds-based fallback.
        
        Args:
            match: Match object with team and odds information
            
        Returns:
            Dictionary containing:
                - prediction: Predicted result ('H', 'D', or 'A')
                - probabilities: Dict with probabilities for each outcome
                - ai_score: AI confidence score (0-10)
                - betting_advice: Human-readable betting recommendation
                - value_rating: Value bet rating (0-10)
        """
        # Extract features from match
        features = self._extract_features(match)
        
        # Get probabilities
        if self.model:
            probs = self.model.predict_proba([features])[0]
        else:
            probs = self._odds_to_probs(
                match.odds_home,
                match.odds_draw,
                match.odds_away
            )
        
        # Determine prediction
        prediction = ['H', 'D', 'A'][np.argmax(probs)]
        confidence = float(max(probs))
        
        # Calculate AI score (0-10)
        ai_score = self._calculate_ai_score(confidence, features)
        
        # Generate betting advice
        betting_advice, value_rating = self._generate_betting_advice(
            prediction, probs, match
        )
        
        return {
            'prediction': prediction,
            'probabilities': {
                'H': float(probs[0]),
                'D': float(probs[1]),
                'A': float(probs[2])
            },
            'ai_score': ai_score,
            'betting_advice': betting_advice,
            'value_rating': value_rating
        }
    
    def _extract_features(self, match) -> List[float]:
        """
        Extract features from match for ML model.
        
        Args:
            match: Match object
            
        Returns:
            List of feature values
        """
        return [
            match.odds_home,
            match.odds_draw,
            match.odds_away,
            match.home_team.current_points if match.home_team else 0,
            match.away_team.current_points if match.away_team else 0,
            match.home_team.current_gd if match.home_team else 0,
            match.away_team.current_gd if match.away_team else 0,
            match.home_team.home_win_rate if match.home_team else 0.0,
            match.away_team.away_win_rate if match.away_team else 0.0
        ]
    
    def _odds_to_probs(self, odds_h: float, odds_d: float, odds_a: float) -> np.ndarray:
        """
        Convert betting odds to probabilities.
        
        Args:
            odds_h: Home win odds
            odds_d: Draw odds
            odds_a: Away win odds
            
        Returns:
            Normalized probability array [P(H), P(D), P(A)]
        """
        prob_h = 1 / odds_h
        prob_d = 1 / odds_d
        prob_a = 1 / odds_a
        total = prob_h + prob_d + prob_a
        
        # Normalize to sum to 1
        return np.array([prob_h / total, prob_d / total, prob_a / total])
    
    def _calculate_ai_score(self, confidence: float, features: List[float]) -> float:
        """
        Calculate AI confidence score.
        
        Args:
            confidence: Model confidence (0-1)
            features: Feature vector
            
        Returns:
            AI score (0-10)
        """
        # Base score from confidence
        base_score = confidence * 10
        
        # Adjust based on data quality (simplified)
        # In production, this would consider feature completeness,
        # data freshness, historical accuracy, etc.
        quality_factor = 1.0
        if features[3] == 0 and features[4] == 0:  # No team stats available
            quality_factor = 0.7
        
        final_score = base_score * quality_factor
        return min(10.0, max(0.0, final_score))
    
    def _generate_betting_advice(
        self,
        prediction: str,
        probs: np.ndarray,
        match
    ) -> Tuple[str, float]:
        """
        Generate betting advice and value rating.
        
        Args:
            prediction: Predicted outcome
            probs: Probability array
            match: Match object
            
        Returns:
            Tuple of (betting_advice, value_rating)
        """
        confidence = max(probs)
        
        # Get odds for predicted outcome
        odds_map = {
            'H': match.odds_home,
            'D': match.odds_draw,
            'A': match.odds_away
        }
        predicted_odds = odds_map[prediction]
        
        # Calculate value
        market_prob = 1 / predicted_odds
        model_prob = probs[['H', 'D', 'A'].index(prediction)]
        value = (model_prob - market_prob) * 10  # Scale to 0-10
        
        # Generate advice
        result_names = {'H': '主勝', 'D': '平局', 'A': '客勝'}
        result_name = result_names[prediction]
        
        if value > 0.8 and confidence > 0.6:
            advice = f"強烈推薦投注{result_name}（信心度: {confidence*100:.1f}%）"
        elif value > 0.3 and confidence > 0.5:
            advice = f"建議小注{result_name}（信心度: {confidence*100:.1f}%）"
        elif confidence > 0.5:
            advice = f"預測{result_name}，但無明顯投注價值"
        else:
            advice = "賽果難以預測，建議觀戰為主"
        
        value_rating = max(0.0, min(10.0, value * 10))
        
        return advice, value_rating
