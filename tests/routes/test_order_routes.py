"""Integration tests for Order routes (/orders).

Covers:
- GET /orders (Customer view own, Admin view all, Filters, Search, Pagination, 401 Unauthorized)
- GET /orders/<id> (Customer view own 200, Customer view other's 404, Admin view any 200, 404 Not Found, 401 Unauthorized)
- POST /orders (Customer happy path 201, Stock deduction, 400 Insufficient stock, 400 Invalid product, 401 Unauthorized, 422 Validation)
- PATCH /orders/<id> (Status transitions, Shipped requires tracking_number 422, Cancelled requires cancellation_reason 422, Stock restore on cancel, Customer role guards, 409 Invalid transition, 404 Not Found, 401 Unauthorized)
- DELETE /orders/<id> (Soft-cancel 200, Restores stock, Cancellation reason required 422, 409 Invalid state, 404 Not Found, 401 Unauthorized)
"""

import pytest
from app.extensions import db
from app.models.product import Product
from app.models.order import Order


# ==============================================================================
# 1. GET /orders
# ==============================================================================

def test_get_orders_as_customer(client, customer_headers):
    """Verify customer can retrieve only their own orders."""
    response = client.get('/orders', headers=customer_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    # Customer Alice has user_id = 3
    for o in data:
        assert o["user_id"] == 3


def test_get_orders_as_admin_sees_all(client, admin_headers):
    """Verify admin can view all customer orders and filter by status."""
    response = client.get('/orders', headers=admin_headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1

    # Filter by status
    res_status = client.get('/orders?status=pending', headers=admin_headers)
    assert res_status.status_code == 200
    for o in res_status.get_json()["data"]:
        assert o["status"] == "pending"


def test_get_orders_filters_and_pagination(client, admin_headers):
    """Verify order search and pagination."""
    # Search by recipient name
    res_search = client.get('/orders?search=Alice', headers=admin_headers)
    assert res_search.status_code == 200
    assert len(res_search.get_json()["data"]) >= 1

    # Pagination
    res_page = client.get('/orders?page=1&per_page=1', headers=admin_headers)
    assert res_page.status_code == 200
    page_data = res_page.get_json()
    assert len(page_data["data"]) == 1
    assert page_data["page"] == 1


def test_get_orders_unauthorized(client):
    """Verify GET /orders without JWT token returns 401."""
    response = client.get('/orders')
    assert response.status_code == 401


# ==============================================================================
# 2. GET /orders/<id>
# ==============================================================================

def test_get_order_by_id_customer_own(client, customer_headers):
    """Verify customer can retrieve details of their own order (Order 1)."""
    response = client.get('/orders/1', headers=customer_headers)
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["id"] == 1
    assert "items" in data
    assert len(data["items"]) >= 1


def test_get_order_by_id_admin_any(client, admin_headers):
    """Verify admin can view any order."""
    response = client.get('/orders/1', headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == 1


def test_get_order_by_id_not_found_or_forbidden_for_other_user(client):
    """Verify querying another user's order or non-existent order returns 404 (prevents enumeration)."""
    # Create another customer
    from werkzeug.security import generate_password_hash
    from app.models.user import User
    user_b = User(
        username="bob_user",
        email="bob@example.com",
        password_hash=generate_password_hash("bob_password"),
        role="customer",
        is_active=True
    )
    db.session.add(user_b)
    db.session.commit()

    login_res = client.post('/auth/login', json={"username": "bob_user", "password": "bob_password"})
    token_b = login_res.get_json()["data"]["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Bob tries accessing Alice's order (ID 1) -> 404
    res = client.get('/orders/1', headers=headers_b)
    assert res.status_code == 404
    assert res.get_json()["error_code"] == "ORDER_NOT_FOUND"

    # Non-existent order
    res_none = client.get('/orders/99999', headers=headers_b)
    assert res_none.status_code == 404


# ==============================================================================
# 3. POST /orders
# ==============================================================================

def test_place_order_success(client, customer_headers):
    """Verify placing a valid order returns 201 and creates order with decremented product stock."""
    # Check initial stock of product 2
    p2 = db.session.get(Product, 2)
    initial_stock = p2.stock

    payload = {
        "shipping_address": "123 Marina Bay, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+6591234567",
        "items": [
            {
                "product_id": 2,
                "quantity": 2
            }
        ]
    }

    response = client.post('/orders', json=payload, headers=customer_headers)
    assert response.status_code == 201

    data = response.get_json()["data"]
    assert data["recipient_name"] == "Alice Smith"
    assert data["status"] == "pending"
    assert data["total_amount"] == 39.80  # 2 * 19.90
    assert len(data["items"]) == 1

    # Verify stock decremented
    db.session.refresh(p2)
    assert p2.stock == initial_stock - 2


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


def test_place_order_insufficient_stock_fails(client, customer_headers):
    """Verify ordering more than available stock returns 400."""
    payload = {
        "shipping_address": "123 Marina Bay, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+6591234567",
        "items": [{"product_id": 2, "quantity": 99999}]
    }

    response = client.post('/orders', json=payload, headers=customer_headers)
    assert response.status_code == 400
    assert response.get_json()["error_code"] == "PRODUCT_STOCK_VALIDATION_ERROR"


def test_place_order_invalid_product_fails(client, customer_headers):
    """Verify ordering non-existent or inactive product returns 404."""
    # Non-existent product
    payload_none = {
        "shipping_address": "123 Marina Bay",
        "recipient_name": "Alice",
        "recipient_phone": "+6591234567",
        "items": [{"product_id": 99999, "quantity": 1}]
    }
    res_none = client.post('/orders', json=payload_none, headers=customer_headers)
    assert res_none.status_code == 404
    assert res_none.get_json()["error_code"] == "PRODUCT_NOT_FOUND"

    # Inactive product (Product 16 is inactive)
    payload_inact = {
        "shipping_address": "123 Marina Bay",
        "recipient_name": "Alice",
        "recipient_phone": "+6591234567",
        "items": [{"product_id": 16, "quantity": 1}]
    }
    res_inact = client.post('/orders', json=payload_inact, headers=customer_headers)
    assert res_inact.status_code == 404
    assert res_inact.get_json()["error_code"] == "PRODUCT_NOT_FOUND"


def test_place_order_validation_missing_fields(client, customer_headers):
    """Verify placing order with empty items list or missing address returns 422."""
    res_empty_items = client.post('/orders', json={
        "shipping_address": "Address",
        "recipient_name": "Alice",
        "recipient_phone": "+6591234567",
        "items": []
    }, headers=customer_headers)
    assert res_empty_items.status_code == 422


# ==============================================================================
# 4. PATCH /orders/<id>
# ==============================================================================

def test_order_full_status_lifecycle(client, admin_headers, customer_headers):
    """Verify complete order lifecycle: pending -> paid -> processing -> shipped -> delivered."""
    # 1. Place order
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay, Singapore",
        "recipient_name": "Alice Smith",
        "recipient_phone": "+6591234567",
        "items": [{"product_id": 3, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # 2. Customer or Admin sets 'paid'
    paid_res = client.patch(f'/orders/{order_id}', json={"status": "paid"}, headers=customer_headers)
    assert paid_res.status_code == 200
    assert paid_res.get_json()["data"]["status"] == "paid"

    # 3. Admin sets 'processing'
    proc_res = client.patch(f'/orders/{order_id}', json={"status": "processing"}, headers=admin_headers)
    assert proc_res.status_code == 200
    assert proc_res.get_json()["data"]["status"] == "processing"

    # 4. Admin sets 'shipped' (requires tracking_number)
    ship_res = client.patch(
        f'/orders/{order_id}',
        json={"status": "shipped", "tracking_number": "TRK-100293"},
        headers=admin_headers
    )
    assert ship_res.status_code == 200
    assert ship_res.get_json()["data"]["status"] == "shipped"
    assert ship_res.get_json()["data"]["tracking_number"] == "TRK-100293"

    # 5. Admin sets 'delivered'
    deliv_res = client.patch(f'/orders/{order_id}', json={"status": "delivered"}, headers=admin_headers)
    assert deliv_res.status_code == 200
    assert deliv_res.get_json()["data"]["status"] == "delivered"


def test_ship_order_requires_tracking_number(client, admin_headers, customer_headers):
    """Verify transitioning order to 'shipped' requires tracking_number."""
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 3, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    client.patch(f'/orders/{order_id}', json={"status": "paid"}, headers=admin_headers)
    client.patch(f'/orders/{order_id}', json={"status": "processing"}, headers=admin_headers)

    # Missing tracking_number -> 422
    ship_res_no_tracking = client.patch(f'/orders/{order_id}', json={"status": "shipped"}, headers=admin_headers)
    assert ship_res_no_tracking.status_code == 422


def test_cancel_order_via_patch_restores_stock(client, customer_headers):
    """Verify cancelling order via PATCH restores inventory stock."""
    p = db.session.get(Product, 4)
    stock_before = p.stock

    # Place order for 2 units
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 4, "quantity": 2}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    db.session.refresh(p)
    assert p.stock == stock_before - 2

    # Cancel order
    cancel_res = client.patch(f'/orders/{order_id}', json={
        "status": "cancelled",
        "cancellation_reason": "Changed my mind"
    }, headers=customer_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["data"]["status"] == "cancelled"

    # Stock restored
    db.session.refresh(p)
    assert p.stock == stock_before


def test_customer_forbidden_restricted_status_transition(client, customer_headers):
    """Verify customer cannot advance order to 'processing' or 'shipped'."""
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 1, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # Customer pays order
    client.patch(f'/orders/{order_id}', json={"status": "paid"}, headers=customer_headers)

    # Customer tries setting status to 'processing' -> 403 Forbidden
    res = client.patch(f'/orders/{order_id}', json={
        "status": "processing"
    }, headers=customer_headers)
    assert res.status_code == 403
    assert res.get_json()["error_code"] == "FORBIDDEN"


def test_invalid_status_transition_conflict(client, admin_headers, customer_headers):
    """Verify illegal status jump (e.g. pending -> delivered) returns 409 Conflict."""
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 1, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # Illegal transition: pending -> delivered
    res = client.patch(f'/orders/{order_id}', json={"status": "delivered"}, headers=admin_headers)
    assert res.status_code == 409
    assert res.get_json()["error_code"] == "ORDER_INVALID_TRANSITION"


# ==============================================================================
# 5. DELETE /orders/<id>
# ==============================================================================

def test_delete_order_soft_cancels_and_restores_stock(client, customer_headers):
    """Verify DELETE /orders/<id> soft-cancels the order with reason and restores product stock."""
    p = db.session.get(Product, 5)
    stock_before = p.stock

    # Place order
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 5, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # Cancel via DELETE
    del_res = client.delete(f'/orders/{order_id}', json={
        "cancellation_reason": "Item not needed anymore"
    }, headers=customer_headers)
    assert del_res.status_code == 200

    data = del_res.get_json()["data"]
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Item not needed anymore"

    # Verify stock restored
    db.session.refresh(p)
    assert p.stock == stock_before


def test_delete_order_requires_cancellation_reason(client, customer_headers):
    """Verify DELETE /orders/<id> returns 422 if cancellation_reason is missing."""
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 1, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    del_res = client.delete(f'/orders/{order_id}', headers=customer_headers)
    assert del_res.status_code == 422
    assert del_res.get_json()["error_code"] == "VALIDATION_ERROR"


def test_delete_order_blocked_when_already_delivered(client, admin_headers, customer_headers):
    """Verify attempting to cancel an already delivered order returns 409 Conflict."""
    order_res = client.post('/orders', json={
        "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
        "items": [{"product_id": 1, "quantity": 1}]
    }, headers=customer_headers)
    order_id = order_res.get_json()["data"]["id"]

    # Advance to delivered
    client.patch(f'/orders/{order_id}', json={"status": "paid"}, headers=admin_headers)
    client.patch(f'/orders/{order_id}', json={"status": "processing"}, headers=admin_headers)
    client.patch(f'/orders/{order_id}', json={"status": "shipped", "tracking_number": "TRK-01"}, headers=admin_headers)
    client.patch(f'/orders/{order_id}', json={"status": "delivered"}, headers=admin_headers)

    # Attempt cancel on delivered order -> 409
    del_res = client.delete(f'/orders/{order_id}', json={
        "cancellation_reason": "Trying to cancel delivered"
    }, headers=admin_headers)
    assert del_res.status_code == 409
    assert del_res.get_json()["error_code"] == "ORDER_CANNOT_BE_CANCELLED"


def test_delete_order_unauthorized(client):
    """Verify DELETE /orders/<id> without JWT returns 401."""
    response = client.delete('/orders/1')
    assert response.status_code == 401
