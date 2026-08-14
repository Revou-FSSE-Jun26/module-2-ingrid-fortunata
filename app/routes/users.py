from flask_smorest import Blueprint
from flask import jsonify
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.schemas import UserRegisterInputSchema, UserRegisterResponseSchema, UserLoginInputSchema, UserGetResponseSchema, AuthLoginResponseSchema

users_bp = Blueprint('users', __name__, description='Operations on users')

@users_bp.route('/users', methods=['POST'])
@users_bp.arguments(UserRegisterInputSchema, location='json')
@users_bp.response(201, UserRegisterResponseSchema)
def register_user(user_data):
    """Register a new user with password hashing."""
    username = user_data.get('username')
    email = user_data.get('email')
    raw_password = user_data.get('password') or user_data.get('password_hash')
    role = user_data.get('role', 'user')

    # Hash password
    password_hash = generate_password_hash(raw_password)

    if User.query.filter_by(username=username).first():
        return jsonify({
            'error_code': 'CONFLICT',
            'message': 'Username already exists.'
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            'error_code': 'CONFLICT',
            'message': 'Email already exists.'
        }), 400

    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )
    
    new_user.role = role

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'data': new_user.to_dict()
    }), 201

@users_bp.route('/users/<int:id>', methods=['GET'])
@users_bp.response(200, UserGetResponseSchema)
def get_user_by_id(id):
    """Fetches and returns a user by ID, handling 404."""
    user = db.session.get(User, id)
    if not user:
        return jsonify({
            'error_code': 'NOT_FOUND',
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

    if not identity or not password:
        return jsonify({
            'error_code': 'VALIDATION_ERROR',
            'message': 'username/email and password are required.'
        }), 400

    user = User.query.filter((User.username == identity) | (User.email == identity)).first()

    if not user:
        return jsonify({
            'error_code': 'UNAUTHORIZED',
            'message': 'Invalid username/email or password.'
        }), 401

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
            'error_code': 'UNAUTHORIZED',
            'message': 'Invalid username/email or password.'
        }), 401

    if not user.is_active:
        return jsonify({
            'error_code': 'FORBIDDEN',
            'message': 'Account is deactivated.'
        }), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    }), 200

