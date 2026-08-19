"""Integration tests for Authentication routes (/auth/login)."""

import pytest


def test_login_success_with_username(client):
    """Verify login succeeds with valid username and password."""
    payload = {
        "username": "alice_smith",
        "password": "alice_password"
    }
    response = client.post('/auth/login', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "token" in data["data"]
    assert data["data"]["user"]["username"] == "alice_smith"
    assert data["data"]["user"]["is_active"] is True


def test_login_success_with_email(client):
    """Verify login succeeds with valid email."""
    payload = {
        "email": "alice@example.com",
        "password": "alice_password"
    }
    response = client.post('/auth/login', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "token" in data["data"]
    assert data["data"]["user"]["email"] == "alice@example.com"


def test_login_fails_wrong_password(client):
    """Verify login returns 401 when given an incorrect password."""
    payload = {
        "username": "alice_smith",
        "password": "definitely_wrong_password"
    }
    response = client.post('/auth/login', json=payload)
    assert response.status_code == 401
    
    data = response.get_json()
    assert data["error_code"] == "USER_UNAUTHORIZED"


def test_login_fails_deactivated_user(client):
    """Verify login returns 401 for deactivated users to avoid account enumeration."""
    payload = {
        "username": "deactivated_user",
        "password": "deactivated_password"
    }
    response = client.post('/auth/login', json=payload)
    assert response.status_code == 401
    
    data = response.get_json()
    assert data["error_code"] == "USER_UNAUTHORIZED"


def test_login_validation_missing_identity(client):
    """Verify login returns 422 when neither username nor email is provided."""
    payload = {
        "password": "some_password"
    }
    response = client.post('/auth/login', json=payload)
    assert response.status_code == 422
    
    data = response.get_json()
    assert data["error_code"] == "VALIDATION_ERROR"
