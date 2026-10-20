"""Machine Learning service for match predictions."""

import joblib
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# ── Feature 欄位定義（與 feature_engineer 輸出對齊）─────────────────────────
FEATURE_COLS = [
    "home_rank", "home_points", "home_goal_diff", "home_wins",
    "home_draws", "home_losses", "home_played",
    "home_goals_for", "home_goals_against",
    "away_rank", "away_points", "away_goal_diff", "away_wins",
    "away_draws", "away_losses", "away_played",
    "away_goals_for", "away_goals_against",
    "rank_diff", "points_diff", "gd_diff",
    "home_home_win_rate", "home_away_win_rate", "home_recent_form",
    "away_home_win_rate", "away_away_win_rate", "away_recent_form",
    "home_elo", "away_elo", "elo_diff",
    "home_rest_days", "away_rest_days",
    "h2h_home_win_rate", "h2h_games",
    "home_shots_pg", "away_shots_pg", "shots_diff",
    "implied_home", "implied_draw", "implied_away",
]

TARGET_COL = "result"  # H / D / A


class MLService:
    """ML service for predicting match outcomes."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path or "models/ensemble_model.pkl")
        self.model = self._load_model()
        self.feature_cols = FEATURE_COLS

    def _load_model(self):
        if self.model_path.exists():
            try:
                model = joblib.load(self.model_path)
                logger.info(f"[MLService] Model loaded: {self.model_path}")
                return model
            except Exception as e:
                logger.exception(f"[MLService] Error loading model: {e}")
        return None

    # ── 訓練 ──────────────────────────────────────────────────────────────────

    def train(self, features_df: pd.DataFrame) -> Dict:
        """
        用 feature_engineer 輸出的 DataFrame 訓練模型。
        features_df 必須包含 result 欄位（H/D/A）。

        Returns: dict with accuracy, n_samples, feature_importance
        """
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import VotingClassifier
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import LabelEncoder

        df = features_df.dropna(subset=[TARGET_COL]).copy()
        df = df[df[TARGET_COL].isin(["H", "D", "A"])]

        if len(df) < 50:
            raise ValueError(f"訓練樣本不足：{len(df)} 場，需要至少 50 場有結果的比賽")

        # 取交集（避免欄位不存在）
        available = [c for c in FEATURE_COLS if c in df.columns]
        X = df[available].fillna(0).values

        le = LabelEncoder()
        y = le.fit_transform(df[TARGET_COL])  # A=0, D=1, H=2

        # Ensemble
        gb  = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
        rf  = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
        lr  = LogisticRegression(max_iter=5000, solver="saga", random_state=42)

        ensemble = VotingClassifier(
            estimators=[("gb", gb), ("rf", rf), ("lr", lr)],
            voting="soft",
        )
        ensemble.fit(X, y)

        # 交叉驗證
        cv_scores = cross_val_score(ensemble, X, y, cv=5, scoring="accuracy")

        # 儲存模型 + metadata
        self.model_path.parent.mkdir(exist_ok=True)
        joblib.dump({
            "model": ensemble,
            "label_encoder": le,
            "feature_cols": available,
        }, self.model_path)

        self.model = joblib.load(self.model_path)
        logger.info(f"[MLService] Model trained & saved. CV accuracy: {cv_scores.mean():.3f}")

        return {
            "n_samples": len(df),
            "cv_accuracy": round(float(cv_scores.mean()), 4),
            "cv_std": round(float(cv_scores.std()), 4),
            "features_used": available,
        }

    # ── 預測 ──────────────────────────────────────────────────────────────────

    def predict_from_dataframe(
        self,
        features_df: pd.DataFrame,
        model_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        輸入 feature_engineer 輸出的 DataFrame，
        回傳每場比賽的勝平負機率。
        """
        df = features_df.copy()
        if "match_id" not in df.columns:
            df["match_id"] = df.index.astype(str)

        out = pd.DataFrame()
        out["match_id"] = df["match_id"].astype(str)

        probs = self._compute_probs(df)

        out["predicted_home_win_prob"]  = probs[:, 0].round(4)
        out["predicted_draw_prob"]      = probs[:, 1].round(4)
        out["predicted_away_win_prob"]  = probs[:, 2].round(4)
        out["prediction"]               = [["H","D","A"][int(np.argmax(p))] for p in probs]
        out["confidence"]               = probs.max(axis=1).round(4)
        out["model_version"]            = model_name or self._model_version()
        out["pred_timestamp"]           = pd.Timestamp.now()

        return out

    def _compute_probs(self, df: pd.DataFrame) -> np.ndarray:
        """嘗試用模型預測，失敗則 fallback 到均勻分佈"""
        if self.model is not None:
            try:
                payload = self.model  # dict or model
                if isinstance(payload, dict):
                    model_obj = payload["model"]
                    feat_cols  = payload.get("feature_cols", FEATURE_COLS)
                    le         = payload.get("label_encoder")
                else:
                    model_obj  = payload
                    feat_cols  = FEATURE_COLS
                    le         = None

                available = [c for c in feat_cols if c in df.columns]
                X = df[available].fillna(0).values

                raw_probs = model_obj.predict_proba(X)  # shape (n, 3)

                # LabelEncoder 順序是 A=0,D=1,H=2 → 重排成 H,D,A
                if le is not None:
                    classes = list(le.classes_)        # ['A','D','H']
                    h_idx = classes.index("H")
                    d_idx = classes.index("D")
                    a_idx = classes.index("A")
                    return raw_probs[:, [h_idx, d_idx, a_idx]]
                return raw_probs

            except Exception as e:
                logger.error(f"[MLService] predict_proba failed: {e}")

        # Fallback：用 odds，沒有 odds 就均勻分佈
        probs_list = []
        for _, row in df.iterrows():
            oh = row.get("odds_home") or 0.0
            od = row.get("odds_draw") or 0.0
            oa = row.get("odds_away") or 0.0
            probs_list.append(self._odds_to_probs(oh, od, oa))
        return np.vstack(probs_list)

    def _odds_to_probs(self, oh, od, oa) -> np.ndarray:
        try:
            ph = 1/float(oh) if oh and float(oh)>0 else 0.0
            pd_ = 1/float(od) if od and float(od)>0 else 0.0
            pa = 1/float(oa) if oa and float(oa)>0 else 0.0
        except Exception:
            ph = pd_ = pa = 0.0
        total = ph + pd_ + pa
        if total <= 0:
            return np.array([0.33, 0.34, 0.33])
        return np.array([ph/total, pd_/total, pa/total])

    def _model_version(self) -> str:
        if self.model is None:
            return "odds-fallback"
        if isinstance(self.model, dict):
            return self.model.get("model").__class__.__name__
        return self.model.__class__.__name__

    # ── 舊介面相容（保留給 predict_match）────────────────────────────────────

    def predict_match(self, match) -> Dict:
        """舊介面：接受 Match ORM 物件"""
        features = self._extract_features(match)
        probs = self._odds_to_probs(
            getattr(match, "odds_home", 0),
            getattr(match, "odds_draw", 0),
            getattr(match, "odds_away", 0),
        )
        if self.model is not None:
            try:
                payload = self.model
                model_obj = payload["model"] if isinstance(payload, dict) else payload
                probs_raw = model_obj.predict_proba([features])[0]
                if isinstance(payload, dict) and "label_encoder" in payload:
                    le = payload["label_encoder"]
                    classes = list(le.classes_)
                    probs = probs_raw[[classes.index("H"), classes.index("D"), classes.index("A")]]
                else:
                    probs = probs_raw
            except Exception as e:
                logger.error(f"[MLService] predict_match model error: {e}")

        prediction = ["H", "D", "A"][int(np.argmax(probs))]
        confidence = float(max(probs))
        advice, value_rating = self._generate_betting_advice(prediction, probs, match)

        return {
            "prediction": prediction,
            "probabilities": {"H": float(probs[0]), "D": float(probs[1]), "A": float(probs[2])},
            "ai_score": round(confidence * 10, 2),
            "betting_advice": advice,
            "value_rating": value_rating,
        }

    def _extract_features(self, match) -> List[float]:
        return [
            getattr(match, "odds_home", 0) or 0,
            getattr(match, "odds_draw", 0) or 0,
            getattr(match, "odds_away", 0) or 0,
        ]

    def _generate_betting_advice(self, prediction, probs, match) -> Tuple[str, float]:
        confidence = float(max(probs))
        odds_map = {
            "H": getattr(match, "odds_home", 0) or 1.0,
            "D": getattr(match, "odds_draw", 0) or 1.0,
            "A": getattr(match, "odds_away", 0) or 1.0,
        }
        predicted_odds = float(odds_map.get(prediction, 1.0))
        market_prob = 1.0 / predicted_odds if predicted_odds > 0 else 0.0
        idx = ["H", "D", "A"].index(prediction)
        value = (float(probs[idx]) - market_prob) * 10

        result_names = {"H": "主勝", "D": "平局", "A": "客勝"}
        rn = result_names.get(prediction, prediction)

        if value > 0.8 and confidence > 0.6:
            advice = f"強烈推薦投注{rn}（信心度: {confidence*100:.1f}%）"
        elif value > 0.3 and confidence > 0.5:
            advice = f"建議小注{rn}（信心度: {confidence*100:.1f}%）"
        elif confidence > 0.5:
            advice = f"預測{rn}，但無明顯投注價值"
        else:
            advice = "賽果難以預測，建議觀戰為主"

        return advice, max(0.0, min(10.0, value * 10))
