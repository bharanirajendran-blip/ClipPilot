"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Load configuration from environment variables."""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # External APIs
    ANTHROPIC_API_KEY: str
    RUNWAY_API_KEY: str = ""  # Optional fallback — Veo is primary
    ELEVENLABS_API_KEY: str
    DEEPGRAM_API_KEY: str

    # Google Cloud / Veo
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GCS_BUCKET: str = ""  # Cloud Storage bucket for Veo output
    VEO_MODEL: str = "veo-2.0-generate-001"
    VIDEO_PROVIDER: str = "veo"  # "veo" or "runway"


    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Rate Limits
    MAX_VIDEOS_PER_USER: int = 2
    TESTER_EMAILS: str = ""
    TESTER_VIDEO_LIMIT: int = 50
    MAX_VIDEOS_PER_DAY_GLOBAL: int = 20

    # Environment
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # API Configuration
    JOB_TIMEOUT_SECONDS: int = 600
    RUNWAY_MODEL: str = "gen3a_turbo"  # Options: gen3a_turbo, gen4.5, kling3.0_pro, veo3, etc.
    RUNWAY_POLL_INTERVAL: int = 5
    RUNWAY_MAX_RETRIES: int = 60

    # Model Parameters
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    ELEVENLABS_MODEL_ID: str = "eleven_turbo_v2_5"

    class Config:
        env_file = ("../.env", ".env")
        case_sensitive = True


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


settings = get_settings()
