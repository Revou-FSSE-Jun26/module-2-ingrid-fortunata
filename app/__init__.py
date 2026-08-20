from datetime import datetime, timezone
from flask import Flask, jsonify
from sqlalchemy import text
from app.config import Config
from app.extensions import db, migrate, api, jwt, cors


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    cors.init_app(
        flask_app,
        resources={r"/*": {"origins": flask_app.config.get('CORS_ALLOWED_ORIGINS', '*')}},
        supports_credentials=True
    )
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    api.init_app(flask_app)
    jwt.init_app(flask_app)

    # Import models to ensure they are registered with SQLAlchemy/Migrate
    import app.models

    # Register blueprints
    from app.routes.products import products_bp
    from app.routes.users import users_bp
    from app.routes.categories import categories_bp
    from app.routes.orders import orders_bp

    api.register_blueprint(products_bp)
    api.register_blueprint(users_bp)
    api.register_blueprint(categories_bp)
    api.register_blueprint(orders_bp)

    # ------------------------------------------------------------------ #
    # Global HTTP error handlers                                           #
    # Ensures ALL error responses use the same {error_code, message} shape #
    # ------------------------------------------------------------------ #

    @flask_app.errorhandler(400)
    def handle_bad_request(err):
        """Malformed JSON or bad syntax in request body."""
        return jsonify({
            "error_code": "BAD_REQUEST",
            "message": "The request body is malformed or contains invalid JSON."
        }), 400

    @flask_app.errorhandler(404)
    def handle_not_found(err):
        """Route / resource not found."""
        return jsonify({
            "error_code": "NOT_FOUND",
            "message": "The requested resource or endpoint does not exist."
        }), 404

    @flask_app.errorhandler(405)
    def handle_method_not_allowed(err):
        """HTTP method not allowed on this endpoint."""
        return jsonify({
            "error_code": "METHOD_NOT_ALLOWED",
            "message": "The HTTP method used is not allowed for this endpoint."
        }), 405

    @flask_app.errorhandler(422)
    def handle_unprocessable_entity(err):
        """Flask-Smorest / Marshmallow validation failure (schema errors)."""
        # err.data is set by flask-smorest when it raises a 422
        messages = getattr(err, "data", {}).get("messages", {})
        return jsonify({
            "error_code": "VALIDATION_ERROR",
            "message": "Request body failed validation.",
            "details": messages
        }), 422

    @flask_app.errorhandler(500)
    def handle_internal_error(err):
        """Unhandled server error fallback."""
        return jsonify({
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later."
        }), 500

    # JWT error handlers — consistent shape for token issues
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error_code": "TOKEN_EXPIRED",
            "message": "Your access token has expired. Please log in again."
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({
            "error_code": "TOKEN_INVALID",
            "message": f"Invalid token: {reason}."
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({
            "error_code": "TOKEN_MISSING",
            "message": "Authorization token is missing. Please include a Bearer token."
        }), 401

    @flask_app.route('/')
    def index():
        return {
            "name": "RevoFashion API",
            "version": "1.0",
            "checkpoint": 2,
            "status": "online"
        }

    @flask_app.route('/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            db_status = "connected"
        except Exception as e:
            db_status = f"disconnected: {str(e)}"
            return {
                "status": "unhealthy",
                "database": db_status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, 503

        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, 200

    return flask_app
