"""Match model for database."""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime, timezone


class MatchStatus(str, enum.Enum):
    """Match status enumeration."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"


class Match(Base):
    """Match model representing football matches."""
    
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    league = Column(String, index=True)  # ENG_PL, GER_B1, etc.
    match_date = Column(DateTime, index=True)
    status = Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)
    
    # Team references
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    
    # Match scores (nullable until match finishes)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Odds data
    odds_home = Column(Float)
    odds_draw = Column(Float)
    odds_away = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    home_team = relationship(
        "Team",
        foreign_keys=[home_team_id],
        back_populates="home_matches"
    )
    away_team = relationship(
        "Team",
        foreign_keys=[away_team_id],
        back_populates="away_matches"
    )
    predictions = relationship("Prediction", back_populates="match")
    
    def __repr__(self):
        """String representation."""
        return (
            f"<Match(id={self.id}, "
            f"{self.home_team.name if self.home_team else 'N/A'} vs "
            f"{self.away_team.name if self.away_team else 'N/A'})>"
        )
