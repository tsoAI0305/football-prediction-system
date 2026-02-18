from .matches import router as matches_router
from .predictions import router as predictions_router
from .history import router as history_router
from .teams import router as teams_router

__all__ = ["matches_router", "predictions_router", "history_router", "teams_router"]
