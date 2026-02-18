from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamResponse
from datetime import datetime

router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)


@router.get("/", response_model=List[TeamResponse])
def get_teams(
    skip: int = 0,
    limit: int = 100,
    league: str = None,
    db: Session = Depends(get_db)
):
    """Get all teams with optional filters"""
    query = db.query(Team)
    
    if league:
        query = query.filter(Team.league == league)
    
    teams = query.offset(skip).limit(limit).all()
    return teams


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get a specific team by ID"""
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id {team_id} not found"
        )
    
    return team


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team"""
    
    # Check if team already exists
    existing_team = db.query(Team).filter(Team.name == team.name).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team with name '{team.name}' already exists"
        )
    
    # Create new team
    db_team = Team(
        name=team.name,
        league=team.league,
        country=team.country
    )
    
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    return db_team


@router.put("/{team_id}", response_model=TeamResponse)
def update_team_stats(
    team_id: int,
    wins: int = None,
    draws: int = None,
    losses: int = None,
    goals_for: int = None,
    goals_against: int = None,
    points: int = None,
    db: Session = Depends(get_db)
):
    """Update team statistics"""
    
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id {team_id} not found"
        )
    
    # Update fields
    if wins is not None:
        team.wins = wins
    if draws is not None:
        team.draws = draws
    if losses is not None:
        team.losses = losses
    if goals_for is not None:
        team.goals_for = goals_for
    if goals_against is not None:
        team.goals_against = goals_against
    if points is not None:
        team.points = points
    
    team.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(team)
    
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    """Delete a team"""
    
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id {team_id} not found"
        )
    
    db.delete(team)
    db.commit()
    
    return None
