"""Application settings loaded from environment variables."""

from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = BACKEND_DIR / "job_automation.db"


class Settings(BaseSettings):
    """Application configuration loaded from .env file or environment variables."""

    model_config = SettingsConfigDict(
        env_file=[str(BACKEND_DIR / ".env"), str(BACKEND_DIR.parent / ".env"), ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AI Job Application Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database: Supports Neon PostgreSQL or local SQLite fallback
    DATABASE_URL: str = f"sqlite:///{DB_FILE.as_posix()}"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if not v or not str(v).strip():
            return f"sqlite:///{DB_FILE.as_posix()}"
        val = str(v).strip()
        # Fix: Render / Neon / Heroku URLs starting with postgres:// instead of postgresql://
        if val.startswith("postgres://"):
            val = val.replace("postgres://", "postgresql://", 1)
        return val

    # Security
    SECRET_KEY: str = "super-secret-key-change-in-production-abc123xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AI / LLM
    ANTHROPIC_API_KEY: str = ""

    # File uploads
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")

    # Default demo user
    DEFAULT_USER_EMAIL: str = "demo@jobbot.com"
    DEFAULT_USER_PASSWORD: str = "password123"


settings = Settings()
