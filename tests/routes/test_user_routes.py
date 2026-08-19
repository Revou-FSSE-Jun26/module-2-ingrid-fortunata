"""Integration tests for User routes (/users)."""

import pytest
import uuid
from app.extensions import db
from app.models.user import User


def test_register_user_success(client):
    """Verify user registration succeeds with 201 Created and customer role."""
    unique_suffix = uuid.uuid4().hex[:6]
    payload = {
        "username": f"user_{unique_suffix}",
        "email": f"user_{unique_suffix}@example.com",
        "password": "validpassword123"
    }

    response = client.post('/users', json=payload)
    assert response.status_code == 201

    data = response.get_json()["data"]
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["role"] == "customer"
    assert data["is_active"] is True


def test_register_user_duplicate_username_fails(client):
    """Verify registering an existing username returns 409 Conflict."""
    payload = {
        "username": "alice_smith",
        "email": "alice_duplicate@example.com",
        "password": "password123"
    }

    response = client.post('/users', json=payload)
    assert response.status_code == 409

    data = response.get_json()
    assert data["error_code"] == "USER_NAME_CONFLICT"


def test_get_user_by_id_unauthorized(client):
    """Verify accessing /users/<id> without JWT returns 401 Unauthorized."""
    response = client.get('/users/1')
    assert response.status_code == 401


def test_get_user_by_id_authorized(client, customer_headers):
    """Verify customer can access their own profile."""
    # Alice Smith has ID 2 in seed data
    user = User.query.filter_by(username="alice_smith").first()
    assert user is not None

    response = client.get(f'/users/{user.id}', headers=customer_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["username"] == "alice_smith"
