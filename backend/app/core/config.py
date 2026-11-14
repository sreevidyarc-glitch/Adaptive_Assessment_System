from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os

class Settings(BaseSettings):
    APP_NAME: str = "AI-Powered Adaptive Assessment System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/adaptive_assessment"
    FALLBACK_SQLITE_URL: str = "sqlite:///./adaptive_assessment.db"

    # Security & Tokens
    JWT_SECRET_KEY: str = "default_insecure_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    FACULTY_TOKEN_EXPIRE_MINUTES: int = 30  # Spec Section 3 line 37: 30 minutes
    STUDENT_TOKEN_EXPIRE_MINUTES: int = 60  # Spec Section 3 line 111: 60 minutes

    # OTP
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    DEV_EXPOSE_OTP_IN_RESPONSE: bool = True

    # AI Integration (Server-side only)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

