"""Unit tests for User Marshmallow Schemas."""

import pytest
from marshmallow import ValidationError
from app.schemas.user import (
    UserRegisterInputSchema,
    UserLoginInputSchema,
    UserSchema
)


def test_user_register_schema_success():
    """Verify valid user registration payload passes schema validation."""
    schema = UserRegisterInputSchema()
    payload = {
        "username": "valid_user",
        "email": "user@example.com",
        "password": "strong_password123"
    }

    result = schema.load(payload)
    assert result["username"] == "valid_user"
    assert result["email"] == "user@example.com"
    assert result["password"] == "strong_password123"


def test_user_register_schema_rejects_spaces_in_username():
    """Verify username with spaces raises ValidationError with specific error message."""
    schema = UserRegisterInputSchema()
    payload = {
        "username": "user name with spaces",
        "email": "user@example.com",
        "password": "validpassword123"
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "username" in errors
    assert "Username cannot contain spaces." in errors["username"]


def test_user_register_schema_rejects_short_password():
    """Verify password shorter than 6 chars raises ValidationError."""
    schema = UserRegisterInputSchema()
    payload = {
        "username": "user123",
        "email": "user@example.com",
        "password": "123"
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "password" in errors


def test_user_login_schema_missing_identity_raises():
    """Verify missing both username and email raises identity validation error."""
    schema = UserLoginInputSchema()
    payload = {
        "password": "mypassword"
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "identity" in errors
    assert "Either 'username' or 'email' must be provided." in errors["identity"]


def test_user_login_schema_valid_with_username_or_email():
    """Verify login schema succeeds with either username or email."""
    schema = UserLoginInputSchema()
    
    res1 = schema.load({"username": "alice", "password": "pw"})
    assert res1["username"] == "alice"

    res2 = schema.load({"email": "alice@example.com", "password": "pw"})
    assert res2["email"] == "alice@example.com"


def test_user_update_schema_success():
    """Verify valid update payloads pass schema validation."""
    from app.schemas.user import UserUpdateInputSchema
    schema = UserUpdateInputSchema()

    res = schema.load({"username": "new_name", "email": "new@example.com", "role": "admin", "is_active": False})
    assert res["username"] == "new_name"
    assert res["email"] == "new@example.com"
    assert res["role"] == "admin"
    assert res["is_active"] is False


def test_user_update_schema_empty_payload_raises():
    """Verify empty dictionary raises ValidationError requiring at least one field."""
    from app.schemas.user import UserUpdateInputSchema
    schema = UserUpdateInputSchema()

    with pytest.raises(ValidationError) as exc_info:
        schema.load({})

    errors = exc_info.value.messages
    assert "_schema" in errors
    assert "At least one field must be provided to update." in errors["_schema"]


def test_user_update_schema_invalid_role_raises():
    """Verify invalid role string raises ValidationError."""
    from app.schemas.user import UserUpdateInputSchema
    schema = UserUpdateInputSchema()

    with pytest.raises(ValidationError) as exc_info:
        schema.load({"role": "super_manager"})

    errors = exc_info.value.messages
    assert "role" in errors
    assert "Invalid role" in errors["role"][0]


def test_user_update_schema_username_with_spaces_raises():
    """Verify username with spaces raises ValidationError."""
    from app.schemas.user import UserUpdateInputSchema
    schema = UserUpdateInputSchema()

    with pytest.raises(ValidationError) as exc_info:
        schema.load({"username": "bad name"})

    errors = exc_info.value.messages
    assert "username" in errors
    assert "Username cannot contain spaces." in errors["username"]

