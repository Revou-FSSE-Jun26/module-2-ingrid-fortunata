import pytest
from app import create_app
from app.extensions import db


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask application instance for tests."""
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
    })

    with flask_app.app_context():
        yield flask_app


@pytest.fixture(scope="function")
def client(app):
    """A test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def admin_headers(client):
    """Returns Bearer authorization headers for the seeded admin user."""
    payload = {"username": "admin_user", "password": "admin_password"}
    res = client.post('/auth/login', json=payload)
    data = res.get_json()
    assert res.status_code == 200, f"Admin login failed: {data}"
    token = data['data']['token']
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def customer_headers(client):
    """Returns Bearer authorization headers for the seeded customer user (alice_smith)."""
    payload = {"username": "alice_smith", "password": "alice_password"}
    res = client.post('/auth/login', json=payload)
    data = res.get_json()
    assert res.status_code == 200, f"Customer login failed: {data}"
    token = data['data']['token']
    return {"Authorization": f"Bearer {token}"}
