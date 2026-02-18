"""Prediction schemas for API."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PredictionBase(BaseModel):
    """Base prediction schema."""
    id: int
    match_id: int
    predicted_result: str
    confidence_home: float
    confidence_draw: float
    confidence_away: float
    ai_score: float
    betting_advice: str
    value_rating: float
    llm_analysis: Optional[str] = None
    news_sentiment: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionDetail(PredictionBase):
    """Detailed prediction with actual result."""
    actual_result: Optional[str] = None
    is_correct: Optional[bool] = None
    
    class Config:
        from_attributes = True
