from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class PredictionBase(BaseModel):
    match_id: int = Field(..., description="Match ID")
    home_win_probability: float = Field(..., ge=0, le=1, description="Home win probability")
    draw_probability: float = Field(..., ge=0, le=1, description="Draw probability")
    away_win_probability: float = Field(..., ge=0, le=1, description="Away win probability")


class PredictionCreate(PredictionBase):
    predicted_home_score: Optional[float] = Field(None, description="Predicted home score")
    predicted_away_score: Optional[float] = Field(None, description="Predicted away score")
    model_name: str = Field(default="ensemble", description="ML model name")
    model_version: Optional[str] = Field(None, description="Model version")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Prediction confidence")
    features_used: Optional[Dict[str, Any]] = Field(None, description="Features used for prediction")


class PredictionResponse(PredictionBase):
    id: int
    predicted_home_score: Optional[float] = None
    predicted_away_score: Optional[float] = None
    model_name: str
    model_version: Optional[str] = None
    confidence_score: Optional[float] = None
    llm_analysis: Optional[str] = None
    llm_provider: Optional[str] = None
    features_used: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
