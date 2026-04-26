"""Pytest configuration and fixtures for ClipPilot Lite backend."""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_current_user
from app.config import Settings


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient for the app (no auth override)."""
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table = MagicMock(return_value=MagicMock())
    mock.storage = MagicMock()
    mock.auth = MagicMock()
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.incr = MagicMock(return_value=1)
    mock.expire = MagicMock(return_value=True)
    mock.ping = MagicMock(return_value=True)
    mock.close = MagicMock()
    return mock


@pytest.fixture
def test_settings():
    """Create test settings with defaults, ignoring .env files."""
    return Settings(
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="test-service-role-key",
        SUPABASE_ANON_KEY="test-anon-key",
        ANTHROPIC_API_KEY="test-anthropic-key",
        ELEVENLABS_API_KEY="test-elevenlabs-key",
        DEEPGRAM_API_KEY="test-deepgram-key",
        REDIS_URL="redis://localhost:6379",
        GOOGLE_CLOUD_PROJECT="test-project",
        GCS_BUCKET="test-bucket",
        MAX_VIDEOS_PER_USER=2,
        TESTER_VIDEO_LIMIT=50,
        MAX_VIDEOS_PER_DAY_GLOBAL=20,
        BACKEND_CORS_ORIGINS="http://localhost:3000",
        APP_ENV="testing",
        LOG_LEVEL="INFO",
        _env_file=None,
    )


@pytest.fixture
def authenticated_client(mock_supabase, mock_redis):
    """Create an authenticated test client with dependency overrides."""
    def override_auth():
        return "test-user-id"

    app.dependency_overrides[get_current_user] = override_auth
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
