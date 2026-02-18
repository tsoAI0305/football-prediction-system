"""Predictions API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ml_service import MLService
from app.services.llm_service import LLMService
from app.models.match import Match
from app.models.prediction import Prediction, PredictionResult

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.get("/{match_id}")
async def get_prediction(match_id: int, db: Session = Depends(get_db)):
    """
    取得比賽的 AI 預測分析。
    
    功能包含：
    - ML 模型預測結果（勝平負概率）
    - AI 信心指數（0-10分）
    - 投注建議
    - LLM 深度分析（如啟用）
    - 新聞情緒分析
    
    如果該比賽已有預測記錄，直接返回；
    否則執行新的預測並儲存到資料庫。
    """
    # Query match
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="比賽不存在")
    
    # Check if prediction already exists
    existing_prediction = db.query(Prediction).filter(
        Prediction.match_id == match_id
    ).first()
    
    if existing_prediction:
        return {
            "id": existing_prediction.id,
            "match_id": existing_prediction.match_id,
            "prediction": {
                "result": existing_prediction.predicted_result.value,
                "probabilities": {
                    "home": existing_prediction.confidence_home,
                    "draw": existing_prediction.confidence_draw,
                    "away": existing_prediction.confidence_away
                },
                "ai_score": existing_prediction.ai_score
            },
            "betting": {
                "advice": existing_prediction.betting_advice,
                "value_rating": existing_prediction.value_rating
            },
            "analysis": {
                "llm_analysis": existing_prediction.llm_analysis,
                "news_sentiment": existing_prediction.news_sentiment
            },
            "actual_result": existing_prediction.actual_result.value if existing_prediction.actual_result else None,
            "is_correct": existing_prediction.is_correct,
            "created_at": existing_prediction.created_at
        }
    
    # Generate new prediction
    ml_service = MLService()
    llm_service = LLMService()
    
    # ML prediction
    ml_result = ml_service.predict_match(match)
    
    # LLM analysis
    if match.home_team and match.away_team:
        llm_analysis = await llm_service.analyze_match(
            match.home_team.name,
            match.away_team.name
        )
    else:
        llm_analysis = {"analysis": "球隊資訊不完整", "sentiment": 0.0}
    
    # Create prediction record
    prediction = Prediction(
        match_id=match_id,
        predicted_result=PredictionResult(ml_result['prediction']),
        confidence_home=ml_result['probabilities']['H'],
        confidence_draw=ml_result['probabilities']['D'],
        confidence_away=ml_result['probabilities']['A'],
        ai_score=ml_result['ai_score'],
        betting_advice=ml_result['betting_advice'],
        value_rating=ml_result['value_rating'],
        llm_analysis=llm_analysis['analysis'],
        news_sentiment=llm_analysis['sentiment']
    )
    
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    return {
        "id": prediction.id,
        "match_id": prediction.match_id,
        "prediction": {
            "result": prediction.predicted_result.value,
            "probabilities": {
                "home": prediction.confidence_home,
                "draw": prediction.confidence_draw,
                "away": prediction.confidence_away
            },
            "ai_score": prediction.ai_score
        },
        "betting": {
            "advice": prediction.betting_advice,
            "value_rating": prediction.value_rating
        },
        "analysis": {
            "llm_analysis": prediction.llm_analysis,
            "news_sentiment": prediction.news_sentiment
        },
        "created_at": prediction.created_at
    }
