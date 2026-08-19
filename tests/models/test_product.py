"""Unit tests for the Product and ProductImage models."""

import pytest
from app.models.product import Product, ProductImage


def test_product_instantiation(app):
    """Test creating a Product instance and verifying fields."""
    product = Product(
        name="Linen Casual Shirt",
        price=39.90,
        stock=15,
        color="White",
        size="Free Size",
        gender="Unisex",
        sku="UQ-LINEN-WHT-01",
        is_active=True
    )

    assert product.name == "Linen Casual Shirt"
    assert product.price == 39.90
    assert product.stock == 15
    assert product.color == "White"
    assert product.size == "Free Size"
    assert product.gender == "Unisex"
    assert product.is_active is True


def test_product_to_dict_method(app):
    """Test Product.to_dict() serialization."""
    product = Product(
        id=10,
        category_id=2,
        name="Selvedge Slim-Fit Jeans",
        description="Premium Japanese denim",
        price=59.90,
        stock=20,
        size="M",
        color="Indigo",
        material="100% Cotton",
        gender="Men",
        sku="UQ-JEAN-IND-01",
        is_active=True
    )

    data = product.to_dict()

    assert data["id"] == 10
    assert data["category_id"] == 2
    assert data["name"] == "Selvedge Slim-Fit Jeans"
    assert data["price"] == 59.90
    assert data["stock"] == 20
    assert data["size"] == "M"
    assert data["gender"] == "Men"
    assert data["sku"] == "UQ-JEAN-IND-01"
    assert data["is_active"] is True


def test_product_image_instantiation_and_to_dict(app):
    """Test ProductImage model creation and to_dict()."""
    image = ProductImage(
        id=5,
        product_id=10,
        image_base64="data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        is_primary=True
    )

    assert image.is_primary is True
    data = image.to_dict()
    assert data["id"] == 5
    assert data["image_base64"] == "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    assert data["is_primary"] is True
