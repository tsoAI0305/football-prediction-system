"""History API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.prediction import Prediction
from typing import Optional

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("/")
async def get_prediction_history(
    limit: int = Query(30, le=100, description="返回數量限制"),
    only_completed: bool = Query(False, description="僅顯示已完賽的預測"),
    db: Session = Depends(get_db)
):
    """
    取得歷史預測記錄。
    
    參數：
    - **limit**: 返回數量 (預設30，最多100)
    - **only_completed**: 是否只顯示已完賽並有實際結果的預測
    
    返回預測歷史記錄，包含：
    - 預測結果
    - 實際結果（如有）
    - 準確率統計
    """
    query = db.query(Prediction)
    
    if only_completed:
        query = query.filter(Prediction.actual_result.isnot(None))
    
    predictions = query.order_by(Prediction.created_at.desc()).limit(limit).all()
    
    # Calculate statistics
    total_predictions = len(predictions)
    correct_predictions = sum(1 for p in predictions if p.is_correct)
    accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    # Format response
    results = []
    for pred in predictions:
        match = pred.match
        results.append({
            "prediction_id": pred.id,
            "match_id": pred.match_id,
            "match_info": {
                "home_team": match.home_team.name if match.home_team else "未知",
                "away_team": match.away_team.name if match.away_team else "未知",
                "match_date": match.match_date,
                "league": match.league
            } if match else None,
            "predicted_result": pred.predicted_result.value,
            "actual_result": pred.actual_result.value if pred.actual_result else None,
            "is_correct": pred.is_correct,
            "ai_score": pred.ai_score,
            "value_rating": pred.value_rating,
            "created_at": pred.created_at
        })
    
    return {
        "total": total_predictions,
        "correct": correct_predictions,
        "accuracy": round(accuracy, 2),
        "predictions": results
    }
