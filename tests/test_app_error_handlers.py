"""Tests for global HTTP error handlers and application index in app/__init__.py."""

from datetime import timedelta
import pytest
from flask_jwt_extended import create_access_token
from app.config import Config
from app import create_app


def test_index_endpoint(client):
    """Verify GET / returns application information."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "RevoFashion API"
    assert data["status"] == "online"


def test_400_bad_request_handler(client):
    """Verify sending malformed JSON triggers 400 global handler."""
    response = client.post('/users', data="{invalid json...", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["error_code"] == "BAD_REQUEST"


def test_404_not_found_handler(client):
    """Verify accessing an unknown endpoint triggers 404 global handler."""
    response = client.get('/non-existent-api-endpoint')
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "NOT_FOUND"


def test_405_method_not_allowed_handler(client):
    """Verify calling an unpermitted method triggers 405 global handler."""
    response = client.delete('/')
    assert response.status_code == 405
    assert response.get_json()["error_code"] == "METHOD_NOT_ALLOWED"


def test_500_internal_error_handler(app):
    """Verify unhandled exception handler returns 500."""
    with app.test_request_context():
        handler = list(app.error_handler_spec[None][500].values())[0]
        res, code = handler(Exception("Forced server error"))
        assert code == 500
        assert res.get_json()["error_code"] == "INTERNAL_SERVER_ERROR"


def test_jwt_expired_token_handler(client, app):
    """Verify expired JWT triggers expired_token_callback."""
    with app.app_context():
        # Create token that expired 1 hour ago
        token = create_access_token(identity="1", expires_delta=timedelta(seconds=-3600))

    response = client.get('/orders', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.get_json()["error_code"] == "TOKEN_EXPIRED"


def test_jwt_invalid_token_handler(client):
    """Verify invalid JWT string triggers invalid_token_callback."""
    response = client.get('/orders', headers={"Authorization": "Bearer invalid.fake.token"})
    assert response.status_code == 401
    assert response.get_json()["error_code"] == "TOKEN_INVALID"


def test_create_app_with_config_class():
    """Verify create_app works when initialized with Config class."""
    custom_app = create_app(Config)
    assert custom_app is not None
