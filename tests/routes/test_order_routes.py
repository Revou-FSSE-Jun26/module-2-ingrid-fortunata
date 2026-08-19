"""Integration tests for Order routes (/orders)."""

import pytest


def test_get_orders_as_customer(client, customer_headers):
    """Verify customer can retrieve their own orders."""
    response = client.get('/orders', headers=customer_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert isinstance(data, list)


def test_place_order_success(client, customer_headers):
    """Verify placing a valid order returns 201 and creates order."""
    payload = {
        "shipping_address": "123 Marina Bay, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+6591234567",
        "items": [
            {
                "product_id": 1,
                "quantity": 1
            }
        ]
    }

    response = client.post('/orders', json=payload, headers=customer_headers)
    assert response.status_code == 201

    data = response.get_json()["data"]
    assert data["recipient_name"] == "Alice Smith"
    assert data["status"] == "pending"
    assert data["total_amount"] > 0


def test_place_order_unauthorized(client):
    """Verify placing order without authentication returns 401."""
    payload = {
        "shipping_address": "Some Address",
        "recipient_name": "Nobody",
        "recipient_phone": "+1234567890",
        "items": [{"product_id": 1, "quantity": 1}]
    }

    response = client.post('/orders', json=payload)
    assert response.status_code == 401


def test_ship_order_requires_tracking_number(client, admin_headers, customer_headers):
    """Verify transitioning order to 'shipped' requires tracking_number."""
    # 1. Customer places order
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+6591234567",
        "items": [{"product_id": 1, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # 2. Advance to paid and processing
    client.patch(f'/orders/{order_id}', json={"status": "paid"}, headers=admin_headers)
    client.patch(f'/orders/{order_id}', json={"status": "processing"}, headers=admin_headers)

    # 3. Transition to shipped without tracking_number -> fails 422
    ship_res_no_tracking = client.patch(f'/orders/{order_id}', json={"status": "shipped"}, headers=admin_headers)
    assert ship_res_no_tracking.status_code == 422

    # 4. Transition to shipped with tracking_number -> succeeds 200
    ship_res = client.patch(
        f'/orders/{order_id}',
        json={"status": "shipped", "tracking_number": "JNE-TRACK-8899"},
        headers=admin_headers
    )
    assert ship_res.status_code == 200
    assert ship_res.get_json()["data"]["tracking_number"] == "JNE-TRACK-8899"
    assert ship_res.get_json()["data"]["status"] == "shipped"


def test_cancel_order_requires_reason(client, customer_headers):
    """Verify cancelling an order via PATCH or DELETE requires a cancellation reason."""
    # 1. Customer places order
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+6591234567",
        "items": [{"product_id": 1, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # 2. Try cancelling via PATCH without reason -> 422
    cancel_res_no_reason = client.patch(f'/orders/{order_id}', json={"status": "cancelled"}, headers=customer_headers)
    assert cancel_res_no_reason.status_code == 422

    # 3. Try cancelling via DELETE without reason -> 422
    delete_res_no_reason = client.delete(f'/orders/{order_id}', headers=customer_headers)
    assert delete_res_no_reason.status_code == 422

    # 4. Cancel via PATCH with reason -> succeeds 200
    cancel_res = client.patch(
        f'/orders/{order_id}',
        json={"status": "cancelled", "cancellation_reason": "Customer ordered wrong size"},
        headers=customer_headers
    )
    assert cancel_res.status_code == 200
    data = cancel_res.get_json()["data"]
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Customer ordered wrong size"
