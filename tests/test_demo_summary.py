"""
Tests demonstrating Pytest Best Practices:
1. Testing for Exceptions with pytest.raises()
2. Checking the exception message with regex/match and exc_info
3. Checking failures with pytest.mark.xfail and assert diffs
4. Reading Passing + Failing Summaries
"""

import pytest
from marshmallow import ValidationError
from app.schemas.user import not_blank, UserRegisterInputSchema


def divide(a: float, b: float) -> float:
    """Helper function to demonstrate exception testing."""
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero.")
    return a / b


# ==============================================================================
# 1. Testing for Exceptions with pytest.raises()
# ==============================================================================

def test_exception_raised_zero_division():
    """Verify that dividing by zero raises ZeroDivisionError using pytest.raises()."""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)


def test_exception_raised_validation_error():
    """Verify that empty string raises ValidationError in not_blank validator."""
    with pytest.raises(ValidationError):
        not_blank("")


# ==============================================================================
# 2. Checking the Exception Message
# ==============================================================================

def test_exception_message_using_match_parameter():
    """Check the exception message using the `match` regex parameter in pytest.raises()."""
    # Regex match checks if the exception message contains the pattern
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero."):
        divide(100, 0)


def test_exception_message_using_exc_info():
    """Inspect exception message and details via `exc_info.value`."""
    with pytest.raises(ValidationError) as exc_info:
        not_blank("   ")  # Whitespace only

    # 1. Convert exception to string and check substring
    error_message = str(exc_info.value)
    assert "Field cannot be blank or whitespace only." in error_message

    # 2. Check the exception type
    assert exc_info.type is ValidationError


def test_marshmallow_schema_validation_message_match():
    """Check structured validation error messages raised by Marshmallow."""
    invalid_payload = {
        "username": "user with spaces",
        "email": "invalid-email-format",
        "password": "123"  # too short
    }

    with pytest.raises(ValidationError) as exc_info:
        UserRegisterInputSchema().load(invalid_payload)

    errors = exc_info.value.messages
    # Verify specific error messages in the schema errors dict
    assert "username" in errors
    assert "Username cannot contain spaces." in errors["username"]
    assert "email" in errors
    assert "password" in errors


# ==============================================================================
# 3. Checking Failure & Expected Failures (xfail)
# ==============================================================================

@pytest.mark.xfail(reason="Demonstrating expected failure handling without breaking CI", strict=True)
def test_demonstrate_expected_failure():
    """This test is expected to fail. Using @pytest.mark.xfail marks it as XFAIL instead of FAILED."""
    expected_sum = 10
    actual_sum = 2 + 2
    assert actual_sum == expected_sum, f"Expected {expected_sum} but got {actual_sum}"


def test_assertion_success():
    """A standard passing assert statement."""
    product = {"name": "T-Shirt", "price": 25.0, "stock": 10}
    assert product["name"] == "T-Shirt"
    assert product["price"] > 0
    assert product["stock"] >= 0


# ==============================================================================
# 4. Guide on Reading Passing + Failing Summaries
# ==============================================================================
#
# When running tests via terminal:
#
# Command:
#   pytest tests/ -v
#
# Output Explanation:
#   - PASSED (green dot / text): The test asserted successfully.
#   - FAILED (red F / text): An assert failed or an unexpected exception occurred.
#   - XFAIL (yellow x): Expected failure (test failed as expected).
#   - XPASS (yellow X): Unexpected pass (test marked as xfail but actually passed).
#
# Summary Section at Bottom of Output:
#   =========================== short test summary info ============================
#   FAILED tests/test_example.py::test_failing_case - AssertionError: assert 4 == 10
#   =================== 1 failed, 25 passed, 1 xfailed in 0.35s ====================
#
