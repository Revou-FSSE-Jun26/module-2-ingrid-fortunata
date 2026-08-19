from flask import jsonify


def error_response(error_code: str, message: str, status_code: int = 400):
    """Returns a standard JSON error response across all application endpoints.

    Format:
    {
        "error_code": "...",
        "message": "..."
    }, status_code
    """
    return jsonify({
        "error_code": error_code,
        "message": message
    }), status_code


def not_found_response(resource_name: str, resource_id=None):
    """Shortcut for 404 resource not found errors."""
    if resource_id is not None:
        message = f"No {resource_name.lower()} exists with ID {resource_id}."
    else:
        message = f"{resource_name} not found."
    return error_response(f"{resource_name.upper()}_NOT_FOUND", message, 404)


def conflict_response(error_code: str, message: str):
    """Shortcut for 409 conflict errors."""
    return error_response(error_code, message, 409)


def forbidden_response(message: str = "You do not have permission to perform this action.", error_code: str = "FORBIDDEN"):
    """Shortcut for 403 forbidden errors."""
    return error_response(error_code, message, 403)


def unauthorized_response(message: str = "Missing or invalid authorization token.", error_code: str = "UNAUTHORIZED"):
    """Shortcut for 401 unauthorized errors."""
    return error_response(error_code, message, 401)

