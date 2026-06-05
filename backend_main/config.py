# backend_main/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application Metadata
    APP_NAME: str = "ML-Powered Vital Diagnosis API"
    APP_VERSION: str = "1.0.0"
    DESCRIPTION: str = "Unified API for ML-powered vital diagnosis across multiple tracks (eICU, Multimorbidity, VitalDB) and the Ensemble layer."
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]  # Restrict in production (e.g., ["http://localhost:3000"])
    
    # Authentication & Security
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEYS: List[str] = ["dev-api-key", "track1-key", "track2-key", "track3-key", "ensemble-key"]
    
    # Track Service URLs (Used for health checks and internal routing)
    TRACK1_URL: str = "http://localhost:8001"
    TRACK2_URL: str = "http://localhost:8002"
    TRACK3_URL: str = "http://localhost:8003"
    ENSEMBLE_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()