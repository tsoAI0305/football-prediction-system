"""Matches API endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.match import Match, MatchStatus
from app.models.team import Team
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/matches", tags=["Matches"])


@router.get("/")
async def get_matches(
    league: Optional[str] = Query(None, description="聯賽篩選: ENG_PL, GER_B1"),
    date: Optional[str] = Query(None, description="日期篩選: YYYY-MM-DD"),
    status: Optional[MatchStatus] = Query(None, description="狀態篩選"),
    limit: int = Query(20, le=100, description="返回數量限制"),
    db: Session = Depends(get_db)
):
    """
    取得賽事列表。
    
    支援多種篩選條件：
    - **league**: 聯賽篩選 (如: ENG_PL, GER_B1)
    - **date**: 日期篩選 (格式: YYYY-MM-DD)
    - **status**: 狀態篩選 (scheduled, live, finished, postponed)
    - **limit**: 返回數量限制 (最多100場)
    
    返回包含賽事詳情和 AI 推薦指數的列表。
    """
    query = db.query(Match)
    
    # Apply filters
    if league:
        query = query.filter(Match.league == league)
    
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(
                text("DATE(match_date) = :target_date")
            ).params(target_date=target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式錯誤，請使用 YYYY-MM-DD")
    
    if status:
        query = query.filter(Match.status == status)
    
    # Order by date and limit
    matches = query.order_by(Match.match_date).limit(limit).all()
    
    # Format response
    results = []
    for match in matches:
        match_data = {
            "id": match.id,
            "league": match.league,
            "match_date": match.match_date,
            "status": match.status.value,
            "home_team": {
                "id": match.home_team.id,
                "name": match.home_team.name,
                "current_points": match.home_team.current_points,
                "current_rank": match.home_team.current_rank
            } if match.home_team else None,
            "away_team": {
                "id": match.away_team.id,
                "name": match.away_team.name,
                "current_points": match.away_team.current_points,
                "current_rank": match.away_team.current_rank
            } if match.away_team else None,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "odds": {
                "home": match.odds_home,
                "draw": match.odds_draw,
                "away": match.odds_away
            }
        }
        results.append(match_data)
    
    return {
        "total": len(results),
        "matches": results
    }


@router.get("/{match_id}")
async def get_match_detail(match_id: int, db: Session = Depends(get_db)):
    """
    取得單場比賽詳細資訊。
    
    包含：
    - 比賽基本資訊
    - 主客隊詳細數據
    - 預測記錄（如有）
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="比賽不存在")
    
    return {
        "match": {
            "id": match.id,
            "league": match.league,
            "match_date": match.match_date,
            "status": match.status.value,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "odds": {
                "home": match.odds_home,
                "draw": match.odds_draw,
                "away": match.odds_away
            }
        },
        "home_team": {
            "id": match.home_team.id,
            "name": match.home_team.name,
            "league": match.home_team.league,
            "current_points": match.home_team.current_points,
            "current_gd": match.home_team.current_gd,
            "current_rank": match.home_team.current_rank,
            "recent_form": match.home_team.recent_form,
            "home_win_rate": match.home_team.home_win_rate
        } if match.home_team else None,
        "away_team": {
            "id": match.away_team.id,
            "name": match.away_team.name,
            "league": match.away_team.league,
            "current_points": match.away_team.current_points,
            "current_gd": match.away_team.current_gd,
            "current_rank": match.away_team.current_rank,
            "recent_form": match.away_team.recent_form,
            "away_win_rate": match.away_team.away_win_rate
        } if match.away_team else None,
        "predictions": [
            {
                "id": p.id,
                "predicted_result": p.predicted_result.value,
                "confidence_home": p.confidence_home,
                "confidence_draw": p.confidence_draw,
                "confidence_away": p.confidence_away,
                "ai_score": p.ai_score,
                "betting_advice": p.betting_advice,
                "value_rating": p.value_rating,
                "created_at": p.created_at
            }
            for p in match.predictions
        ]
    }
