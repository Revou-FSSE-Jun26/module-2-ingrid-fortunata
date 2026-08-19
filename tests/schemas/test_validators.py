"""Unit tests for standalone validation functions using pytest.raises and message checking."""

import pytest
from marshmallow import ValidationError
from app.schemas.user import not_blank
from app.schemas.product import VALID_SIZES, VALID_GENDERS


def test_not_blank_valid_input():
    """Verify not_blank does not raise exception on valid strings."""
    # Should complete without raising any exception
    not_blank("valid string")
    not_blank("  padded but has content  ")


def test_not_blank_empty_string_raises_exception():
    """Verify not_blank raises ValidationError on empty string."""
    with pytest.raises(ValidationError) as exc_info:
        not_blank("")
    
    assert "Field cannot be blank or whitespace only." in str(exc_info.value)


def test_not_blank_whitespace_only_raises_with_match():
    """Verify not_blank raises ValidationError on spaces with regex match."""
    with pytest.raises(ValidationError, match="Field cannot be blank or whitespace only."):
        not_blank("     \t\n")


def test_not_blank_none_raises():
    """Verify not_blank raises ValidationError when given None or falsy."""
    with pytest.raises(ValidationError):
        not_blank(None)


def test_valid_sizes_and_genders_constants():
    """Verify validation constants are properly configured."""
    assert "Free Size" in VALID_SIZES
    assert "M" in VALID_SIZES
    assert "Unisex" in VALID_GENDERS
    assert "Men" in VALID_GENDERS
