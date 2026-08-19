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
