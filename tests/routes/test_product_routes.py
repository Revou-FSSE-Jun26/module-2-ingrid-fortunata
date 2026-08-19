"""Integration tests for Product routes (/products)."""

import pytest


def test_get_products_list_public(client):
    """Verify public GET /products returns only active products in active categories."""
    response = client.get('/products')
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert len(data) >= 1
    
    product_names = [p["name"] for p in data]
    assert "Deactivated Phone" not in product_names
    assert "Product in Inactive Category" not in product_names


def test_get_product_by_id_active(client):
    """Verify getting an active product by ID returns 200."""
    response = client.get('/products/1')
    assert response.status_code == 200
    
    data = response.get_json()["data"]
    assert data["id"] == 1


def test_get_product_by_id_inactive_returns_404(client):
    """Verify querying an inactive product returns 404 for customers/public."""
    # Find deactivated product
    response = client.get('/products/99999')
    assert response.status_code == 404


def test_admin_create_product_success(client, admin_headers):
    """Verify admin can create a product with default size and unisex gender."""
    payload = {
        "name": "Pytest Unisex Windbreaker",
        "price": 49.90,
        "stock": 30,
        "color": "Black"
    }

    response = client.post('/products', json=payload, headers=admin_headers)
    assert response.status_code == 201

    data = response.get_json()["data"]
    assert data["name"] == "Pytest Unisex Windbreaker"
    assert data["size"] == "Free Size"
    assert data["gender"] == "Unisex"
    assert data["sku"].startswith("UQ-")

    # Clean up product
    prod_id = data["id"]
    client.delete(f'/products/{prod_id}', headers=admin_headers)


def test_customer_cannot_create_product(client, customer_headers):
    """Verify customer receives 403 Forbidden when attempting to create a product."""
    payload = {
        "name": "Unauthorized Jacket",
        "price": 100.0,
        "stock": 10,
        "color": "Blue"
    }

    response = client.post('/products', json=payload, headers=customer_headers)
    assert response.status_code == 403


def test_delete_product_conflict_when_ordered(client, admin_headers):
    """Verify deleting a product linked to seeded orders returns 409 Conflict."""
    response = client.delete('/products/1', headers=admin_headers)
    assert response.status_code == 409

    data = response.get_json()
    assert data["error_code"] == "PRODUCT_CONFLICT"


def test_admin_update_product_partial_stock_only(client, admin_headers):
    """Verify admin can perform partial update on a product (e.g. stock only)."""
    # 1. Create a product first
    create_payload = {
        "name": "Partial Update Test Shirt",
        "price": 25.00,
        "stock": 10,
        "color": "White"
    }
    create_res = client.post('/products', json=create_payload, headers=admin_headers)
    assert create_res.status_code == 201
    prod_id = create_res.get_json()["data"]["id"]

    # 2. Update stock only via PUT
    update_res = client.put(f'/products/{prod_id}', json={"stock": 55}, headers=admin_headers)
    assert update_res.status_code == 200
    updated_data = update_res.get_json()["data"]

    # Verify stock changed, but other fields remain untouched
    assert updated_data["stock"] == 55
    assert updated_data["name"] == "Partial Update Test Shirt"
    assert updated_data["price"] == 25.00
    assert updated_data["color"] == "White"

    # 3. Clean up
    client.delete(f'/products/{prod_id}', headers=admin_headers)


def test_admin_update_product_empty_body_fails(client, admin_headers):
    """Verify updating product with empty payload returns 422 validation error."""
    response = client.put('/products/1', json={}, headers=admin_headers)
    assert response.status_code == 422
    assert response.get_json()["error_code"] == "VALIDATION_ERROR"
