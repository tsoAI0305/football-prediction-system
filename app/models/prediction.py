from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from datetime import datetime
from .base import Base


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    # ML Predictions
    home_win_probability = Column(Float, nullable=False)
    draw_probability = Column(Float, nullable=False)
    away_win_probability = Column(Float, nullable=False)
    
    # Predicted scores
    predicted_home_score = Column(Float, nullable=True)
    predicted_away_score = Column(Float, nullable=True)
    
    # Model details
    model_name = Column(String, nullable=False)  # e.g., "xgboost", "lightgbm", "ensemble"
    model_version = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # LLM Analysis
    llm_analysis = Column(String, nullable=True)
    llm_provider = Column(String, nullable=True)  # e.g., "groq"
    
    # Feature importance or additional data
    features_used = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
