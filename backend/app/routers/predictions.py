"""Predictions API endpoints."""
import os
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ml_service import MLService
from app.services.llm_service import LLMService
from app.models.match import Match
from app.models.prediction import Prediction, PredictionResult

router = APIRouter(tags=["Predictions"])

PREDICTIONS_FILE = "data/final_predictions.json"


def _load_predictions_json() -> list:
    if not os.path.exists(PREDICTIONS_FILE):
        raise HTTPException(status_code=404, detail="預測資料尚未生成，請先執行 predict_next_week.py")
    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 靜態路由（必須在 /{match_id} 之前）────────────────────────────────────────

@router.get("/")
async def get_predictions(
    league: Optional[str] = Query(None),
    team:   Optional[str] = Query(None),
    date:   Optional[str] = Query(None),
):
    """取得所有預測，支援 league / team / date 篩選"""
    predictions = _load_predictions_json()

    if league:
        predictions = [p for p in predictions if p["league"].lower() == league.lower()]
    if team:
        t = team.lower()
        predictions = [p for p in predictions
                       if t in p["home_team"].lower() or t in p["away_team"].lower()]
    if date:
        predictions = [p for p in predictions if p["date"] == date]

    return {"total": len(predictions), "predictions": predictions}


@router.get("/leagues")
async def get_leagues():
    """取得所有聯賽列表"""
    predictions = _load_predictions_json()
    leagues = sorted(set(p["league"] for p in predictions))
    return {"leagues": leagues, "count": len(leagues)}


@router.get("/teams")
async def get_teams(league: Optional[str] = Query(None)):
    """取得所有球隊列表（可依聯賽篩選）"""
    predictions = _load_predictions_json()
    if league:
        predictions = [p for p in predictions if p["league"] == league]
    teams = sorted(set(t for p in predictions for t in [p["home_team"], p["away_team"]]))
    return {"teams": teams, "count": len(teams)}


@router.get("/stats")
async def get_stats():
    """取得預測統計摘要"""
    predictions = _load_predictions_json()
    total = len(predictions)
    if total == 0:
        return {"total": 0}

    h = sum(1 for p in predictions if p["prediction"]["prediction"] == "H")
    d = sum(1 for p in predictions if p["prediction"]["prediction"] == "D")
    a = sum(1 for p in predictions if p["prediction"]["prediction"] == "A")
    over = sum(1 for p in predictions if p["prediction"]["ou_pick"] == "OVER")

    avg_conf = sum(p["prediction"]["confidence"] for p in predictions) / total

    league_dist: dict = {}
    for p in predictions:
        league_dist[p["league"]] = league_dist.get(p["league"], 0) + 1

    return {
        "total": total,
        "result_distribution": {"H": h, "D": d, "A": a},
        "ou_distribution": {"OVER": over, "UNDER": total - over},
        "avg_confidence": round(avg_conf, 3),
        "league_distribution": league_dist,
    }


# ── 動態路由（放最後，避免吃掉靜態路由）──────────────────────────────────────

@router.get("/{match_id}")
async def get_prediction_by_id(match_id: int, db: Session = Depends(get_db)):
    """
    取得單場比賽的 ML 預測 + LLM 深度分析。

    流程：
    1. 先從 final_predictions.json 找 ML 結果
    2. 若已有 LLM 分析快取（DB Prediction 表）直接回傳
    3. 否則呼叫 Groq 做補充分析，存入 DB 快取
    """
    # ── Step 1：從 JSON 取 ML 預測 ────────────────────────────────────────
    ml_pred = None
    try:
        predictions = _load_predictions_json()
        ml_pred = next((p for p in predictions if p.get("match_id") == match_id), None)
    except HTTPException:
        pass

    # ── Step 2：從 DB 取比賽資訊 ──────────────────────────────────────────
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="比賽不存在")

    # ── Step 3：檢查 LLM 快取 ─────────────────────────────────────────────
    existing = db.query(Prediction).filter(Prediction.match_id == match_id).first()
    if existing:
        return _build_response(match, ml_pred, existing)

    # ── Step 4：呼叫 Groq LLM 做補充分析 ─────────────────────────────────
    # LLM 的角色：根據 ML 數字給出「人類語言」的解讀與注意事項
    # 不取代 ML 預測，只做補充說明
    llm_analysis_text = "LLM 分析未啟用"
    llm_sentiment = 0.0

    llm_service = LLMService()
    if match.home_team and match.away_team:
        try:
            # 把 ML 結果一起餵給 LLM，讓它做「理由補充」而非重新預測
            ml_context = ""
            if ml_pred:
                p = ml_pred["prediction"]
                ml_context = (
                    f"ML 模型預測結果：{p['prediction']}（信心{p['confidence']*100:.0f}%），"
                    f"大小球：{p['ou_pick']}（{p['over25_prob']*100:.0f}%）。"
                    f"投注建議：{p['betting_advice']}。"
                    f"請根據以上數據，用繁體中文補充說明這場比賽的關鍵影響因素，"
                    f"以及是否有需要特別注意的風險（50字以內）。"
                )

            result = await llm_service.analyze_match(
                match.home_team,
                match.away_team,
                extra_context=ml_context,  # llm_service 需支援此參數
            )
            llm_analysis_text = result.get("analysis", "")
            llm_sentiment = result.get("sentiment", 0.0)
        except Exception:
            llm_analysis_text = "LLM 分析暫時無法使用"

    # ── Step 5：存入 DB 快取 ──────────────────────────────────────────────
    if ml_pred:
        p = ml_pred["prediction"]
        pred_record = Prediction(
            match_id=match_id,
            predicted_result=PredictionResult(p["prediction"]),
            confidence_home=p["home_win_prob"],
            confidence_draw=p["draw_prob"],
            confidence_away=p["away_win_prob"],
            ai_score=round(p["confidence"] * 10, 2),
            betting_advice=p["betting_advice"],
            value_rating=0.0,
            llm_analysis=llm_analysis_text,
            news_sentiment=llm_sentiment,
        )
        db.add(pred_record)
        db.commit()
        db.refresh(pred_record)
        existing = pred_record

    return _build_response(match, ml_pred, existing)


def _build_response(match: Match, ml_pred: Optional[dict], db_pred) -> dict:
    """組合回傳格式"""
    base = {
        "match_id": match.id,
        "league":   match.league,
        "date":     match.match_date.strftime("%Y-%m-%d") if match.match_date else None,
        "time":     match.match_date.strftime("%H:%M")    if match.match_date else None,
        "home_team": match.home_team,
        "away_team": match.away_team,
    }

    if ml_pred:
        base["prediction"] = ml_pred["prediction"]
    elif db_pred:
        base["prediction"] = {
            "prediction":    db_pred.predicted_result.value,
            "confidence":    db_pred.ai_score / 10 if db_pred.ai_score else 0,
            "home_win_prob": db_pred.confidence_home,
            "draw_prob":     db_pred.confidence_draw,
            "away_win_prob": db_pred.confidence_away,
            "over25_prob":   0.5,
            "under25_prob":  0.5,
            "ou_pick":       "OVER",
            "betting_advice": db_pred.betting_advice or "",
        }

    if db_pred:
        base["llm_analysis"] = db_pred.llm_analysis
        base["news_sentiment"] = db_pred.news_sentiment

    return base