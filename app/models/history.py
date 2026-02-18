from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from datetime import datetime
from .base import Base


class PredictionHistory(Base):
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    # Prediction accuracy metrics
    was_correct = Column(Boolean, nullable=True)  # True if prediction matched result
    actual_result = Column(String, nullable=True)  # "home_win", "draw", "away_win"
    predicted_result = Column(String, nullable=False)
    
    # Performance metrics
    probability_score = Column(Float, nullable=True)
    brier_score = Column(Float, nullable=True)  # Probability accuracy metric
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
