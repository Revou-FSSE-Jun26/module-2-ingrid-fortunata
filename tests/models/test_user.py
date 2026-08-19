"""Unit tests for the User model."""

import pytest
from app.models.user import User


def test_user_instantiation(app):
    """Test creating a User instance and inspecting properties."""
    user = User(
        username="pytest_user",
        email="pytest_user@example.com",
        password_hash="hashed_secret_123",
        role="customer",
        is_active=True
    )

    assert user.username == "pytest_user"
    assert user.email == "pytest_user@example.com"
    assert user.password_hash == "hashed_secret_123"
    assert user.role == "customer"
    assert user.is_active is True


def test_user_to_dict_method(app):
    """Test the to_dict() serialization method on the User model."""
    user = User(
        id=999,
        username="dict_user",
        email="dict@example.com",
        password_hash="hashed_pw",
        role="admin",
        is_active=False
    )

    user_dict = user.to_dict()

    assert isinstance(user_dict, dict)
    assert user_dict["id"] == 999
    assert user_dict["username"] == "dict_user"
    assert user_dict["email"] == "dict@example.com"
    assert user_dict["role"] == "admin"
    assert user_dict["is_active"] is False
    # Ensure sensitive fields like password_hash are NEVER exposed in to_dict()
    assert "password_hash" not in user_dict
    assert "password" not in user_dict
