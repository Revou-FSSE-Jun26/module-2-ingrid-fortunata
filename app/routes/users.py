import logging
from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required
from app.auth import roles_required, get_current_user
from app.schemas import (
    UserRegisterInputSchema,
    UserRegisterResponseSchema,
    UserLoginInputSchema,
    UserGetResponseSchema,
    UserListResponseSchema,
    UserUpdateInputSchema,
    AuthLoginResponseSchema,
)

from app.errors import error_response, not_found_response, forbidden_response, unauthorized_response, conflict_response
from app.validators import validate_user_registration, validate_user_update
from app.utils.pagination import get_page_params

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__, description='Operations on users')



@users_bp.route('/users', methods=['POST'])
@users_bp.arguments(UserRegisterInputSchema, location='json')
@users_bp.response(201, UserRegisterResponseSchema)
def register_user(user_data):
    """Register a new user. Role defaults to 'customer' — role assignment is a privileged admin action."""
    username = user_data.get('username', '').strip()
    email = user_data.get('email', '').strip().lower()
    raw_password = user_data.get('password')
    logger.info("POST /users — registering user '%s' (%s)", username, email)

    # Duplicate checks via validator
    err = validate_user_registration(username, email)
    if err:
        logger.warning("Registration failed validation for username='%s', email='%s'", username, email)
        return err

    new_user = User(
        username=username,
        email=email,
        role='customer'   # hardcoded — public registration cannot choose role
    )
    new_user.set_password(raw_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        logger.info("User registered successfully — id=%d, username='%s'", new_user.id, new_user.username)
    except IntegrityError:
        db.session.rollback()
        logger.warning("Registration IntegrityError — duplicate username or email: '%s' / '%s'", username, email)
        return conflict_response('USER_CONFLICT', 'Username or email already exists.')
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error creating user '%s': %s", username, e, exc_info=True)
        return error_response('USER_DATABASE_ERROR', 'An error occurred while creating the user.', 500)

    return jsonify({
        'data': new_user.to_dict()
    }), 201


@users_bp.route('/users', methods=['GET'])
@roles_required('superadmin')
@users_bp.response(200, UserListResponseSchema)
def get_all_users():
    """Retrieve all users with optional filtering and pagination.
    Restricted strictly to superadmin.
    """
    logger.info("GET /users — superadmin user query")
    role = request.args.get('role', None)
    is_active_raw = request.args.get('is_active', None)
    search = request.args.get('search', None)

    query = User.query.order_by(User.id.asc())

    if role:
        query = query.filter(func.lower(User.role) == role.strip().lower())

    if is_active_raw is not None:
        val = is_active_raw.strip().lower()
        if val in ['true', '1']:
            query = query.filter(User.is_active.is_(True))
        elif val in ['false', '0']:
            query = query.filter(User.is_active.is_(False))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(User.username.ilike(search_term) | User.email.ilike(search_term))

    page, per_page = get_page_params()
    page = page or 1
    per_page = per_page or 10

    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()
    logger.debug("Returning %d users", len(users))

    return jsonify({
        'data': [u.to_dict() for u in users]
    }), 200


@users_bp.route('/users/<int:id>', methods=['GET'])
@jwt_required()
@users_bp.response(200, UserGetResponseSchema)
def get_user_by_id(id):
    """Fetches and returns a user by ID.
    Customers can only view their own profile.
    Admins and superadmins can view any user.
    """
    logger.info("GET /users/%d", id)
    requester = get_current_user()
    if not requester:
        return unauthorized_response('Authenticated user not found.')

    is_admin = requester.role in ['superadmin', 'admin']
    if not is_admin and requester.id != id:
        logger.warning("Forbidden profile access attempt for id=%d by user_id=%d", id, requester.id)
        return forbidden_response('You do not have permission to view this profile.', error_code='USER_FORBIDDEN')

    user = db.session.get(User, id)
    if not user:
        logger.warning("User not found: id=%d", id)
        return not_found_response('User', id)

    return jsonify({
        'data': user.to_dict()
    }), 200


@users_bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
@users_bp.arguments(UserUpdateInputSchema, location='json')
@users_bp.response(200, UserGetResponseSchema)
def update_user_by_id(user_data, id):
    """Update user profile.
    Customers can update only their own username and email.
    Superadmins can update any user's profile, including role and is_active.
    """
    logger.info("PUT /users/%d", id)
    requester = get_current_user()
    if not requester:
        return unauthorized_response('Authenticated user not found.')

    if not requester.is_active:
        logger.warning("Deactivated user %d attempted profile update", requester.id)
        return error_response('USER_DEACTIVATED', 'Account is deactivated.', 403)

    user = db.session.get(User, id)
    if not user:
        logger.warning("Update user failed — User not found: id=%d", id)
        return not_found_response('User', id)

    # Validate permissions & unique constraints via validator
    err = validate_user_update(user, user_data, requester)
    if err:
        logger.warning("User update failed validation for user_id=%d", id)
        return err

    # Apply valid updates
    if 'username' in user_data:
        user.username = user_data['username'].strip()
    if 'email' in user_data:
        user.email = user_data['email'].strip().lower()

    # Superadmin-only updates
    if requester.role == 'superadmin':
        if 'role' in user_data:
            user.role = user_data['role'].strip().lower()
        if 'is_active' in user_data:
            user.is_active = user_data['is_active']

    try:
        db.session.commit()
        logger.info("User updated successfully — id=%d", user.id)
    except IntegrityError:
        db.session.rollback()
        logger.warning("User update IntegrityError — duplicate username or email for id=%d", id)
        return conflict_response('USER_CONFLICT', 'Username or email already exists.')
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating user id=%d: %s", id, e, exc_info=True)
        return error_response('USER_DATABASE_ERROR', 'An error occurred while updating the user.', 500)

    return jsonify({
        'data': user.to_dict()
    }), 200



@users_bp.route('/auth/login', methods=['POST'])
@users_bp.arguments(UserLoginInputSchema, location='json')
@users_bp.response(200, AuthLoginResponseSchema)
def login_auth(login_data):
    """Login endpoint returning JWT token expiring in 1 day."""
    identity = login_data.get('username') or login_data.get('email')
    password = login_data.get('password')

    identity_clean = identity.strip()
    logger.info("POST /auth/login — login attempt for identity '%s'", identity_clean)

    # Look up user by username or email (case-insensitive)
    user = User.query.filter(
        (func.lower(User.username) == identity_clean.lower()) | 
        (func.lower(User.email) == identity_clean.lower())
    ).first()

    # Check is_active BEFORE password to avoid leaking that the password is correct
    # Both "user not found" and "account deactivated" return the same 401 to prevent
    # user enumeration / account-state leakage
    if not user or not user.is_active:
        logger.warning("Login failed — account not found or deactivated for '%s'", identity_clean)
        return error_response('USER_UNAUTHORIZED', 'Invalid username/email or password.', 401)

    if not user.check_password(password):
        logger.warning("Login failed — incorrect password for '%s'", identity_clean)
        return error_response('USER_UNAUTHORIZED', 'Invalid username/email or password.', 401)

    token = create_access_token(identity=str(user.id))
    logger.info("Login successful for user_id=%d ('%s')", user.id, user.username)
    return jsonify({
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    }), 200

