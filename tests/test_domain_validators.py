import pytest
from app.errors import (
    error_response,
    not_found_response,
    conflict_response,
    forbidden_response,
    unauthorized_response,
)
from app.validators import (
    validate_order_status_transition,
    validate_order_cancellation,
)


def test_error_response_helpers(app):
    """Test error response constructors generate expected status codes and JSON keys."""
    with app.test_request_context():
        res, code = error_response("CUSTOM_ERROR", "Custom message", 400)
        assert code == 400
        assert res.get_json() == {"error_code": "CUSTOM_ERROR", "message": "Custom message"}

        res, code = not_found_response("Product", 99)
        assert code == 404
        assert res.get_json()["error_code"] == "PRODUCT_NOT_FOUND"

        res, code = conflict_response("TEST_CONFLICT", "Conflict test")
        assert code == 409
        assert res.get_json()["error_code"] == "TEST_CONFLICT"

        res, code = forbidden_response("Forbidden test", error_code="USER_FORBIDDEN")
        assert code == 403
        assert res.get_json()["error_code"] == "USER_FORBIDDEN"

        res, code = unauthorized_response("Unauthorized test")
        assert code == 401
        assert res.get_json()["error_code"] == "UNAUTHORIZED"


def test_order_status_transition_validator():
    """Test business logic status transition rules."""
    # Valid transitions for admin
    assert validate_order_status_transition("pending", "paid", is_admin=True) is None
    assert validate_order_status_transition("paid", "processing", is_admin=True) is None
    assert validate_order_status_transition("processing", "shipped", is_admin=True) is None
    assert validate_order_status_transition("shipped", "delivered", is_admin=True) is None

    # Invalid transitions
    err = validate_order_status_transition("pending", "pending", is_admin=True)
    assert err is not None

    err = validate_order_status_transition("delivered", "pending", is_admin=True)
    assert err is not None

    # Customer restricted transitions (cannot directly ship or deliver)
    err = validate_order_status_transition("processing", "shipped", is_admin=False)
    assert err is not None


def test_order_cancellation_validator():
    """Test order cancellation eligibility rules."""
    assert validate_order_cancellation("pending") is None
    assert validate_order_cancellation("paid") is None

    assert validate_order_cancellation("processing") is not None
    assert validate_order_cancellation("shipped") is not None
    assert validate_order_cancellation("delivered") is not None
    assert validate_order_cancellation("cancelled") is not None
