"""Integration tests for Category routes (/categories)."""

import pytest


def test_get_categories_list(client):
    """Verify public GET /categories returns active categories list."""
    response = client.get('/categories')
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_category_by_id(client):
    """Verify GET /categories/1 returns the category."""
    response = client.get('/categories/1')
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["id"] == 1


def test_customer_cannot_create_category(client, customer_headers):
    """Verify customer cannot create a category (403 Forbidden)."""
    payload = {"name": "Unauthorized Category", "description": "Desc"}
    response = client.post('/categories', json=payload, headers=customer_headers)
    assert response.status_code == 403


def test_admin_create_and_delete_category(client, admin_headers):
    """Verify admin can create and delete a category."""
    payload = {
        "name": "Pytest Temp Category",
        "description": "Created for testing"
    }

    response = client.post('/categories', json=payload, headers=admin_headers)
    assert response.status_code == 201

    cat_id = response.get_json()["data"]["id"]

    # Delete category
    del_res = client.delete(f'/categories/{cat_id}', headers=admin_headers)
    assert del_res.status_code == 204
