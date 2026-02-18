from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PredictionHistoryResponse(BaseModel):
    id: int
    prediction_id: int
    match_id: int
    was_correct: Optional[bool] = None
    actual_result: Optional[str] = None
    predicted_result: str
    probability_score: Optional[float] = None
    brier_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
