"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://football_user:football_pass@db:5432/football_db"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # API Keys
    football_api_key: Optional[str] = None
    football_api_base_url: str = "https://v3.football.api-sports.io"
    football_data_token: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: str = ["http://localhost:3000", "http://localhost:8000"]
    
    # Application
    app_name: str = "Football Prediction API"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        extra = "allow"  # ← 重要！允許額外欄位

settings = Settings()