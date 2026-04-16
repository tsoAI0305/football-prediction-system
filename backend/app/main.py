"""FastAPI main application."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os

app = FastAPI(
    title="Football Prediction API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Football Prediction API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/predictions/")
async def get_predictions(
    league: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
):
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        all_predictions = json.load(f)
    
    filtered = all_predictions
    
    if league:
        filtered = [p for p in filtered if p["league"].lower() == league.lower()]
    
    if team:
        filtered = [p for p in filtered 
                   if team.lower() in p["home_team"].lower() 
                   or team.lower() in p["away_team"].lower()]
    
    if date:
        filtered = [p for p in filtered if p["date"] == date]
    
    return {"total": len(filtered), "predictions": filtered}

@app.get("/api/predictions/leagues")
async def get_leagues():
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料��生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    leagues = list(set(p["league"] for p in predictions))
    
    return {"leagues": sorted(leagues), "count": len(leagues)}

@app.get("/api/predictions/teams")
async def get_teams(league: Optional[str] = None):
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    if league:
        predictions = [p for p in predictions if p["league"] == league]
    
    teams = set()
    for p in predictions:
        teams.add(p["home_team"])
        teams.add(p["away_team"])
    
    return {"teams": sorted(list(teams)), "count": len(teams)}

@app.get("/api/history/")
async def get_history(
    limit: int = Query(30, le=100),
    only_completed: bool = Query(False)
):
    """取得預測歷史記錄"""
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="尚無預測記錄")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    history_records = []
    for idx, pred in enumerate(predictions[:limit], 1):
        record = {
            "id": idx,
            "date": pred["date"],
            "time": pred["time"],
            "league": pred["league"],
            "home_team": pred["home_team"],
            "away_team": pred["away_team"],
            "predicted_result": pred["prediction"]["prediction"],
            "predicted_score": pred["prediction"]["expected_score"],
            "confidence": pred["prediction"]["confidence"],
            "actual_result": None,
            "actual_score": None,
            "is_correct": None
        }
        history_records.append(record)
    
    if only_completed:
        history_records = [r for r in history_records if r["actual_result"] is not None]
    
    return {
        "total": len(history_records),
        "records": history_records
    }

@app.get("/api/history/stats")
async def get_history_stats():
    """取得預測統計"""
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="尚無預測記錄")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    
    total = len(predictions)
    home_wins = sum(1 for p in predictions if p["prediction"]["prediction"] == "home_win")
    draws = sum(1 for p in predictions if p["prediction"]["prediction"] == "draw")
    away_wins = sum(1 for p in predictions if p["prediction"]["prediction"] == "away_win")
    
    avg_confidence = sum(p["prediction"]["confidence"] for p in predictions) / total if total > 0 else 0
    
    league_stats = {}
    for pred in predictions:
        league = pred["league"]
        if league not in league_stats:
            league_stats[league] = 0
        league_stats[league] += 1
    
    return {
        "total_predictions": total,
        "result_distribution": {
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins
        },
        "average_confidence": round(avg_confidence, 2),
        "league_distribution": league_stats,
        "accuracy_rate": None
    }
@app.get("/api/teams/{team_name}")
async def get_team_details(team_name: str):
    """取得球隊詳細資訊"""
    import sys
    sys.path.insert(0, "scripts")
    from predict_match import predict_match
    
    predictions_file = "data/final_predictions.json"
    
    if not os.path.exists(predictions_file):
        raise HTTPException(status_code=404, detail="預測資料未生成")
    
    with open(predictions_file, "r", encoding="utf-8") as f:
        all_predictions = json.load(f)
    
    # 找到該球隊的任一場比賽
    team_match = None
    opponent = None
    league = None
    upcoming_matches = []
    
    for pred in all_predictions:
        if pred["home_team"] == team_name:
            if not team_match:
                team_match = pred
                opponent = pred["away_team"]
                league = pred["league"]
            upcoming_matches.append(pred)
        elif pred["away_team"] == team_name:
            if not team_match:
                team_match = pred
                opponent = pred["home_team"]
                league = pred["league"]
            upcoming_matches.append(pred)
    
    if not team_match:
        raise HTTPException(status_code=404, detail=f"找不到球隊: {team_name}")
    
    # 主動計算主客場數據
    home_prediction = predict_match(team_name, opponent)
    home_analysis = home_prediction.get("analysis", {})
    home_win_rate = home_analysis.get("home_win_rate", 0)
    home_score = home_analysis.get("home_total_score", 0)
    home_avg_goals = home_analysis.get("home_avg_goals", 0)
    recent_form = home_analysis.get("home_form", "")
    
    away_prediction = predict_match(opponent, team_name)
    away_analysis = away_prediction.get("analysis", {})
    away_win_rate = away_analysis.get("away_win_rate", 0)
    away_score = away_analysis.get("away_total_score", 0)
    away_avg_goals = away_analysis.get("away_avg_goals", 0)
    
    total_score = max(home_score, away_score)
    avg_goals = (home_avg_goals + away_avg_goals) / 2
    
    # 簡化排名計算（基於綜合實力分數）
    league_teams = {}
    
    for pred in all_predictions:
        if pred["league"] != league:
            continue
        
        h_team = pred["home_team"]
        a_team = pred["away_team"]
        analysis = pred["prediction"]["analysis"]
        
        h_score = analysis["home_total_score"]
        a_score = analysis["away_total_score"]
        
        if h_team not in league_teams or league_teams[h_team] < h_score:
            league_teams[h_team] = h_score
        if a_team not in league_teams or league_teams[a_team] < a_score:
            league_teams[a_team] = a_score
    
    # 將當前球隊加入（確保有排名）
    if team_name not in league_teams:
        league_teams[team_name] = total_score
    else:
        league_teams[team_name] = max(league_teams[team_name], total_score)
    
    # 排序
    sorted_teams = sorted(league_teams.items(), key=lambda x: x[1], reverse=True)
    overall_ranking = next((i+1 for i, (t, _) in enumerate(sorted_teams) if t == team_name), None)
    
    return {
        "team_name": team_name,
        "league": league,
        "recent_form": recent_form,
        "total_score": total_score,
        "home_win_rate": home_win_rate,
        "away_win_rate": away_win_rate,
        "home_score": home_score,
        "away_score": away_score,
        "avg_goals": round(avg_goals, 2),
        "overall_ranking": overall_ranking,
        "total_teams": len(league_teams),
        "upcoming_matches": len(upcoming_matches)
    } 