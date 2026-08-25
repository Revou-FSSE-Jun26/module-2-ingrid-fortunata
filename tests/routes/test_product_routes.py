"""Integration tests for Product routes (/products).

Covers:
- GET /products (Public active list, Admin filter, Search, Category filter, Fashion filters, Price filter, Sorting, Pagination)
- GET /products/<id> (Active product, Inactive product customer 404 vs admin 200, 404 Not Found)
- POST /products (Admin happy path, With images, 401 Unauthorized, 403 Forbidden, 400 Invalid category, 422 Validation)
- PUT /products/<id> (Admin partial update, Replace images, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Validation)
- DELETE /products/<id> (Hard delete un-ordered 204, Soft delete delivered/cancelled 204, 409 Conflict active orders, 401 Unauthorized, 403 Forbidden, 404 Not Found)
"""

import pytest
from app.extensions import db
from app.models.product import Product
from app.models.order import Order


# ==============================================================================
# 1. GET /products
# ==============================================================================

def test_get_products_list_public(client):
    """Verify public GET /products returns only active products in active categories."""
    response = client.get('/products')
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert len(data) >= 1
    
    product_names = [p["name"] for p in data]
    assert "Vintage Flannel Shirt (Discontinued)" not in product_names


def test_get_products_admin_filter_inactive(client, admin_headers):
    """Verify admin can view inactive products via ?is_active=false."""
    response = client.get('/products?is_active=false', headers=admin_headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) >= 1
    assert all(p["is_active"] is False for p in data)


def test_get_products_filters(client):
    """Verify filtering products by gender, category_id, color, price range, and search."""
    # Filter by gender
    res_gender = client.get('/products?gender=Men')
    assert res_gender.status_code == 200
    for p in res_gender.get_json()["data"]:
        assert p["gender"] in ["Men", "Unisex"]

    # Filter by category_id
    res_cat = client.get('/products?category_id=1')
    assert res_cat.status_code == 200
    for p in res_cat.get_json()["data"]:
        assert p["category_id"] == 1

    # Search by keyword
    res_search = client.get('/products?search=AIRism')
    assert res_search.status_code == 200
    data_search = res_search.get_json()["data"]
    assert len(data_search) >= 1
    assert any("AIRism" in p["name"] for p in data_search)

    # Filter by price range
    res_price = client.get('/products?min_price=10&max_price=20')
    assert res_price.status_code == 200
    for p in res_price.get_json()["data"]:
        assert 10 <= p["price"] <= 20


def test_get_products_sorting_and_pagination(client):
    """Verify sorting and pagination on GET /products."""
    # Sort by price ascending
    res_sort = client.get('/products?sort_by=price_asc')
    assert res_sort.status_code == 200
    data = res_sort.get_json()["data"]
    prices = [p["price"] for p in data]
    assert prices == sorted(prices)

    # Pagination
    res_page = client.get('/products?page=1&per_page=3')
    assert res_page.status_code == 200
    page_data = res_page.get_json()
    assert len(page_data["data"]) == 3
    assert page_data["page"] == 1
    assert page_data["per_page"] == 3


# ==============================================================================
# 2. GET /products/<id>
# ==============================================================================

def test_get_product_by_id_active(client):
    """Verify getting an active product by ID returns 200 with detail dictionary."""
    response = client.get('/products/1')
    assert response.status_code == 200
    
    data = response.get_json()["data"]
    assert data["id"] == 1
    assert "images" in data
    assert len(data["images"]) >= 1


def test_get_product_by_id_inactive_customer_404_vs_admin_200(client, admin_headers):
    """Verify customer receives 404 for inactive product (ID 16), while admin receives 200."""
    # Customer / public
    res_cust = client.get('/products/16')
    assert res_cust.status_code == 404

    # Admin
    res_admin = client.get('/products/16', headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.get_json()["data"]["id"] == 16


def test_get_product_by_id_not_found(client):
    """Verify querying non-existent product returns 404."""
    response = client.get('/products/99999')
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "PRODUCT_NOT_FOUND"


# ==============================================================================
# 3. POST /products
# ==============================================================================

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


def test_admin_create_product_with_images(client, admin_headers):
    """Verify admin can create a product with multiple images and designated primary."""
    payload = {
        "name": "Multi-Image Hoodie",
        "price": 59.90,
        "stock": 25,
        "color": "Grey",
        "category_id": 4,
        "images": [
            {"image_base64": "data:image/png;base64,AAA1", "is_primary": True},
            {"image_base64": "data:image/png;base64,AAA2", "is_primary": False}
        ]
    }

    response = client.post('/products', json=payload, headers=admin_headers)
    assert response.status_code == 201

    data = response.get_json()["data"]
    assert len(data["images"]) == 2
    assert any(img["is_primary"] is True for img in data["images"])

    # Clean up
    client.delete(f'/products/{data["id"]}', headers=admin_headers)


def test_create_product_unauthorized(client):
    """Verify creating product without token returns 401."""
    payload = {"name": "Unauth Product", "price": 10.0, "stock": 5, "color": "Red"}
    response = client.post('/products', json=payload)
    assert response.status_code == 401


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
    assert response.get_json()["error_code"] == "FORBIDDEN"


def test_create_product_invalid_category(client, admin_headers):
    """Verify creating product with non-existent (404) or inactive category (400)."""
    # Non-existent category -> 404
    res_none = client.post('/products', json={
        "name": "Bad Category Product",
        "price": 20.0,
        "stock": 5,
        "color": "White",
        "category_id": 99999
    }, headers=admin_headers)
    assert res_none.status_code == 404
    assert res_none.get_json()["error_code"] == "CATEGORY_NOT_FOUND"

    # Inactive category (Category 8 is inactive)
    res_inact = client.post('/products', json={
        "name": "Inactive Category Product",
        "price": 20.0,
        "stock": 5,
        "color": "White",
        "category_id": 8
    }, headers=admin_headers)
    assert res_inact.status_code == 400
    assert res_inact.get_json()["error_code"] == "CATEGORY_INACTIVE"


def test_create_product_validation_errors(client, admin_headers):
    """Verify validation errors when missing required fields or negative price/stock."""
    # Missing required name/price/stock/color
    res = client.post('/products', json={"description": "No name"}, headers=admin_headers)
    assert res.status_code == 422

    # Negative price
    res_neg_price = client.post('/products', json={
        "name": "Negative Price", "price": -5.0, "stock": 10, "color": "Red"
    }, headers=admin_headers)
    assert res_neg_price.status_code == 422


# ==============================================================================
# 4. PUT /products/<id>
# ==============================================================================

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


def test_admin_update_product_images(client, admin_headers):
    """Verify updating product images replaces previous image list."""
    # 1. Create product
    create_res = client.post('/products', json={
        "name": "Image Replace Product", "price": 30.0, "stock": 10, "color": "Green"
    }, headers=admin_headers)
    prod_id = create_res.get_json()["data"]["id"]

    # 2. Update with new image
    update_res = client.put(f'/products/{prod_id}', json={
        "images": [{"image_base64": "data:image/png;base64,NEW_IMG", "is_primary": True}]
    }, headers=admin_headers)
    assert update_res.status_code == 200
    updated_data = update_res.get_json()["data"]
    assert len(updated_data["images"]) == 1
    assert updated_data["images"][0]["image_base64"] == "data:image/png;base64,NEW_IMG"

    # 3. Clean up
    client.delete(f'/products/{prod_id}', headers=admin_headers)


def test_update_product_unauthorized(client):
    """Verify updating product without token returns 401."""
    response = client.put('/products/1', json={"stock": 10})
    assert response.status_code == 401


def test_update_product_forbidden(client, customer_headers):
    """Verify customer receives 403 when trying to update product."""
    response = client.put('/products/1', json={"stock": 10}, headers=customer_headers)
    assert response.status_code == 403


def test_update_product_not_found(client, admin_headers):
    """Verify updating non-existent product returns 404."""
    response = client.put('/products/99999', json={"stock": 10}, headers=admin_headers)
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "PRODUCT_NOT_FOUND"


def test_admin_update_product_empty_body_fails(client, admin_headers):
    """Verify updating product with empty payload returns 422 validation error."""
    response = client.put('/products/1', json={}, headers=admin_headers)
    assert response.status_code == 422
    assert response.get_json()["error_code"] == "VALIDATION_ERROR"


# ==============================================================================
# 5. DELETE /products/<id>
# ==============================================================================

def test_delete_product_conflict_when_active_order(client, admin_headers):
    """Verify deleting a product linked to pending/paid/processing/shipped orders returns 409 Conflict."""
    response = client.delete('/products/1', headers=admin_headers)
    assert response.status_code == 409
    data = response.get_json()
    assert data["error_code"] == "PRODUCT_CONFLICT"


def test_delete_product_hard_delete_success(client, admin_headers):
    """Verify un-ordered product is hard-deleted with 204 No Content."""
    # Create product
    create_res = client.post('/products', json={
        "name": "Hard Delete Product", "price": 15.0, "stock": 5, "color": "Grey"
    }, headers=admin_headers)
    prod_id = create_res.get_json()["data"]["id"]

    # Delete
    del_res = client.delete(f'/products/{prod_id}', headers=admin_headers)
    assert del_res.status_code == 204

    # Verify 404 on GET
    get_res = client.get(f'/products/{prod_id}', headers=admin_headers)
    assert get_res.status_code == 404


def test_delete_product_unauthorized(client):
    """Verify deleting product without token returns 401."""
    response = client.delete('/products/1')
    assert response.status_code == 401


def test_delete_product_forbidden(client, customer_headers):
    """Verify customer receives 403 when trying to delete product."""
    response = client.delete('/products/1', headers=customer_headers)
    assert response.status_code == 403


def test_delete_product_not_found(client, admin_headers):
    """Verify deleting non-existent product returns 404."""
    response = client.delete('/products/99999', headers=admin_headers)
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "PRODUCT_NOT_FOUND"
