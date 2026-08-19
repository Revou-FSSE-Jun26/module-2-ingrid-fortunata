"""Unit tests for Order model."""

import pytest
from app.models.order import Order


def test_order_instantiation(app):
    """Test creating an Order instance and verifying fields."""
    order = Order(
        user_id=1,
        total_amount=120.50,
        status="pending",
        shipping_address="123 Orchard Road, Singapore",
        recipient_name="Alice Smith",
        recipient_phone="+6591234567"
    )

    assert order.user_id == 1
    assert order.total_amount == 120.50
    assert order.status == "pending"
    assert order.recipient_name == "Alice Smith"
    assert order.shipping_address == "123 Orchard Road, Singapore"


def test_order_to_dict_method(app):
    """Test Order.to_dict() serialization."""
    order = Order(
        id=42,
        user_id=2,
        total_amount=89.90,
        status="shipped",
        shipping_address="456 Sunset Boulevard",
        recipient_name="Bob Builder",
        recipient_phone="+1234567890",
        tracking_number="JNE-12345678",
        cancellation_reason=None
    )

    data = order.to_dict()

    assert data["id"] == 42
    assert data["user_id"] == 2
    assert data["total_amount"] == 89.90
    assert data["status"] == "shipped"
    assert data["recipient_name"] == "Bob Builder"
    assert data["tracking_number"] == "JNE-12345678"
    assert data["cancellation_reason"] is None
