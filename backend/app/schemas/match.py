"""Match schemas for API."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TeamBase(BaseModel):
    """Base team schema."""
    id: int
    name: str
    league: str
    current_points: int
    current_gd: int
    
    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    """Base match schema."""
    id: int
    league: str
    match_date: datetime
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    odds_home: float
    odds_draw: float
    odds_away: float
    
    class Config:
        from_attributes = True


class MatchDetail(MatchBase):
    """Detailed match schema with team information."""
    home_team: TeamBase
    away_team: TeamBase
    
    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Match list response schema."""
    total: int
    matches: list
