from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.extensions import db

def roles_required(*roles):
    """Decorator to restrict access to endpoints based on user roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Verify that JWT is present and valid
            verify_jwt_in_request()
            
            # Retrieve identity (user ID) from the JWT
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({
                    "error_code": "UNAUTHORIZED",
                    "message": "Missing or invalid authorization token."
                }), 401
                
            # Fetch user from the database
            user = db.session.get(User, int(user_id))
            if not user:
                return jsonify({
                    "error_code": "UNAUTHORIZED",
                    "message": "User not found."
                }), 401
                
            # Verify user is active
            if not user.is_active:
                return jsonify({
                    "error_code": "FORBIDDEN",
                    "message": "Account is deactivated."
                }), 403

            # Check if user's role is permitted
            if user.role not in roles:
                return jsonify({
                    "error_code": "FORBIDDEN",
                    "message": "You do not have permission to perform this action."
                }), 403
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def is_admin_user():
    """Returns True if the current request carries a valid JWT belonging to an active admin/superadmin."""
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user = db.session.get(User, int(user_id))
            return bool(user and user.is_active and user.role in ['superadmin', 'admin'])
    except Exception:
        pass
    return False
