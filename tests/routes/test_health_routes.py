"""Tests for API and Database Health Check endpoint (GET /health)."""

from unittest.mock import patch
import pytest


def test_health_check_healthy(client):
    """Verify GET /health returns 200 and healthy status when database is reachable."""
    response = client.get('/health')
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_health_check_unhealthy(client):
    """Verify GET /health returns 503 and unhealthy status when database connection fails."""
    with patch("app.extensions.db.session.execute", side_effect=Exception("Database connection timeout")):
        response = client.get('/health')
        assert response.status_code == 503

        data = response.get_json()
        assert data["status"] == "unhealthy"
        assert "disconnected" in data["database"]
        assert "Database connection timeout" in data["database"]
        assert "timestamp" in data


def test_cors_headers(client):
    """Verify CORS headers are present in response."""
    response = client.get('/health', headers={'Origin': 'http://localhost:3000'})
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:3000'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'

