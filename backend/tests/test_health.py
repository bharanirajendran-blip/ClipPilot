"""Tests for health check endpoint."""

import pytest


def test_health_check_returns_200(test_client):
    """Test that health endpoint returns 200 with expected JSON."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


def test_health_check_response_structure(test_client):
    """Test that health response has expected fields."""
    response = test_client.get("/health")

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
