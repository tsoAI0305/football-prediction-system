from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MatchBase(BaseModel):
    home_team_id: int = Field(..., description="Home team ID")
    away_team_id: int = Field(..., description="Away team ID")
    league: str = Field(..., description="League name")
    season: str = Field(..., description="Season (e.g., '2023-24')")
    match_date: datetime = Field(..., description="Match date and time")


class MatchCreate(MatchBase):
    home_odds: Optional[float] = Field(None, description="Home win odds")
    draw_odds: Optional[float] = Field(None, description="Draw odds")
    away_odds: Optional[float] = Field(None, description="Away win odds")


class MatchUpdate(BaseModel):
    home_score: Optional[int] = Field(None, description="Home team score")
    away_score: Optional[int] = Field(None, description="Away team score")
    is_finished: Optional[bool] = Field(None, description="Match finished status")


class MatchResponse(MatchBase):
    id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    is_finished: bool = False
    home_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    away_odds: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
