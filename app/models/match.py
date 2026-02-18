from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Teams
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Match details
    league = Column(String, nullable=False)
    season = Column(String, nullable=False)
    match_date = Column(DateTime, nullable=False)
    
    # Results (null if match hasn't been played)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_finished = Column(Boolean, default=False)
    
    # Betting odds (optional)
    home_odds = Column(Float, nullable=True)
    draw_odds = Column(Float, nullable=True)
    away_odds = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
