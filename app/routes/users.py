from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.models.user import User
from app.auth import roles_required
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
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

users_bp = Blueprint('users', __name__, description='Operations on users')



@users_bp.route('/users', methods=['POST'])
@users_bp.arguments(UserRegisterInputSchema, location='json')
@users_bp.response(201, UserRegisterResponseSchema)
def register_user(user_data):
    """Register a new user. Role defaults to 'customer' — role assignment is a privileged admin action."""
    username = user_data.get('username', '').strip()
    email = user_data.get('email', '').strip().lower()
    raw_password = user_data.get('password')

    # Duplicate checks via validator
    err = validate_user_registration(username, email)
    if err:
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
    except IntegrityError:
        db.session.rollback()
        return conflict_response('USER_CONFLICT', 'Username or email already exists.')
    except SQLAlchemyError:
        db.session.rollback()
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

    raw_page = request.args.get('page', None, type=int)
    raw_per_page = request.args.get('per_page', None, type=int)

    page = max(1, raw_page) if raw_page is not None else 1
    per_page = min(100, max(1, raw_per_page)) if raw_per_page is not None else 10

    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()

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
    requester_id = int(get_jwt_identity())
    requester = db.session.get(User, requester_id)
    if not requester:
        return unauthorized_response('Authenticated user not found.')

    is_admin = requester.role in ['superadmin', 'admin']
    if not is_admin and requester_id != id:
        return forbidden_response('You do not have permission to view this profile.', error_code='USER_FORBIDDEN')

    user = db.session.get(User, id)
    if not user:
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
    requester_id = int(get_jwt_identity())
    requester = db.session.get(User, requester_id)
    if not requester:
        return unauthorized_response('Authenticated user not found.')

    if not requester.is_active:
        return error_response('USER_DEACTIVATED', 'Account is deactivated.', 403)

    user = db.session.get(User, id)
    if not user:
        return not_found_response('User', id)

    # Validate permissions & unique constraints via validator
    err = validate_user_update(user, user_data, requester)
    if err:
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
    except IntegrityError:
        db.session.rollback()
        return conflict_response('USER_CONFLICT', 'Username or email already exists.')
    except SQLAlchemyError:
        db.session.rollback()
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
    # Look up user by username or email (case-insensitive)
    user = User.query.filter(
        (func.lower(User.username) == identity_clean.lower()) | 
        (func.lower(User.email) == identity_clean.lower())
    ).first()

    # Check is_active BEFORE password to avoid leaking that the password is correct
    # Both "user not found" and "account deactivated" return the same 401 to prevent
    # user enumeration / account-state leakage
    if not user or not user.is_active:
        return error_response('USER_UNAUTHORIZED', 'Invalid username/email or password.', 401)

    if not user.check_password(password):
        return error_response('USER_UNAUTHORIZED', 'Invalid username/email or password.', 401)

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    }), 200
