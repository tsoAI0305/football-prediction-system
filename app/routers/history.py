from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.history import PredictionHistory
from app.schemas.history import PredictionHistoryResponse

router = APIRouter(
    prefix="/history",
    tags=["history"]
)


@router.get("/", response_model=List[PredictionHistoryResponse])
def get_prediction_history(
    skip: int = 0,
    limit: int = 100,
    prediction_id: int = None,
    db: Session = Depends(get_db)
):
    """Get prediction history with optional filters"""
    query = db.query(PredictionHistory)
    
    if prediction_id:
        query = query.filter(PredictionHistory.prediction_id == prediction_id)
    
    history = query.offset(skip).limit(limit).all()
    return history


@router.get("/{history_id}", response_model=PredictionHistoryResponse)
def get_history_entry(history_id: int, db: Session = Depends(get_db)):
    """Get a specific history entry by ID"""
    history = db.query(PredictionHistory).filter(PredictionHistory.id == history_id).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History entry with id {history_id} not found"
        )
    
    return history


@router.get("/stats/accuracy")
def get_accuracy_stats(db: Session = Depends(get_db)):
    """Get overall prediction accuracy statistics"""
    
    total_predictions = db.query(PredictionHistory).filter(
        PredictionHistory.was_correct.isnot(None)
    ).count()
    
    correct_predictions = db.query(PredictionHistory).filter(
        PredictionHistory.was_correct == True
    ).count()
    
    if total_predictions == 0:
        return {
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "message": "No prediction history available yet"
        }
    
    accuracy = correct_predictions / total_predictions
    
    return {
        "total_predictions": total_predictions,
        "correct_predictions": correct_predictions,
        "incorrect_predictions": total_predictions - correct_predictions,
        "accuracy": round(accuracy, 4),
        "accuracy_percentage": round(accuracy * 100, 2)
    }
