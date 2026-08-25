"""Unit and integration tests for authentication helper functions in app/auth.py."""

from unittest.mock import patch
import pytest
from flask_jwt_extended import create_access_token
from app.auth import roles_required, get_current_user, is_admin_user
from app.models.user import User


def test_roles_required_user_not_found(client, app):
    """Verify roles_required returns 401 when token has an ID of a non-existent user."""
    with app.app_context():
        token = create_access_token(identity="99999")

    # Access endpoint protected by roles_required (e.g. POST /categories)
    res = client.post('/categories', json={"name": "Ghost Category"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.get_json()["message"] == "User not found."


def test_roles_required_deactivated_user(client, app):
    """Verify roles_required returns 403 when token belongs to a deactivated user."""
    with app.app_context():
        deactivated = User.query.filter_by(username="deactivated_user").first()
        token = create_access_token(identity=str(deactivated.id))

    res = client.post('/categories', json={"name": "Deactivated Category"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert res.get_json()["message"] == "Account is deactivated."


def test_roles_required_missing_identity(client, app):
    """Verify roles_required returns 401 when get_jwt_identity returns None."""
    with app.app_context():
        token = create_access_token(identity="1")

    with patch("app.auth.get_jwt_identity", return_value=None):
        res = client.post('/categories', json={"name": "No Identity"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert res.get_json()["message"] == "Missing or invalid authorization token."


def test_get_current_user_and_is_admin_user_exception_handling(app):
    """Verify get_current_user and is_admin_user gracefully return None/False on exception."""
    with app.test_request_context():
        with patch("app.auth.get_jwt_identity", side_effect=Exception("Context error")):
            assert get_current_user() is None

        with patch("app.auth.verify_jwt_in_request", side_effect=Exception("JWT Error")):
            assert is_admin_user() is False
