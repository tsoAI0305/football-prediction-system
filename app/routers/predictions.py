from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.prediction import Prediction
from app.models.match import Match
from app.models.team import Team
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.services.ml_predictor import MLPredictionService
from app.services.llm_analyzer import LLMAnalysisService
from datetime import datetime

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"]
)

# Initialize services
ml_service = MLPredictionService()
llm_service = LLMAnalysisService()


@router.get("/", response_model=List[PredictionResponse])
def get_predictions(
    skip: int = 0,
    limit: int = 100,
    match_id: int = None,
    db: Session = Depends(get_db)
):
    """Get all predictions with optional filters"""
    query = db.query(Prediction)
    
    if match_id:
        query = query.filter(Prediction.match_id == match_id)
    
    predictions = query.offset(skip).limit(limit).all()
    return predictions


@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get a specific prediction by ID"""
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction with id {prediction_id} not found"
        )
    
    return prediction


@router.post("/", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
    prediction_data: PredictionCreate,
    include_llm_analysis: bool = False,
    db: Session = Depends(get_db)
):
    """Create a new prediction (can be manual or auto-generated)"""
    
    # Verify match exists
    match = db.query(Match).filter(Match.id == prediction_data.match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {prediction_data.match_id} not found"
        )
    
    # Create prediction
    db_prediction = Prediction(
        match_id=prediction_data.match_id,
        home_win_probability=prediction_data.home_win_probability,
        draw_probability=prediction_data.draw_probability,
        away_win_probability=prediction_data.away_win_probability,
        predicted_home_score=prediction_data.predicted_home_score,
        predicted_away_score=prediction_data.predicted_away_score,
        model_name=prediction_data.model_name,
        model_version=prediction_data.model_version,
        confidence_score=prediction_data.confidence_score,
        features_used=prediction_data.features_used
    )
    
    # Add LLM analysis if requested
    if include_llm_analysis:
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
        
        if home_team and away_team:
            home_stats = {
                'wins': home_team.wins,
                'draws': home_team.draws,
                'losses': home_team.losses,
                'goals_for': home_team.goals_for,
                'goals_against': home_team.goals_against,
                'points': home_team.points,
                'games_played': home_team.wins + home_team.draws + home_team.losses
            }
            
            away_stats = {
                'wins': away_team.wins,
                'draws': away_team.draws,
                'losses': away_team.losses,
                'goals_for': away_team.goals_for,
                'goals_against': away_team.goals_against,
                'points': away_team.points,
                'games_played': away_team.wins + away_team.draws + away_team.losses
            }
            
            pred_probs = {
                'home_win': prediction_data.home_win_probability,
                'draw': prediction_data.draw_probability,
                'away_win': prediction_data.away_win_probability
            }
            
            analysis = llm_service.analyze_match(
                home_team.name,
                away_team.name,
                home_stats,
                away_stats,
                pred_probs
            )
            
            if analysis:
                db_prediction.llm_analysis = analysis
                db_prediction.llm_provider = "groq"
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return db_prediction


@router.post("/generate/{match_id}", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def generate_prediction(
    match_id: int,
    include_llm_analysis: bool = True,
    db: Session = Depends(get_db)
):
    """Generate an ML-based prediction for a match"""
    
    # Get match
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {match_id} not found"
        )
    
    # Get teams
    home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
    
    if not home_team or not away_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team data not found"
        )
    
    # Prepare team statistics
    home_stats = {
        'wins': home_team.wins,
        'draws': home_team.draws,
        'losses': home_team.losses,
        'goals_for': home_team.goals_for,
        'goals_against': home_team.goals_against,
        'points': home_team.points,
        'games_played': home_team.wins + home_team.draws + home_team.losses
    }
    
    away_stats = {
        'wins': away_team.wins,
        'draws': away_team.draws,
        'losses': away_team.losses,
        'goals_for': away_team.goals_for,
        'goals_against': away_team.goals_against,
        'points': away_team.points,
        'games_played': away_team.wins + away_team.draws + away_team.losses
    }
    
    # Generate prediction
    home_win_prob, draw_prob, away_win_prob, features = ml_service.predict_match_outcome(
        home_stats, away_stats, use_ensemble=True
    )
    
    # Predict scores
    predicted_home, predicted_away = ml_service.predict_score(home_stats, away_stats)
    
    # Calculate confidence
    max_prob = max(home_win_prob, draw_prob, away_win_prob)
    confidence = max_prob
    
    # Create prediction
    db_prediction = Prediction(
        match_id=match_id,
        home_win_probability=home_win_prob,
        draw_probability=draw_prob,
        away_win_probability=away_win_prob,
        predicted_home_score=predicted_home,
        predicted_away_score=predicted_away,
        model_name="ensemble",
        model_version="1.0",
        confidence_score=confidence,
        features_used=features
    )
    
    # Add LLM analysis
    if include_llm_analysis:
        pred_probs = {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob
        }
        
        analysis = llm_service.analyze_match(
            home_team.name,
            away_team.name,
            home_stats,
            away_stats,
            pred_probs
        )
        
        if analysis:
            db_prediction.llm_analysis = analysis
            db_prediction.llm_provider = "groq"
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return db_prediction
