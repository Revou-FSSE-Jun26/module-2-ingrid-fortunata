"""Tests simulating database exceptions and rollbacks to verify error responses."""

from unittest.mock import patch
import pytest
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


def test_user_routes_database_errors(client, superadmin_headers):
    """Verify database exceptions in user routes return 500 USER_DATABASE_ERROR or 409 USER_CONFLICT."""
    # Registration database error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res = client.post('/users', json={
            "username": "dberroruser", "email": "dberror@example.com", "password": "password123"
        })
        assert res.status_code == 500
        assert res.get_json()["error_code"] == "USER_DATABASE_ERROR"

    # Registration integrity error
    with patch("app.extensions.db.session.commit", side_effect=IntegrityError("stmt", "params", "orig")):
        res_integ = client.post('/users', json={
            "username": "integuser", "email": "integ@example.com", "password": "password123"
        })
        assert res_integ.status_code == 409
        assert res_integ.get_json()["error_code"] == "USER_CONFLICT"

    # User update database error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_up = client.put('/users/1', json={"username": "new_name"}, headers=superadmin_headers)
        assert res_up.status_code == 500
        assert res_up.get_json()["error_code"] == "USER_DATABASE_ERROR"

    # User update integrity error
    with patch("app.extensions.db.session.commit", side_effect=IntegrityError("stmt", "params", "orig")):
        res_up_integ = client.put('/users/1', json={"username": "new_name"}, headers=superadmin_headers)
        assert res_up_integ.status_code == 409
        assert res_up_integ.get_json()["error_code"] == "USER_CONFLICT"


def test_category_routes_database_errors(client, admin_headers):
    """Verify database exceptions in category routes return 500 CATEGORY_DATABASE_ERROR or 409 CATEGORY_CONFLICT."""
    # Create category DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res = client.post('/categories', json={"name": "DBCat"}, headers=admin_headers)
        assert res.status_code == 500
        assert res.get_json()["error_code"] == "CATEGORY_DATABASE_ERROR"

    # Create category Integrity error
    with patch("app.extensions.db.session.commit", side_effect=IntegrityError("stmt", "params", "orig")):
        res_integ = client.post('/categories', json={"name": "IntegCat"}, headers=admin_headers)
        assert res_integ.status_code == 409
        assert res_integ.get_json()["error_code"] == "CATEGORY_CONFLICT"

    # Update category DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_up = client.put('/categories/1', json={"description": "New"}, headers=admin_headers)
        assert res_up.status_code == 500
        assert res_up.get_json()["error_code"] == "CATEGORY_DATABASE_ERROR"

    # Update category Integrity error
    with patch("app.extensions.db.session.commit", side_effect=IntegrityError("stmt", "params", "orig")):
        res_up_integ = client.put('/categories/1', json={"description": "New"}, headers=admin_headers)
        assert res_up_integ.status_code == 409
        assert res_up_integ.get_json()["error_code"] == "CATEGORY_CONFLICT"

    # Delete category DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_del = client.delete('/categories/8', headers=admin_headers)
        assert res_del.status_code == 500
        assert res_del.get_json()["error_code"] == "CATEGORY_DATABASE_ERROR"


def test_product_routes_database_errors(client, admin_headers):
    """Verify database exceptions in product routes return 500 PRODUCT_DATABASE_ERROR."""
    # Create product DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res = client.post('/products', json={
            "name": "DB Prod", "price": 10.0, "stock": 5, "color": "Blue"
        }, headers=admin_headers)
        assert res.status_code == 500
        assert res.get_json()["error_code"] == "PRODUCT_DATABASE_ERROR"

    # Update product DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_up = client.put('/products/1', json={"stock": 99}, headers=admin_headers)
        assert res_up.status_code == 500
        assert res_up.get_json()["error_code"] == "PRODUCT_DATABASE_ERROR"

    # Delete product DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_del = client.delete('/products/16', headers=admin_headers)
        assert res_del.status_code == 500
        assert res_del.get_json()["error_code"] == "PRODUCT_DATABASE_ERROR"


def test_order_routes_database_errors(client, customer_headers):
    """Verify database exceptions in order routes return 500 ORDER_DATABASE_ERROR."""
    # Place order DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res = client.post('/orders', json={
            "shipping_address": "123 Marina Bay", "recipient_name": "Alice", "recipient_phone": "+6591234567",
            "items": [{"product_id": 1, "quantity": 1}]
        }, headers=customer_headers)
        assert res.status_code == 500
        assert res.get_json()["error_code"] == "ORDER_DATABASE_ERROR"

    # Update order status DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_patch = client.patch('/orders/1', json={"status": "paid"}, headers=customer_headers)
        assert res_patch.status_code == 500
        assert res_patch.get_json()["error_code"] == "ORDER_DATABASE_ERROR"

    # Delete order DB error
    with patch("app.extensions.db.session.commit", side_effect=SQLAlchemyError("DB Error")):
        res_del = client.delete('/orders/1', json={"cancellation_reason": "Cancel"}, headers=customer_headers)
        assert res_del.status_code == 500
        assert res_del.get_json()["error_code"] == "ORDER_DATABASE_ERROR"
