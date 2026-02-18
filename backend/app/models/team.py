"""Team model for database."""
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Team(Base):
    """Team model representing football teams."""
    
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    league = Column(String, index=True)
    
    # Current season statistics
    current_points = Column(Integer, default=0)
    current_gd = Column(Integer, default=0)  # Goal difference
    current_rank = Column(Integer, nullable=True)
    
    # Calculated features for predictions
    recent_form = Column(String)  # "WWDLL" - last 5 matches
    home_win_rate = Column(Float, default=0.0)
    away_win_rate = Column(Float, default=0.0)
    
    # Relationships
    home_matches = relationship(
        "Match",
        foreign_keys="Match.home_team_id",
        back_populates="home_team"
    )
    away_matches = relationship(
        "Match",
        foreign_keys="Match.away_team_id",
        back_populates="away_team"
    )
    
    def __repr__(self):
        """String representation."""
        return f"<Team(id={self.id}, name='{self.name}', league='{self.league}')>"
