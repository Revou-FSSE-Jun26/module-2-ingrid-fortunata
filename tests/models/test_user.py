"""Unit tests for the User model."""

from unittest.mock import patch
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


def test_user_password_methods():
    """Test set_password and check_password with hashed and plaintext fallback."""
    user = User(username="hash_user", email="hash@example.com")
    user.set_password("mypassword123")

    assert user.check_password("mypassword123") is True
    assert user.check_password("wrongpassword") is False

    # Plaintext fallback check
    user_plain = User(username="plain_user", email="plain@example.com", password_hash="plaintext_pass")
    assert user_plain.check_password("plaintext_pass") is True
    assert user_plain.check_password("other") is False

    # Malformed hash ValueError fallback
    with patch("app.models.user.check_password_hash", side_effect=ValueError("bad")):
        user_bad = User(username="bad", email="bad@example.com", password_hash="pbkdf2:hash")
        assert user_bad.check_password("anything") is False
