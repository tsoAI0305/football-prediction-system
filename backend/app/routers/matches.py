"""Match routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.match import Match
from app.schemas.match import MatchResponse, MatchCreate

router = APIRouter()


@router.get("/", response_model=List[MatchResponse])
def get_matches(
    league: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """Get matches with optional filters."""
    query = db.query(Match)
    
    if league:
        query = query.filter(Match.league == league)
    
    if status:
        query = query.filter(Match.status == status)
    
    matches = query.order_by(Match.match_date.desc()).offset(skip).limit(limit).all()
    return matches


@router.get("/upcoming", response_model=List[MatchResponse])
def get_upcoming_matches(
    days: int = Query(default=7, le=30),
    league: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get upcoming matches."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    
    query = db.query(Match).filter(
        Match.status == 'upcoming',
        Match.match_date >= now,
        Match.match_date <= end_date
    )
    
    if league:
        query = query.filter(Match.league == league)
    
    matches = query.order_by(Match.match_date).all()
    return matches


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get a specific match."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.post("/", response_model=MatchResponse)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    """Create a new match."""
    db_match = Match(**match.dict())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match