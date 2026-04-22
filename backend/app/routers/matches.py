"""Match routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.match import Match
from app.models.team import Team
from app.schemas.match import MatchResponse, MatchCreate


def _serialize_match(match: Match, db: Session):
    """Serialize Match ORM object into dict for response."""
    home_name = match.home_team
    away_name = match.away_team
    # if names not set, try to resolve from team ids
    try:
        if not home_name and match.home_team_id:
            t = db.query(Team).filter(Team.id == match.home_team_id).first()
            if t:
                home_name = t.name
        if not away_name and match.away_team_id:
            t = db.query(Team).filter(Team.id == match.away_team_id).first()
            if t:
                away_name = t.name
    except Exception:
        pass

    return {
        "id": match.id,
        "league": match.league,
        "match_date": match.match_date,
        "status": match.status,
        "home_team": home_name,
        "away_team": away_name,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "api_fixture_id": match.api_fixture_id,
        "home_team_id": match.home_team_id,
        "away_team_id": match.away_team_id,
        "created_at": match.created_at,
        "updated_at": match.updated_at,
        "odds_home": match.odds_home,
        "odds_draw": match.odds_draw,
        "odds_away": match.odds_away,
    }

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
    return [_serialize_match(m, db) for m in matches]


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
    return [_serialize_match(m, db) for m in matches]


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get a specific match."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return _serialize_match(match, db)


@router.post("/", response_model=MatchResponse)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    """Create a new match."""
    db_match = Match(**match.dict())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match