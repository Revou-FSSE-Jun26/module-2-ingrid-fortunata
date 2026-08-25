"""Unit tests for Category Marshmallow Schemas."""

import pytest
from marshmallow import ValidationError
from app.schemas.category import (
    CategoryCreateInputSchema,
    CategoryUpdateInputSchema,
    not_blank
)


def test_category_not_blank_validator():
    """Verify not_blank rejects empty strings."""
    with pytest.raises(ValidationError):
        not_blank("")


def test_category_create_schema_valid():
    """Verify valid category creation payload."""
    payload = {"name": "Jackets", "description": "Coats & Jackets", "is_active": True}
    res = CategoryCreateInputSchema().load(payload)
    assert res["name"] == "Jackets"
    assert res["is_active"] is True


def test_category_create_schema_blank_name_fails():
    """Verify category creation rejects blank name."""
    with pytest.raises(ValidationError):
        CategoryCreateInputSchema().load({"name": "   "})


def test_category_update_schema_valid():
    """Verify valid category update payload."""
    payload = {"name": "Outerwear", "description": "New description"}
    res = CategoryUpdateInputSchema().load(payload)
    assert res["name"] == "Outerwear"


def test_category_update_schema_empty_fails():
    """Verify category update rejects empty dictionary."""
    with pytest.raises(ValidationError, match="At least one field must be provided to update."):
        CategoryUpdateInputSchema().load({})
