from sqlalchemy import func
from app.models.user import User
from app.errors import conflict_response, forbidden_response


def validate_user_registration(username: str, email: str):
    """Validates uniqueness of username and email before user registration.

    Returns:
        tuple: (None, None) if valid, or (None, error_response_tuple) if invalid.
    """
    if User.query.filter(func.lower(User.username) == username.lower()).first():
        return conflict_response('USER_NAME_CONFLICT', 'Username already exists.')

    if User.query.filter(func.lower(User.email) == email.lower()).first():
        return conflict_response('USER_EMAIL_CONFLICT', 'Email already exists.')

    return None


def validate_user_update(target_user: User, user_data: dict, requester: User):
    """Validates permissions and uniqueness constraints for updating a user profile.

    Returns:
        tuple: None if valid, or error_response_tuple if validation fails.
    """
    requester_id = requester.id
    is_superadmin = (requester.role == 'superadmin')
    target_id = target_user.id

    # Non-superadmins can only update their own profile
    if not is_superadmin and requester_id != target_id:
        return forbidden_response('You do not have permission to update this profile.', error_code='USER_FORBIDDEN')

    # Non-superadmins cannot modify role or is_active
    if not is_superadmin and ('role' in user_data or 'is_active' in user_data):
        return forbidden_response('Only superadmin can update role and is_active.', error_code='USER_FORBIDDEN')

    # Validate username uniqueness
    if 'username' in user_data:
        username = user_data['username'].strip()
        conflict = User.query.filter(
            func.lower(User.username) == username.lower(),
            User.id != target_id
        ).first()
        if conflict:
            return conflict_response('USER_NAME_CONFLICT', 'Username already exists.')

    # Validate email uniqueness
    if 'email' in user_data:
        email = user_data['email'].strip().lower()
        conflict = User.query.filter(
            func.lower(User.email) == email.lower(),
            User.id != target_id
        ).first()
        if conflict:
            return conflict_response('USER_EMAIL_CONFLICT', 'Email already exists.')

    return None
