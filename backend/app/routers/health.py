"""Health check endpoint."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.schemas.response import HealthResponse
from app.utils.cache import cache

router = APIRouter(tags=["Health"])


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Readiness: database and Redis must both be up. HTTP 503 when either is not."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    redis_status = "healthy" if cache.enabled else "unhealthy"
    ready = db_status == "healthy" and redis_status == "healthy"
    body = HealthResponse(
        status="healthy" if ready else "unhealthy",
        database=db_status,
        redis=redis_status,
    )
    return JSONResponse(
        status_code=200 if ready else 503,
        content=body.model_dump(),
    )
