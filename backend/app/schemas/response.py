"""Response schemas for API."""
from pydantic import BaseModel
from typing import Any, Optional


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    database: str
    redis: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str


class SuccessResponse(BaseModel):
    """Generic success response."""
    message: str
    data: Optional[Any] = None
