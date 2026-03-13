"""Prediction API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import json
import os

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# 預測結果模型
class PredictionResponse(BaseModel):
    date: str
    time: str
    league: str
    home_team: str
    away_team: str
    prediction: dict

class PredictionListResponse(BaseModel):
    total: int
    predictions: List[PredictionResponse]

@router.get("/", response_model=PredictionListResponse)
async def get_predictions(
    league: Optional[str] = Query(None, description="聯賽篩選"),
    team: Optional[str] = Query(None, description="球隊篩選"),
    date: Optional[str] = Query(None, description="日期篩選 (YYYY-MM-DD)"),
):
    """取得所有預測結果."""
    
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        all_predictions = json.load(f)
    
    filtered = all_predictions
    
    if league:
        filtered = [p for p in filtered if p['league'].lower() == league.lower()]
    
    if team:
        filtered = [p for p in filtered 
                   if team.lower() in p['home_team'].lower() 
                   or team.lower() in p['away_team'].lower()]
    
    if date:
        filtered = [p for p in filtered if p['date'] == date]
    
    return {
        "total": len(filtered),
        "predictions": filtered
    }

@router.get("/leagues")
async def get_leagues():
    """取得所有聯賽列表."""
    
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    leagues = list(set(p['league'] for p in predictions))
    
    return {
        "leagues": sorted(leagues),
        "count": len(leagues)
    }

@router.get("/teams")
async def get_teams(league: Optional[str] = None):
    """取得所有球隊列表."""
    
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    if league:
        predictions = [p for p in predictions if p['league'] == league]
    
    teams = set()
    for p in predictions:
        teams.add(p['home_team'])
        teams.add(p['away_team'])
    
    return {
        "teams": sorted(list(teams)),
        "count": len(teams)
    }

@router.post("/analyze")
async def analyze_match(home_team: str, away_team: str):
    """即時分析特定比賽（使用 AI）."""
    
    import sys
    sys.path.insert(0, '/app')
    from scripts.predict_with_ai import predict_match_with_ai
    
    try:
        result = predict_match_with_ai(home_team, away_team)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
