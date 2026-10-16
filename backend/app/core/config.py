import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "SupportFlow AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supportflow-secret-key-production-ready-secure-salt-48291")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database: Defaults to SQLite for instant local zero-config runs, or PostgreSQL (Neon/Supabase/Render)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./supportflow.db")
    
    # LLM Settings: Gemini API key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_EMBED_MODEL: str = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")
    
    # Human-in-the-loop safety threshold
    HIGH_RISK_REFUND_THRESHOLD: float = 100.0  # Orders/refunds above $100 require human agent approval
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
