"""Unit tests for Product Marshmallow Schemas and validation rules."""

import pytest
from marshmallow import ValidationError
from app.schemas.product import (
    ProductCreateInputSchema,
    ProductUpdateInputSchema,
    ProductImageInputSchema,
    not_blank
)


def test_product_not_blank_validator():
    """Verify not_blank rejects empty strings."""
    with pytest.raises(ValidationError):
        not_blank("   ")


def test_product_create_schema_valid_payload():
    """Verify valid product creation payload passes schema validation."""
    schema = ProductCreateInputSchema()
    payload = {
        "name": "Classic Oxford Shirt",
        "price": 35.0,
        "stock": 10,
        "color": "Light Blue"
    }

    result = schema.load(payload)
    assert result["name"] == "Classic Oxford Shirt"
    assert result["price"] == 35.0
    assert result["stock"] == 10
    assert result["color"] == "Light Blue"
    # Verify defaults are populated
    assert result["size"] == "Free Size"
    assert result["gender"] == "Unisex"
    assert result["is_active"] is True


def test_product_create_schema_negative_price_raises():
    """Verify price <= 0 raises ValidationError with exact message."""
    schema = ProductCreateInputSchema()
    payload = {
        "name": "Invalid Price Item",
        "price": -10.0,
        "stock": 5,
        "color": "Black"
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "price" in errors
    assert "Price must be greater than zero." in errors["price"]


def test_product_create_schema_negative_stock_raises():
    """Verify stock < 0 raises ValidationError with exact message."""
    schema = ProductCreateInputSchema()
    payload = {
        "name": "Invalid Stock Item",
        "price": 15.0,
        "stock": -1,
        "color": "Red"
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "stock" in errors
    assert "Stock cannot be negative." in errors["stock"]


def test_product_create_schema_more_than_three_images_raises():
    """Verify exceeding maximum 3 images raises ValidationError."""
    schema = ProductCreateInputSchema()
    payload = {
        "name": "Multi Image Shirt",
        "price": 20.0,
        "stock": 10,
        "color": "White",
        "images": [
            {"image_base64": "img1"},
            {"image_base64": "img2"},
            {"image_base64": "img3"},
            {"image_base64": "img4"}
        ]
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "images" in errors
    assert "A product can have at most 3 images." in errors["images"]


def test_product_create_schema_multiple_primaries_raises():
    """Verify having more than 1 primary image raises ValidationError."""
    schema = ProductCreateInputSchema()
    payload = {
        "name": "Multi Primary Shirt",
        "price": 20.0,
        "stock": 10,
        "color": "White",
        "images": [
            {"image_base64": "img1", "is_primary": True},
            {"image_base64": "img2", "is_primary": True}
        ]
    }

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    assert "Exactly one image can be flagged as primary." in exc_info.value.messages["images"]


def test_product_update_schema_validation_branches():
    """Verify ProductUpdateInputSchema validation rules."""
    schema = ProductUpdateInputSchema()

    # Empty payload
    with pytest.raises(ValidationError, match="At least one field must be provided"):
        schema.load({})

    # Negative price
    with pytest.raises(ValidationError):
        schema.load({"price": -5.0})

    # Negative stock
    with pytest.raises(ValidationError):
        schema.load({"stock": -1})

    # More than 3 images
    with pytest.raises(ValidationError):
        schema.load({"images": [{"image_base64": "1"}, {"image_base64": "2"}, {"image_base64": "3"}, {"image_base64": "4"}]})

    # Multiple primaries
    with pytest.raises(ValidationError):
        schema.load({"images": [{"image_base64": "1", "is_primary": True}, {"image_base64": "2", "is_primary": True}]})

    # Valid partial
    res = schema.load({"name": "New Valid Name"})
    assert res["name"] == "New Valid Name"


def test_product_image_size_limit_raises():
    """Verify image larger than 1.5MB Base64 raises ValidationError."""
    schema = ProductImageInputSchema()
    huge_base64 = "a" * 1500001
    payload = {"image_base64": huge_base64}

    with pytest.raises(ValidationError) as exc_info:
        schema.load(payload)

    errors = exc_info.value.messages
    assert "image_base64" in errors
    assert "Image size exceeds the 1MB limit." in errors["image_base64"]
