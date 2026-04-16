"""Machine Learning service for match predictions."""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class MLService:
    """ML service for predicting match outcomes."""

    def __init__(self, model_path: Optional[str] = None):
        """Initialize ML service and load model if available."""
        self.model_path = model_path or "models/ensemble_model.pkl"
        self.model = self._load_model(self.model_path)

    def _load_model(self, model_path: str):
        """
        Load trained ML model from disk.

        Returns:
            Model object or None if not available
        """
        model_path = Path(model_path)
        if model_path.exists():
            try:
                return joblib.load(model_path)
            except Exception as e:
                print(f"[MLService] Error loading model: {e}")
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
        if self.model is not None:
            try:
                probs = self.model.predict_proba([features])[0]
            except Exception as e:
                print(f"[MLService] Model predict_proba failed: {e} - falling back to odds")
                probs = self._odds_to_probs(
                    match.odds_home,
                    match.odds_draw,
                    match.odds_away
                )
        else:
            probs = self._odds_to_probs(
                match.odds_home,
                match.odds_draw,
                match.odds_away
            )

        # Determine prediction
        prediction = ["H", "D", "A"][int(np.argmax(probs))]
        confidence = float(max(probs))

        # Calculate AI score (0-10)
        ai_score = self._calculate_ai_score(confidence, features)

        # Generate betting advice
        betting_advice, value_rating = self._generate_betting_advice(
            prediction, probs, match
        )

        return {
            "prediction": prediction,
            "probabilities": {"H": float(probs[0]), "D": float(probs[1]), "A": float(probs[2])},
            "ai_score": ai_score,
            "betting_advice": betting_advice,
            "value_rating": value_rating,
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
            match.odds_home if hasattr(match, "odds_home") else 0.0,
            match.odds_draw if hasattr(match, "odds_draw") else 0.0,
            match.odds_away if hasattr(match, "odds_away") else 0.0,
            match.home_team.current_points if getattr(match, "home_team", None) else 0,
            match.away_team.current_points if getattr(match, "away_team", None) else 0,
            match.home_team.current_gd if getattr(match, "home_team", None) else 0,
            match.away_team.current_gd if getattr(match, "away_team", None) else 0,
            match.home_team.home_win_rate if getattr(match, "home_team", None) else 0.0,
            match.away_team.away_win_rate if getattr(match, "away_team", None) else 0.0,
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
        # Avoid division by zero or invalid odds
        try:
            prob_h = 1.0 / float(odds_h) if odds_h and odds_h > 0 else 0.0
            prob_d = 1.0 / float(odds_d) if odds_d and odds_d > 0 else 0.0
            prob_a = 1.0 / float(odds_a) if odds_a and odds_a > 0 else 0.0
        except Exception:
            prob_h, prob_d, prob_a = 0.0, 0.0, 0.0

        total = prob_h + prob_d + prob_a
        if total <= 0:
            # fallback to uniform distribution
            return np.array([0.33, 0.34, 0.33])
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
        quality_factor = 1.0
        try:
            # if both teams have zero points then mark lower quality
            if len(features) > 4 and features[3] == 0 and features[4] == 0:
                quality_factor = 0.7
        except Exception:
            quality_factor = 0.9

        final_score = base_score * quality_factor
        return min(10.0, max(0.0, final_score))

    def _generate_betting_advice(self, prediction: str, probs: np.ndarray, match) -> Tuple[str, float]:
        """
        Generate betting advice and value rating.

        Args:
            prediction: Predicted outcome
            probs: Probability array
            match: Match object

        Returns:
            Tuple of (betting_advice, value_rating)
        """
        confidence = float(max(probs))

        # Get odds for predicted outcome
        odds_map = {"H": getattr(match, "odds_home", 0.0), "D": getattr(match, "odds_draw", 0.0), "A": getattr(match, "odds_away", 0.0)}
        predicted_odds = odds_map.get(prediction, 0.0)
        predicted_odds = float(predicted_odds) if predicted_odds else 1.0

        # Calculate value
        market_prob = 1.0 / predicted_odds if predicted_odds > 0 else 0.0
        idx = ["H", "D", "A"].index(prediction)
        model_prob = float(probs[idx])
        value = (model_prob - market_prob) * 10  # scale

        # Generate advice (localized)
        result_names = {"H": "主勝", "D": "平局", "A": "客勝"}
        result_name = result_names.get(prediction, prediction)

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

    # -----------------------------
    # New: DataFrame-based prediction
    # -----------------------------
    def predict_from_dataframe(self, features_df: pd.DataFrame, model_name: Optional[str] = None) -> pd.DataFrame:
        """
        Predict outcomes for a dataframe of features.

        Args:
            features_df: DataFrame where each row corresponds to a match. Must include 'match_id'.
            model_name: optional model name/version to include in output

        Returns:
            DataFrame with columns:
                match_id, predicted_home_win_prob, predicted_draw_prob, predicted_away_win_prob, model_version, pred_timestamp
        """
        if "match_id" not in features_df.columns:
            # create match_id if absent
            features_df = features_df.copy()
            features_df["match_id"] = features_df.index.astype(str)

        # Prepare output DataFrame
        out_df = pd.DataFrame()
        out_df["match_id"] = features_df["match_id"].astype(str)

        # Try to build feature matrix for model input
        X = None
        if self.model is not None:
            try:
                # choose numeric columns only (exclude id/date/categorical)
                numeric = features_df.select_dtypes(include=[np.number]).copy()
                # drop prediction-like columns if present
                for col in ["predicted_home_win_prob", "predicted_draw_prob", "predicted_away_win_prob"]:
                    if col in numeric.columns:
                        numeric = numeric.drop(columns=[col])
                # If numeric empty, fallback to odds columns
                if numeric.shape[1] == 0 and {"odds_home", "odds_draw", "odds_away"}.issubset(features_df.columns):
                    numeric = features_df[["odds_home", "odds_draw", "odds_away"]].astype(float).fillna(0.0)
                X = numeric.fillna(0.0).values
            except Exception as e:
                print(f"[MLService] Failed to construct numeric feature matrix from DataFrame: {e}")
                X = None

            if X is not None and hasattr(self.model, "predict_proba"):
                try:
                    probs = self.model.predict_proba(X)
                except Exception as e:
                    print(f"[MLService] model.predict_proba failed for DataFrame: {e}")
                    probs = None
            else:
                probs = None
        else:
            probs = None

        # If probs not produced by model, fallback to odds->probs per-row
        if probs is None:
            probs_list = []
            for _, row in features_df.iterrows():
                odds_h = row.get("odds_home") or row.get("home_odds") or row.get("home_price") or None
                odds_d = row.get("odds_draw") or row.get("draw_odds") or None
                odds_a = row.get("odds_away") or row.get("away_odds") or None
                p = self._odds_to_probs(odds_h or 0.0, odds_d or 0.0, odds_a or 0.0)
                probs_list.append(p)
            probs = np.vstack(probs_list) if len(probs_list) > 0 else np.array([])

        # Ensure shape match
        if probs.shape[0] != out_df.shape[0]:
            # if mismatch, truncate or pad
            n_rows = out_df.shape[0]
            if probs.shape[0] > n_rows:
                probs = probs[:n_rows, :]
            else:
                # pad with uniform probabilities
                pad = np.tile(np.array([0.33, 0.34, 0.33]), (n_rows - probs.shape[0], 1))
                probs = np.vstack([probs, pad])

        out_df["predicted_home_win_prob"] = probs[:, 0].astype(float)
        out_df["predicted_draw_prob"] = probs[:, 1].astype(float)
        out_df["predicted_away_win_prob"] = probs[:, 2].astype(float)
        out_df["model_version"] = model_name or (getattr(self.model, "__class__", None).__name__ if self.model is not None else "odds-fallback")
        out_df["pred_timestamp"] = pd.Timestamp.now()

        # Reorder columns
        cols = ["match_id", "predicted_home_win_prob", "predicted_draw_prob", "predicted_away_win_prob", "model_version", "pred_timestamp"]
        return out_df[cols]