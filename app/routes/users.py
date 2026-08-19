from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.models.user import User
from app.auth import roles_required
from werkzeug.security import generate_password_hash, check_password_hash
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

users_bp = Blueprint('users', __name__, description='Operations on users')



@users_bp.route('/users', methods=['POST'])
@users_bp.arguments(UserRegisterInputSchema, location='json')
@users_bp.response(201, UserRegisterResponseSchema)
def register_user(user_data):
    """Register a new user. Role defaults to 'customer' — role assignment is a privileged admin action."""
    username = user_data.get('username', '').strip()
    email = user_data.get('email', '').strip().lower()
    raw_password = user_data.get('password')

    # Duplicate checks — 409 Conflict (not 400) for existing resources
    if User.query.filter(func.lower(User.username) == username.lower()).first():
        return jsonify({
            'error_code': 'USER_NAME_CONFLICT',
            'message': 'Username already exists.'
        }), 409

    if User.query.filter(func.lower(User.email) == email).first():
        return jsonify({
            'error_code': 'USER_EMAIL_CONFLICT',
            'message': 'Email already exists.'
        }), 409

    password_hash = generate_password_hash(raw_password)

    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role='customer'   # hardcoded — public registration cannot choose role
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error_code': 'USER_CONFLICT',
            'message': 'Username or email already exists.'
        }), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            'error_code': 'USER_DATABASE_ERROR',
            'message': 'An error occurred while creating the user.'
        }), 500

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
        return jsonify({
            'error_code': 'USER_NOT_FOUND',
            'message': 'Authenticated user not found.'
        }), 401

    is_admin = requester.role in ['superadmin', 'admin']
    if not is_admin and requester_id != id:
        return jsonify({
            'error_code': 'USER_FORBIDDEN',
            'message': 'You do not have permission to view this profile.'
        }), 403

    user = db.session.get(User, id)
    if not user:
        return jsonify({
            'error_code': 'USER_NOT_FOUND',
            'message': f'User with ID {id} not found.'
        }), 404

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
        return jsonify({
            'error_code': 'USER_NOT_FOUND',
            'message': 'Authenticated user not found.'
        }), 401

    if not requester.is_active:
        return jsonify({
            'error_code': 'USER_DEACTIVATED',
            'message': 'Account is deactivated.'
        }), 403

    is_superadmin = (requester.role == 'superadmin')

    # Non-superadmins can only update their own profile
    if not is_superadmin and requester_id != id:
        return jsonify({
            'error_code': 'USER_FORBIDDEN',
            'message': 'You do not have permission to update this profile.'
        }), 403

    # Non-superadmins cannot modify role or is_active
    if not is_superadmin and ('role' in user_data or 'is_active' in user_data):
        return jsonify({
            'error_code': 'USER_FORBIDDEN',
            'message': 'Only superadmin can update role and is_active.'
        }), 403

    user = db.session.get(User, id)
    if not user:
        return jsonify({
            'error_code': 'USER_NOT_FOUND',
            'message': f'User with ID {id} not found.'
        }), 404

    # Validate and apply username update
    if 'username' in user_data:
        username = user_data['username'].strip()
        conflict = User.query.filter(func.lower(User.username) == username.lower(), User.id != id).first()
        if conflict:
            return jsonify({
                'error_code': 'USER_NAME_CONFLICT',
                'message': 'Username already exists.'
            }), 409
        user.username = username

    # Validate and apply email update
    if 'email' in user_data:
        email = user_data['email'].strip().lower()
        conflict = User.query.filter(func.lower(User.email) == email.lower(), User.id != id).first()
        if conflict:
            return jsonify({
                'error_code': 'USER_EMAIL_CONFLICT',
                'message': 'Email already exists.'
            }), 409
        user.email = email

    # Superadmin-only updates
    if is_superadmin:
        if 'role' in user_data:
            user.role = user_data['role'].strip().lower()
        if 'is_active' in user_data:
            user.is_active = user_data['is_active']

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error_code': 'USER_CONFLICT',
            'message': 'Username or email already exists.'
        }), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            'error_code': 'USER_DATABASE_ERROR',
            'message': 'An error occurred while updating the user.'
        }), 500

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
        return jsonify({
            'error_code': 'USER_UNAUTHORIZED',
            'message': 'Invalid username/email or password.'
        }), 401

    # Verify password
    is_password_correct = False
    if user.password_hash.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
        try:
            is_password_correct = check_password_hash(user.password_hash, password)
        except ValueError:
            is_password_correct = False
    else:
        # Plaintext fallback for legacy/test users
        is_password_correct = (user.password_hash == password)

    if not is_password_correct:
        return jsonify({
            'error_code': 'USER_UNAUTHORIZED',
            'message': 'Invalid username/email or password.'
        }), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    }), 200
