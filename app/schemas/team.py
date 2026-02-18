from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TeamBase(BaseModel):
    name: str = Field(..., description="Team name")
    league: str = Field(..., description="League name")
    country: str = Field(..., description="Country")


class TeamCreate(TeamBase):
    pass


class TeamResponse(TeamBase):
    id: int
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
