"""Prediction model for database."""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime, timezone


class PredictionResult(str, enum.Enum):
    """Prediction result enumeration."""
    HOME_WIN = "H"
    DRAW = "D"
    AWAY_WIN = "A"


class Prediction(Base):
    """Prediction model storing AI predictions for matches."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    
    # AI prediction results
    predicted_result = Column(Enum(PredictionResult))
    confidence_home = Column(Float)  # 0-1 probability
    confidence_draw = Column(Float)  # 0-1 probability
    confidence_away = Column(Float)  # 0-1 probability
    ai_score = Column(Float)  # 0-10 overall confidence score
    
    # Betting advice
    betting_advice = Column(String)
    value_rating = Column(Float)  # 0-10 value rating
    
    # LLM analysis
    llm_analysis = Column(String, nullable=True)
    news_sentiment = Column(Float, nullable=True)  # -1 to 1
    
    # Actual results (updated after match)
    actual_result = Column(Enum(PredictionResult), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    match = relationship("Match", back_populates="predictions")
    
    def __repr__(self):
        """String representation."""
        return (
            f"<Prediction(id={self.id}, match_id={self.match_id}, "
            f"predicted={self.predicted_result}, ai_score={self.ai_score})>"
        )
