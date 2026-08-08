from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['POST'])
def register_user():
    """Register a new user in the database using db.session.add() and db.session.commit()."""
    data = request.get_json() or {}
    
    # Simple validation
    username = data.get('username')
    email = data.get('email')
    password_hash = data.get('password_hash') or data.get('password')
    role = data.get('role', 'user')

    if not username or not email or not password_hash:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'message': 'username, email, and password (or password_hash) are required.'
        }), 400

    # Check for existing user
    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'error': 'Conflict',
            'message': 'Username already exists.'
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'error': 'Conflict',
            'message': 'Email already exists.'
        }), 400

    # Create new User instance
    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )
    
    # Assign role if column exists on model
    if hasattr(User, 'role'):
        setattr(new_user, 'role', role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'data': new_user.to_dict()
    }), 201

@users_bp.route('/users/<int:id>', methods=['GET'])
def get_user_by_id(id):
    """Fetches and returns a user by ID, handling the 404 case where user is not found."""
    user = db.session.get(User, id)
    if not user:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f'User with ID {id} not found.'
        }), 404

    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 200

