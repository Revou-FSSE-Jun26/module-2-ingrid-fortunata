"""Tests for OpenAPI / Swagger documentation endpoints."""

import pytest


def test_swagger_ui_endpoint(client):
    """Verify Swagger UI page is accessible and returns 200."""
    response = client.get('/swagger-ui')
    assert response.status_code == 200
    assert b'swagger-ui' in response.data.lower()


def test_openapi_spec_json(client):
    """Verify OpenAPI specification JSON endpoint returns valid metadata and security configuration."""
    response = client.get('/openapi.json')
    assert response.status_code == 200

    data = response.get_json()
    assert data['info']['title'] == "RevoFashion API"
    assert data['openapi'] == "3.0.3"
    assert '/users' in data['paths']
    assert '/products' in data['paths']
    assert '/orders' in data['paths']
    assert '/categories' in data['paths']

    # Verify BearerAuth security scheme in OpenAPI components
    security_schemes = data.get('components', {}).get('securitySchemes', {})
    assert 'BearerAuth' in security_schemes
    assert security_schemes['BearerAuth']['type'] == 'http'
    assert security_schemes['BearerAuth']['scheme'] == 'bearer'
    assert security_schemes['BearerAuth']['bearerFormat'] == 'JWT'

    # Verify protected endpoints include security requirement
    assert data['paths']['/products']['post']['security'] == [{'BearerAuth': []}]
    assert data['paths']['/products/{id}']['put']['security'] == [{'BearerAuth': []}]
    assert data['paths']['/products/{id}']['delete']['security'] == [{'BearerAuth': []}]
    assert data['paths']['/categories']['post']['security'] == [{'BearerAuth': []}]
    assert data['paths']['/orders']['post']['security'] == [{'BearerAuth': []}]
    assert data['paths']['/orders']['get']['security'] == [{'BearerAuth': []}]
    assert data['paths']['/users']['get']['security'] == [{'BearerAuth': []}]

    # Verify public endpoints do not require security
    assert 'security' not in data['paths']['/auth/login']['post']
    assert 'security' not in data['paths']['/users']['post']
    assert 'security' not in data['paths']['/products']['get']

