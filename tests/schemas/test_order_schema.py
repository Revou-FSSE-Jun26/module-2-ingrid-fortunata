"""Unit tests for Order Marshmallow Schemas."""

import pytest
from marshmallow import ValidationError
from app.schemas.order import (
    OrderItemInputSchema,
    OrderCreateInputSchema,
    OrderUpdateStatusSchema,
    OrderCancelInputSchema,
    not_blank
)


def test_order_not_blank_validator():
    """Verify not_blank rejects empty or whitespace-only strings."""
    with pytest.raises(ValidationError, match="Field cannot be blank or whitespace only."):
        not_blank("   ")


def test_order_item_schema_valid():
    """Verify valid order item schema loading."""
    payload = {"product_id": 1, "quantity": 3, "size": "M", "color": "Black"}
    result = OrderItemInputSchema().load(payload)
    assert result["product_id"] == 1
    assert result["quantity"] == 3
    assert result["size"] == "M"
    assert result["color"] == "Black"


def test_order_item_schema_invalid_quantity():
    """Verify order item schema rejects zero or negative quantities."""
    with pytest.raises(ValidationError):
        OrderItemInputSchema().load({"product_id": 1, "quantity": 0})

    with pytest.raises(ValidationError):
        OrderItemInputSchema().load({"product_id": 1, "quantity": -5})


def test_order_item_schema_invalid_size():
    """Verify order item schema rejects invalid clothing sizes."""
    with pytest.raises(ValidationError):
        OrderItemInputSchema().load({"product_id": 1, "quantity": 1, "size": "INVALID_SIZE"})


def test_order_create_schema_valid():
    """Verify valid order creation schema payload."""
    payload = {
        "shipping_address": "123 Orchard Road, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+65 9123-4567",
        "items": [
            {"product_id": 1, "quantity": 2, "size": "M", "color": "White"},
            {"product_id": 2, "quantity": 1}
        ]
    }
    result = OrderCreateInputSchema().load(payload)
    assert len(result["items"]) == 2
    assert result["recipient_name"] == "Alice Smith"


def test_order_create_schema_empty_items():
    """Verify schema rejects order with empty items list."""
    payload = {
        "shipping_address": "123 Orchard Road",
        "recipient_name": "Alice",
        "recipient_phone": "+6591234567",
        "items": []
    }
    with pytest.raises(ValidationError, match="Order must contain at least one item."):
        OrderCreateInputSchema().load(payload)


def test_order_create_schema_duplicate_product_ids():
    """Verify schema rejects duplicate product_ids in the same order."""
    payload = {
        "shipping_address": "123 Orchard Road",
        "recipient_name": "Alice",
        "recipient_phone": "+6591234567",
        "items": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 1, "quantity": 2}
        ]
    }
    with pytest.raises(ValidationError, match="Duplicate product_id 1 found"):
        OrderCreateInputSchema().load(payload)


def test_order_create_schema_invalid_phone():
    """Verify schema rejects invalid phone number format."""
    payload = {
        "shipping_address": "123 Orchard Road",
        "recipient_name": "Alice",
        "recipient_phone": "invalid-phone-abc",
        "items": [{"product_id": 1, "quantity": 1}]
    }
    with pytest.raises(ValidationError, match="Invalid phone number format"):
        OrderCreateInputSchema().load(payload)


def test_order_update_status_schema_valid():
    """Verify valid status transitions in OrderUpdateStatusSchema."""
    # Paid
    res_paid = OrderUpdateStatusSchema().load({"status": "paid"})
    assert res_paid["status"] == "paid"

    # Shipped with tracking number
    res_shipped = OrderUpdateStatusSchema().load({"status": "shipped", "tracking_number": "TRK-990"})
    assert res_shipped["tracking_number"] == "TRK-990"

    # Cancelled with reason
    res_cancel = OrderUpdateStatusSchema().load({"status": "cancelled", "cancellation_reason": "Customer request"})
    assert res_cancel["cancellation_reason"] == "Customer request"


def test_order_update_status_schema_missing_tracking_number():
    """Verify status 'shipped' requires tracking_number."""
    with pytest.raises(ValidationError) as exc:
        OrderUpdateStatusSchema().load({"status": "shipped"})
    assert "tracking_number" in exc.value.messages


def test_order_update_status_schema_missing_cancellation_reason():
    """Verify status 'cancelled' requires cancellation_reason."""
    with pytest.raises(ValidationError) as exc:
        OrderUpdateStatusSchema().load({"status": "cancelled"})
    assert "cancellation_reason" in exc.value.messages


def test_order_cancel_input_schema():
    """Verify OrderCancelInputSchema validation."""
    valid = OrderCancelInputSchema().load({"cancellation_reason": "Item out of stock"})
    assert valid["cancellation_reason"] == "Item out of stock"

    with pytest.raises(ValidationError):
        OrderCancelInputSchema().load({"cancellation_reason": "   "})
