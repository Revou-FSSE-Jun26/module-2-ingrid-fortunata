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


# ==============================================================================
# PUT /users/<id> Tests
# ==============================================================================

def test_update_user_customer_own_profile_success(client):
    """Customer can update their own username and email."""
    from werkzeug.security import generate_password_hash
    unique_suffix = uuid.uuid4().hex[:6]
    test_cust = User(
        username=f"cust_{unique_suffix}",
        email=f"cust_{unique_suffix}@example.com",
        password_hash=generate_password_hash("cust_password123"),
        role="customer",
        is_active=True
    )
    db.session.add(test_cust)
    db.session.commit()

    login_res = client.post('/auth/login', json={"username": test_cust.username, "password": "cust_password123"})
    token = login_res.get_json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "username": f"updated_{unique_suffix}",
        "email": f"updated_{unique_suffix}@example.com"
    }

    response = client.put(f'/users/{test_cust.id}', json=payload, headers=headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]



def test_update_user_customer_forbidden_other_profile(client, customer_headers):
    """Customer cannot update another user's profile (e.g. ID 1)."""
    payload = {"username": "hacked_admin"}
    response = client.put('/users/1', json=payload, headers=customer_headers)
    assert response.status_code == 403
    assert response.get_json()["error_code"] == "USER_FORBIDDEN"


def test_update_user_customer_forbidden_role_escalation(client, customer_headers):
    """Customer cannot update their role or active status."""
    user = User.query.filter_by(username="alice_smith").first()
    assert user is not None

    payload = {"role": "superadmin"}
    response = client.put(f'/users/{user.id}', json=payload, headers=customer_headers)
    assert response.status_code == 403
    assert response.get_json()["error_code"] == "USER_FORBIDDEN"


def test_update_user_customer_forbidden_is_active(client, customer_headers):
    """Customer cannot modify is_active field."""
    user = User.query.filter_by(username="alice_smith").first()
    assert user is not None

    payload = {"is_active": False}
    response = client.put(f'/users/{user.id}', json=payload, headers=customer_headers)
    assert response.status_code == 403
    assert response.get_json()["error_code"] == "USER_FORBIDDEN"


def test_update_user_deactivated_forbidden(client):
    """Deactivated user cannot update profile."""
    # Seeded deactivated user
    deactivated = User.query.filter_by(username="deactivated_user").first()
    assert deactivated is not None

    # Generate token directly for deactivated user to test endpoint guard
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=str(deactivated.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(f'/users/{deactivated.id}', json={"username": "new_name"}, headers=headers)
    assert response.status_code == 403
    assert response.get_json()["error_code"] == "USER_DEACTIVATED"



def test_update_user_superadmin_can_update_role_and_is_active(client, superadmin_headers):
    """Superadmin can update any user's role and is_active status."""
    # Create a dummy user to update
    unique_suffix = uuid.uuid4().hex[:6]
    test_user = User(
        username=f"target_{unique_suffix}",
        email=f"target_{unique_suffix}@example.com",
        password_hash="dummy_hash",
        role="customer",
        is_active=True
    )
    db.session.add(test_user)
    db.session.commit()

    payload = {
        "role": "admin",
        "is_active": False
    }

    response = client.put(f'/users/{test_user.id}', json=payload, headers=superadmin_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["role"] == "admin"
    assert data["is_active"] is False


def test_update_user_duplicate_username_conflict(client, superadmin_headers):
    """Updating username to an existing username returns 409 Conflict."""
    superadmin = User.query.filter_by(username="superadmin_user").first()
    admin = User.query.filter_by(username="admin_user").first()

    payload = {"username": admin.username}
    response = client.put(f'/users/{superadmin.id}', json=payload, headers=superadmin_headers)
    assert response.status_code == 409
    assert response.get_json()["error_code"] == "USER_NAME_CONFLICT"


def test_update_user_duplicate_email_conflict(client, superadmin_headers):
    """Updating email to an existing email returns 409 Conflict."""
    superadmin = User.query.filter_by(username="superadmin_user").first()
    admin = User.query.filter_by(username="admin_user").first()

    payload = {"email": admin.email}
    response = client.put(f'/users/{superadmin.id}', json=payload, headers=superadmin_headers)
    assert response.status_code == 409
    assert response.get_json()["error_code"] == "USER_EMAIL_CONFLICT"


def test_update_user_not_found(client, superadmin_headers):
    """Updating non-existent user returns 404 Not Found."""
    response = client.put('/users/99999', json={"username": "nobody"}, headers=superadmin_headers)
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "USER_NOT_FOUND"


def test_update_user_empty_payload_validation_error(client, superadmin_headers):
    """Updating with empty body returns 422 Validation Error."""
    user = User.query.filter_by(username="superadmin_user").first()
    response = client.put(f'/users/{user.id}', json={}, headers=superadmin_headers)
    assert response.status_code == 422
    assert response.get_json()["error_code"] == "VALIDATION_ERROR"


# ==============================================================================
# GET /users Tests
# ==============================================================================

def test_get_all_users_unauthorized(client):
    """GET /users without token returns 401 Unauthorized."""
    response = client.get('/users')
    assert response.status_code == 401


def test_get_all_users_forbidden_for_customer(client, customer_headers):
    """GET /users with customer token returns 403 Forbidden."""
    response = client.get('/users', headers=customer_headers)
    assert response.status_code == 403
    assert response.get_json()["error_code"] == "FORBIDDEN"


def test_get_all_users_forbidden_for_admin(client, admin_headers):
    """GET /users with admin token returns 403 Forbidden (restricted to superadmin)."""
    response = client.get('/users', headers=admin_headers)
    assert response.status_code == 403
    assert response.get_json()["error_code"] == "FORBIDDEN"


def test_get_all_users_superadmin_success(client, superadmin_headers):
    """GET /users with superadmin token returns 200 with list of users."""
    response = client.get('/users', headers=superadmin_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 3
    # Check that password_hash is not returned in user schemas
    assert "password_hash" not in data[0]
    assert "id" in data[0]
    assert "username" in data[0]
    assert "role" in data[0]


def test_get_all_users_filter_role(client, superadmin_headers):
    """GET /users?role=admin filters users by role."""
    response = client.get('/users?role=admin', headers=superadmin_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    for u in data:
        assert u["role"] == "admin"


def test_get_all_users_filter_is_active(client, superadmin_headers):
    """GET /users?is_active=false filters users by active status."""
    response = client.get('/users?is_active=false', headers=superadmin_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    for u in data:
        assert u["is_active"] is False


def test_get_all_users_search(client, superadmin_headers):
    """GET /users?search=superadmin searches by username or email."""
    response = client.get('/users?search=superadmin', headers=superadmin_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert len(data) >= 1
    assert "superadmin" in data[0]["username"]


def test_get_all_users_pagination(client, superadmin_headers):
    """GET /users?page=1&per_page=2 limits returned records."""
    response = client.get('/users?page=1&per_page=2', headers=superadmin_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert len(data) <= 2

