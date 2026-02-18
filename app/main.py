from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import matches_router, predictions_router, history_router, teams_router
from app.database import init_db
import os

# Create FastAPI app
app = FastAPI(
    title="Football Prediction System API",
    description="AI-powered football match prediction system with ML analysis and betting insights",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(teams_router)
app.include_router(matches_router)
app.include_router(predictions_router)
app.include_router(history_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Only initialize if not in test environment
    if os.getenv("TESTING") != "true":
        init_db()


@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "name": "Football Prediction System API",
        "version": "1.0.0",
        "description": "AI-powered football match prediction system",
        "endpoints": {
            "teams": "/teams",
            "matches": "/matches",
            "predictions": "/predictions",
            "history": "/history",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "football-prediction-api"
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
