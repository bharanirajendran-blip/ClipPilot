"""Tests for application configuration."""

import pytest
from app.config import Settings


def test_settings_instantiation_with_env_vars(test_settings):
    """Test that Settings can be instantiated with environment variables."""
    assert test_settings.SUPABASE_URL == "https://test.supabase.co"
    assert test_settings.SUPABASE_SERVICE_ROLE_KEY == "test-service-role-key"
    assert test_settings.ANTHROPIC_API_KEY == "test-anthropic-key"


def test_settings_defaults(test_settings):
    """Test that default values are correct."""
    assert test_settings.MAX_VIDEOS_PER_USER == 2
    assert test_settings.TESTER_VIDEO_LIMIT == 50
    assert test_settings.MAX_VIDEOS_PER_DAY_GLOBAL == 20
    assert test_settings.REDIS_URL == "redis://localhost:6379"
    assert test_settings.APP_ENV == "testing"
    assert test_settings.LOG_LEVEL == "INFO"


def test_settings_required_fields(monkeypatch):
    """Test that required fields are enforced."""
    # Clear env vars that could leak from .env
    for key in ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY",
                "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "DEEPGRAM_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(Exception):
        Settings(
            SUPABASE_URL="https://test.supabase.co",
            # Missing SUPABASE_SERVICE_ROLE_KEY and other required fields
            _env_file=None,
        )


def test_settings_optional_fields():
    """Test that optional fields have sensible defaults."""
    settings = Settings(
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="key",
        SUPABASE_ANON_KEY="key",
        ANTHROPIC_API_KEY="key",
        ELEVENLABS_API_KEY="key",
        DEEPGRAM_API_KEY="key",
        _env_file=None,
    )
    assert settings.RUNWAY_API_KEY == ""


def test_settings_video_limits(test_settings):
    """Test that video limit settings are correctly configured."""
    assert test_settings.MAX_VIDEOS_PER_USER > 0
    assert test_settings.TESTER_VIDEO_LIMIT > test_settings.MAX_VIDEOS_PER_USER
    assert test_settings.MAX_VIDEOS_PER_DAY_GLOBAL > 0


def test_settings_cors_origins(test_settings):
    """Test that CORS origins can be parsed."""
    origins = test_settings.BACKEND_CORS_ORIGINS.split(",")
    assert len(origins) > 0
    assert "http://localhost:3000" in origins


def test_settings_model_config(test_settings):
    """Test that Settings can be instantiated as expected."""
    assert hasattr(test_settings, "Config")
    # Verify key environment variables are present
    assert test_settings.SUPABASE_URL
    assert test_settings.ANTHROPIC_API_KEY
    assert test_settings.ELEVENLABS_API_KEY
