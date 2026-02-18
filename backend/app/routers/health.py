"""Health check endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.response import HealthResponse
from app.utils.cache import cache

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Checks the status of:
    - API service
    - Database connection
    - Redis cache
    
    Returns:
        HealthResponse with status of each service
    """
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis
    redis_status = "healthy" if cache.enabled else "not configured"
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        redis=redis_status
    )
