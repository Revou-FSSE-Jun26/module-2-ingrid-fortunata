from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.extensions import db

from app.errors import unauthorized_response, forbidden_response


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
                return unauthorized_response("Missing or invalid authorization token.")
                
            # Fetch user from the database
            user = db.session.get(User, int(user_id))
            if not user:
                return unauthorized_response("User not found.")
                
            # Verify user is active
            if not user.is_active:
                return forbidden_response("Account is deactivated.")

            # Check if user's role is permitted
            if user.role not in roles:
                return forbidden_response("You do not have permission to perform this action.")
                
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
