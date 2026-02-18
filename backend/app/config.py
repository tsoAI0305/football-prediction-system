"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://football_user:football_pass@localhost:5432/football_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "llama-3.1-70b-versatile"
    
    # API
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-to-random-secret-key"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
