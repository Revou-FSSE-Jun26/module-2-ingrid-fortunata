from flask_smorest import Blueprint
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.schemas import (
    UserRegisterInputSchema,
    UserRegisterResponseSchema,
    UserLoginInputSchema,
    UserGetResponseSchema,
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
    if User.query.filter_by(username=username).first():
        return jsonify({
            'error_code': 'USER_NAME_CONFLICT',
            'message': 'Username already exists.'
        }), 409

    if User.query.filter_by(email=email).first():
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


@users_bp.route('/auth/login', methods=['POST'])
@users_bp.arguments(UserLoginInputSchema, location='json')
@users_bp.response(200, AuthLoginResponseSchema)
def login_auth(login_data):
    """Login endpoint returning JWT token expiring in 1 day."""
    identity = login_data.get('username') or login_data.get('email')
    password = login_data.get('password')

    # Look up user by username or email
    user = User.query.filter(
        (User.username == identity) | (User.email == identity)
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
