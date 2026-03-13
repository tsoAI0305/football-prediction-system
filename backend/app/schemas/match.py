"""Match schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MatchBase(BaseModel):
    """Base match schema."""
    home_team: str
    away_team: str
    league: str
    match_date: datetime
    status: str = "upcoming"


class MatchCreate(MatchBase):
    """Schema for creating a match."""
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    api_fixture_id: Optional[int] = None


class MatchUpdate(BaseModel):
    """Schema for updating a match."""
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for match response."""
    id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    api_fixture_id: Optional[int] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True