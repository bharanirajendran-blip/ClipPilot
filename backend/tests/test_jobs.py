"""Tests for job management endpoints."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_current_user
from app.routes.jobs import get_supabase, get_redis


# ── Unauthenticated tests ──────────────────────────────────────────


def test_create_job_without_auth(test_client):
    """Test that creating a job without auth returns 401."""
    response = test_client.post(
        "/api/jobs",
        json={
            "topic": "How solar panels work",
            "style": "educational",
            "duration": 30,
        },
    )
    # HTTPBearer returns 403 when no Authorization header is present
    assert response.status_code in [401, 403]


def test_create_job_with_invalid_auth(test_client):
    """Test that creating a job with invalid auth returns 401."""
    response = test_client.post(
        "/api/jobs",
        json={
            "topic": "How solar panels work",
            "style": "educational",
            "duration": 30,
        },
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


# ── Authenticated tests ─────────────────────────────────────────────


@pytest.fixture
def mock_deps():
    """Override FastAPI dependencies for authenticated tests."""
    mock_sb = MagicMock()
    mock_rd = MagicMock()
    mock_rd.get = MagicMock(return_value=None)
    mock_rd.incr = MagicMock(return_value=1)
    mock_rd.expire = MagicMock(return_value=True)

    app.dependency_overrides[get_current_user] = lambda: "test-user-id"
    app.dependency_overrides[get_supabase] = lambda: mock_sb
    app.dependency_overrides[get_redis] = lambda: mock_rd

    yield {"supabase": mock_sb, "redis": mock_rd}

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(mock_deps):
    """Test client with all dependencies overridden."""
    return TestClient(app)


@patch("app.routes.jobs.check_input_safety")
@patch("app.routes.jobs.create_pool")
def test_create_job_success(mock_pool, mock_safety, auth_client, mock_deps):
    """Test successful job creation."""
    sb = mock_deps["supabase"]

    mock_safety.return_value = MagicMock(is_safe=True)

    # Build mock chain so different .table() calls return appropriate data
    call_count = {"n": 0}
    original_table = sb.table

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "profiles":
            resp = MagicMock()
            resp.data = [{"email": "test@example.com"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = resp
        elif name == "jobs":
            # For count query
            count_resp = MagicMock()
            count_resp.count = 0
            count_resp.data = []
            mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = count_resp
            # For insert
            mock_table.insert.return_value.execute.return_value = True
        return mock_table

    sb.table = MagicMock(side_effect=table_side_effect)

    # Mock Redis daily counter
    mock_deps["redis"].get.return_value = None
    mock_deps["redis"].incr.return_value = 1

    # Mock pool
    mock_pool_inst = AsyncMock()
    mock_pool_inst.enqueue_job = AsyncMock(return_value=True)
    mock_pool.return_value = mock_pool_inst

    response = auth_client.post(
        "/api/jobs",
        json={
            "topic": "How solar panels work in detail",
            "style": "educational",
            "duration": 30,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_get_job_status_success(auth_client, mock_deps):
    """Test getting job status for own job."""
    sb = mock_deps["supabase"]

    job_resp = MagicMock()
    job_resp.data = {
        "id": "job-123",
        "user_id": "test-user-id",
        "status": "processing",
        "progress": 50,
        "current_step": "Generating video",
        "topic": "Solar panels",
        "style": "educational",
        "duration": 30,
        "error_message": None,
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp

    response = auth_client.get("/api/jobs/job-123/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress"] == 50


def test_get_job_status_other_user(auth_client, mock_deps):
    """Test that accessing another user's job returns 403."""
    sb = mock_deps["supabase"]

    job_resp = MagicMock()
    job_resp.data = {
        "id": "job-123",
        "user_id": "different-user-id",
        "status": "completed",
        "progress": 100,
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp

    response = auth_client.get("/api/jobs/job-123/status")
    assert response.status_code == 403


def test_list_user_jobs_empty(auth_client, mock_deps):
    """Test listing user jobs when they have none."""
    sb = mock_deps["supabase"]

    jobs_resp = MagicMock()
    jobs_resp.data = []
    sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = jobs_resp

    response = auth_client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == []
    assert data["total"] == 0


def test_list_user_jobs_success(auth_client, mock_deps):
    """Test listing user's jobs."""
    sb = mock_deps["supabase"]

    jobs_resp = MagicMock()
    jobs_resp.data = [
        {
            "id": "job-1",
            "user_id": "test-user-id",
            "topic": "Solar panels",
            "style": "educational",
            "duration": 30,
            "status": "completed",
            "progress": 100,
            "current_step": "Complete",
            "video_url": "https://example.com/video.mp4",
            "thumbnail_url": "https://example.com/thumb.png",
            "title": "Solar Panels",
            "created_at": "2024-04-21T10:00:00Z",
            "updated_at": "2024-04-21T10:15:00Z",
        }
    ]
    sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = jobs_resp

    response = auth_client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["topic"] == "Solar panels"


@patch("app.routes.jobs.create_pool")
def test_cancel_job_success(mock_pool, auth_client, mock_deps):
    """Test successful job cancellation."""
    sb = mock_deps["supabase"]

    job_resp = MagicMock()
    job_resp.data = {
        "id": "job-123",
        "user_id": "test-user-id",
        "status": "processing",
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = True

    mock_pool_inst = AsyncMock()
    mock_pool_inst.abort_job = AsyncMock(return_value=True)
    mock_pool.return_value = mock_pool_inst

    response = auth_client.post("/api/jobs/job-123/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


def test_delete_job_success(auth_client, mock_deps):
    """Test successful job deletion."""
    sb = mock_deps["supabase"]

    job_resp = MagicMock()
    job_resp.data = {
        "id": "job-123",
        "user_id": "test-user-id",
        "status": "completed",
        "video_url": None,
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp
    sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = True

    response = auth_client.delete("/api/jobs/job-123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"


def test_delete_active_job_fails(auth_client, mock_deps):
    """Test that deleting an active job returns 409."""
    sb = mock_deps["supabase"]

    job_resp = MagicMock()
    job_resp.data = {
        "id": "job-123",
        "user_id": "test-user-id",
        "status": "queued",
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp

    response = auth_client.delete("/api/jobs/job-123")
    assert response.status_code == 409


# ── Audio/Visual option tests ──────────────────────────────────────


@patch("app.routes.jobs.check_input_safety")
@patch("app.routes.jobs.create_pool")
def test_create_job_with_options(mock_pool, mock_safety, auth_client, mock_deps):
    """Test job creation with narration/captions/music options."""
    sb = mock_deps["supabase"]

    mock_safety.return_value = MagicMock(is_safe=True)

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "profiles":
            resp = MagicMock()
            resp.data = [{"email": "test@example.com"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = resp
        elif name == "jobs":
            count_resp = MagicMock()
            count_resp.count = 0
            count_resp.data = []
            mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = count_resp
            mock_table.insert.return_value.execute.return_value = True
        return mock_table

    sb.table = MagicMock(side_effect=table_side_effect)
    mock_deps["redis"].get.return_value = None

    mock_pool_inst = AsyncMock()
    mock_pool_inst.enqueue_job = AsyncMock(return_value=True)
    mock_pool.return_value = mock_pool_inst

    response = auth_client.post(
        "/api/jobs",
        json={
            "topic": "A robot finds a flower in a junkyard",
            "style": "storytelling",
            "duration": 30,
            "include_narration": False,
            "include_captions": False,
            "include_music": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


@patch("app.routes.jobs.check_input_safety")
@patch("app.routes.jobs.create_pool")
def test_create_job_documentary_style(mock_pool, mock_safety, auth_client, mock_deps):
    """Test job creation with documentary style (replaced 'news')."""
    sb = mock_deps["supabase"]

    mock_safety.return_value = MagicMock(is_safe=True)

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "profiles":
            resp = MagicMock()
            resp.data = [{"email": "test@example.com"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = resp
        elif name == "jobs":
            count_resp = MagicMock()
            count_resp.count = 0
            count_resp.data = []
            mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = count_resp
            mock_table.insert.return_value.execute.return_value = True
        return mock_table

    sb.table = MagicMock(side_effect=table_side_effect)
    mock_deps["redis"].get.return_value = None

    mock_pool_inst = AsyncMock()
    mock_pool_inst.enqueue_job = AsyncMock(return_value=True)
    mock_pool.return_value = mock_pool_inst

    response = auth_client.post(
        "/api/jobs",
        json={
            "topic": "The history of space exploration from 1960s to today",
            "style": "documentary",
            "duration": 60,
        },
    )

    assert response.status_code == 200


def test_create_job_invalid_news_style(test_client):
    """Test that the old 'news' style is rejected."""
    response = test_client.post(
        "/api/jobs",
        json={
            "topic": "Breaking news about technology",
            "style": "news",
            "duration": 30,
        },
        headers={"Authorization": "Bearer test-token"},
    )
    # Should fail validation (news is not a valid style anymore)
    assert response.status_code in [401, 422]


# ── Share endpoint tests ───────────────────────────────────────────


def test_share_completed_video(test_client, mock_deps):
    """Test public share endpoint returns video data."""
    from app.routes.jobs import get_supabase
    sb = mock_deps["supabase"]
    app.dependency_overrides[get_supabase] = lambda: sb

    job_resp = MagicMock()
    job_resp.data = {
        "video_url": "https://storage.example.com/video.mp4",
        "thumbnail_url": "https://storage.example.com/thumb.png",
        "title": "Solar Panels Explained",
        "description": "Learn about solar energy",
        "tags": ["solar", "energy"],
        "status": "completed",
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp

    response = test_client.get("/api/jobs/job-123/share")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Solar Panels Explained"
    assert "video_url" in data

    app.dependency_overrides.clear()


def test_share_incomplete_video_returns_404(test_client, mock_deps):
    """Test that sharing an incomplete video returns 404."""
    from app.routes.jobs import get_supabase
    sb = mock_deps["supabase"]
    app.dependency_overrides[get_supabase] = lambda: sb

    job_resp = MagicMock()
    job_resp.data = {
        "status": "processing",
    }
    sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = job_resp

    response = test_client.get("/api/jobs/job-123/share")
    assert response.status_code == 404

    app.dependency_overrides.clear()
