"""Tests for OpenAPI / Swagger documentation endpoints."""

import pytest


def test_swagger_ui_endpoint(client):
    """Verify Swagger UI page is accessible and returns 200."""
    response = client.get('/swagger-ui')
    assert response.status_code == 200
    assert b'swagger-ui' in response.data.lower()


def test_openapi_spec_json(client):
    """Verify OpenAPI specification JSON endpoint returns valid metadata."""
    response = client.get('/openapi.json')
    assert response.status_code == 200

    data = response.get_json()
    assert data['info']['title'] == "RevoFashion API"
    assert data['openapi'] == "3.0.3"
    assert '/users' in data['paths']
    assert '/products' in data['paths']
    assert '/orders' in data['paths']
    assert '/categories' in data['paths']
