"""Integration tests for Category routes (/categories).

Covers:
- GET /categories (Happy & Admin filter)
- GET /categories/<id> (Happy & 404 Not Found)
- POST /categories (Happy 201, 401 Unauthorized, 403 Forbidden, 422 Validation Error, 409 Conflict)
- PUT /categories/<id> (Happy 200, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Validation Error)
- DELETE /categories/<id> (Happy 204, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict active products guard)
"""

import pytest


# ============================================================================
# 1. GET /categories
# ============================================================================

def test_get_categories_list_happy(client):
    """Happy Path: Public user gets active categories list."""
    response = client.get('/categories')
    assert response.status_code == 200

    payload = response.get_json()
    assert "data" in payload
    data = payload["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check category item structure
    cat = data[0]
    assert "id" in cat
    assert "name" in cat
    assert "description" in cat
    assert "is_active" in cat


def test_get_categories_admin_filter(client, admin_headers):
    """Happy Path: Admin can query categories by is_active filter."""
    response = client.get('/categories?is_active=true', headers=admin_headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert isinstance(data, list)


# ============================================================================
# 2. GET /categories/<id>
# ============================================================================

def test_get_category_by_id_happy(client):
    """Happy Path: Public user gets specific category by ID with products."""
    response = client.get('/categories/1')
    assert response.status_code == 200

    payload = response.get_json()
    assert "data" in payload
    cat = payload["data"]
    assert cat["id"] == 1
    assert "name" in cat
    assert "products" in cat
    assert isinstance(cat["products"], list)


def test_get_category_by_id_not_found(client):
    """Error Case: 404 Not Found for non-existent category ID."""
    response = client.get('/categories/99999')
    assert response.status_code == 404

    payload = response.get_json()
    assert payload["error_code"] == "CATEGORY_NOT_FOUND"
    assert "message" in payload


# ============================================================================
# 3. POST /categories
# ============================================================================

def test_create_category_happy_path(client, admin_headers):
    """Happy Path: Admin creates a new category (201 Created)."""
    payload = {
        "name": "QA Test Outerwear",
        "description": "Jackets & Winter Coats",
        "is_active": True
    }
    response = client.post('/categories', json=payload, headers=admin_headers)
    assert response.status_code == 201

    data = response.get_json()["data"]
    assert data["name"] == "QA Test Outerwear"
    assert data["description"] == "Jackets & Winter Coats"
    assert data["is_active"] is True
    assert "id" in data

    # Cleanup
    cat_id = data["id"]
    client.delete(f'/categories/{cat_id}', headers=admin_headers)


def test_create_category_unauthorized(client):
    """Error Case: 401 Unauthorized when missing authentication token."""
    payload = {"name": "Unauthenticated Category"}
    response = client.post('/categories', json=payload)
    assert response.status_code == 401


def test_create_category_forbidden(client, customer_headers):
    """Error Case: 403 Forbidden when customer user attempts creation."""
    payload = {"name": "Unauthorized Category", "description": "Customer attempt"}
    response = client.post('/categories', json=payload, headers=customer_headers)
    assert response.status_code == 403

    payload = response.get_json()
    assert payload["error_code"] == "FORBIDDEN"
    assert "message" in payload


def test_create_category_validation_missing_name(client, admin_headers):
    """Error Case: 422 Unprocessable Entity when 'name' is missing or blank."""
    # Missing name
    response = client.post('/categories', json={"description": "No name"}, headers=admin_headers)
    assert response.status_code == 422

    # Blank name
    response_blank = client.post('/categories', json={"name": "   "}, headers=admin_headers)
    assert response_blank.status_code == 422


def test_create_category_duplicate_name(client, admin_headers):
    """Error Case: 409 Conflict when category name already exists."""
    import uuid
    unique_name = f"Category Dup Test {uuid.uuid4()}"
    payload = {"name": unique_name, "description": "Desc"}
    
    # Create category first
    res1 = client.post('/categories', json=payload, headers=admin_headers)
    assert res1.status_code == 201
    cat_id = res1.get_json()["data"]["id"]

    # Try creating duplicate
    res2 = client.post('/categories', json=payload, headers=admin_headers)
    assert res2.status_code == 409
    payload_err = res2.get_json()
    assert payload_err["error_code"] == "CATEGORY_CONFLICT"
    assert "message" in payload_err

    # Cleanup
    client.delete(f'/categories/{cat_id}', headers=admin_headers)


# ============================================================================
# 4. PUT /categories/<id>
# ============================================================================

def test_update_category_happy_path(client, admin_headers):
    """Happy Path: Admin updates category fields (200 OK)."""
    import uuid
    cat_name = f"Pre-Update {uuid.uuid4()}"
    new_name = f"Post-Update {uuid.uuid4()}"

    # Create temporary category
    create_res = client.post('/categories', json={"name": cat_name}, headers=admin_headers)
    assert create_res.status_code == 201
    cat_id = create_res.get_json()["data"]["id"]

    # Update category
    update_payload = {
        "name": new_name,
        "description": "Updated Description",
        "is_active": False
    }
    put_res = client.put(f'/categories/{cat_id}', json=update_payload, headers=admin_headers)
    assert put_res.status_code == 200

    updated_data = put_res.get_json()["data"]
    assert updated_data["name"] == new_name
    assert updated_data["description"] == "Updated Description"
    assert updated_data["is_active"] is False

    # Cleanup
    client.delete(f'/categories/{cat_id}', headers=admin_headers)


def test_update_category_unauthorized(client):
    """Error Case: 401 Unauthorized when missing authentication token on PUT."""
    response = client.put('/categories/1', json={"name": "Unauth Update"})
    assert response.status_code == 401


def test_update_category_forbidden(client, customer_headers):
    """Error Case: 403 Forbidden when customer user attempts PUT."""
    response = client.put('/categories/1', json={"name": "Forbidden Update"}, headers=customer_headers)
    assert response.status_code == 403


def test_update_category_not_found(client, admin_headers):
    """Error Case: 404 Not Found for non-existent category ID on PUT."""
    response = client.put('/categories/99999', json={"name": "Ghost Category"}, headers=admin_headers)
    assert response.status_code == 404

    payload = response.get_json()
    assert payload["error_code"] == "CATEGORY_NOT_FOUND"
    assert "message" in payload


def test_update_category_duplicate_name(client, admin_headers):
    """Error Case: 409 Conflict when updating category to an existing category's name."""
    import uuid
    name_a = f"Cat Alpha {uuid.uuid4()}"
    name_b = f"Cat Beta {uuid.uuid4()}"

    # Create category A and B
    res_a = client.post('/categories', json={"name": name_a}, headers=admin_headers)
    assert res_a.status_code == 201
    cat_a = res_a.get_json()["data"]["id"]

    res_b = client.post('/categories', json={"name": name_b}, headers=admin_headers)
    assert res_b.status_code == 201
    cat_b = res_b.get_json()["data"]["id"]

    # Try updating B's name to name_a
    put_res = client.put(f'/categories/{cat_b}', json={"name": name_a}, headers=admin_headers)
    assert put_res.status_code == 409
    assert put_res.get_json()["error_code"] == "CATEGORY_CONFLICT"

    # Cleanup
    client.delete(f'/categories/{cat_a}', headers=admin_headers)
    client.delete(f'/categories/{cat_b}', headers=admin_headers)



def test_update_category_validation_empty_body(client, admin_headers):
    """Error Case: 422 Unprocessable Entity when sending empty request body to PUT."""
    response = client.put('/categories/1', json={}, headers=admin_headers)
    assert response.status_code == 422


# ============================================================================
# 5. DELETE /categories/<id>
# ============================================================================

def test_delete_category_happy_path(client, admin_headers):
    """Happy Path: Admin deletes a category without active products (204 No Content)."""
    # Create temporary category
    create_res = client.post('/categories', json={"name": "Delete Target Category"}, headers=admin_headers)
    cat_id = create_res.get_json()["data"]["id"]

    # Delete
    del_res = client.delete(f'/categories/{cat_id}', headers=admin_headers)
    assert del_res.status_code == 204

    # Verify 404 on GET
    get_res = client.get(f'/categories/{cat_id}')
    assert get_res.status_code == 404


def test_delete_category_unauthorized(client):
    """Error Case: 401 Unauthorized when missing authentication token on DELETE."""
    response = client.delete('/categories/1')
    assert response.status_code == 401


def test_delete_category_forbidden(client, customer_headers):
    """Error Case: 403 Forbidden when customer attempts DELETE."""
    response = client.delete('/categories/1', headers=customer_headers)
    assert response.status_code == 403


def test_delete_category_not_found(client, admin_headers):
    """Error Case: 404 Not Found for non-existent category ID on DELETE."""
    response = client.delete('/categories/99999', headers=admin_headers)
    assert response.status_code == 404
    assert response.get_json()["error_code"] == "CATEGORY_NOT_FOUND"


def test_delete_category_blocked_by_active_products(client, admin_headers):
    """Error Case: 409 Conflict when attempting to delete category with active products."""
    # Category 1 has active seeded products
    response = client.delete('/categories/1', headers=admin_headers)
    assert response.status_code == 409

    payload = response.get_json()
    assert payload["error_code"] == "CATEGORY_CONFLICT"
    assert "message" in payload


