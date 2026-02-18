from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.match import Match
from app.schemas.match import MatchCreate, MatchResponse, MatchUpdate
from datetime import datetime

router = APIRouter(
    prefix="/matches",
    tags=["matches"]
)


@router.get("/", response_model=List[MatchResponse])
def get_matches(
    skip: int = 0,
    limit: int = 100,
    league: str = None,
    is_finished: bool = None,
    db: Session = Depends(get_db)
):
    """Get all matches with optional filters"""
    query = db.query(Match)
    
    if league:
        query = query.filter(Match.league == league)
    
    if is_finished is not None:
        query = query.filter(Match.is_finished == is_finished)
    
    matches = query.offset(skip).limit(limit).all()
    return matches


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get a specific match by ID"""
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {match_id} not found"
        )
    
    return match


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    """Create a new match"""
    
    # Create new match
    db_match = Match(
        home_team_id=match.home_team_id,
        away_team_id=match.away_team_id,
        league=match.league,
        season=match.season,
        match_date=match.match_date,
        home_odds=match.home_odds,
        draw_odds=match.draw_odds,
        away_odds=match.away_odds
    )
    
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    
    return db_match


@router.put("/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: int,
    match_update: MatchUpdate,
    db: Session = Depends(get_db)
):
    """Update match results"""
    
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {match_id} not found"
        )
    
    # Update fields
    if match_update.home_score is not None:
        match.home_score = match_update.home_score
    
    if match_update.away_score is not None:
        match.away_score = match_update.away_score
    
    if match_update.is_finished is not None:
        match.is_finished = match_update.is_finished
    
    match.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(match)
    
    return match


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(match_id: int, db: Session = Depends(get_db)):
    """Delete a match"""
    
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {match_id} not found"
        )
    
    db.delete(match)
    db.commit()
    
    return None
