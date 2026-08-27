import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from sqlalchemy import text
from app.config import Config
from app.extensions import db, migrate, api, jwt, cors

logger = logging.getLogger(__name__)


def setup_logging(app=None):
    """Sets up root and application logging handlers (Console StreamHandler + TimedRotatingFileHandler)."""
    log_level = Config.get_log_level()
    formatter = logging.Formatter(Config.LOG_FORMAT, datefmt=Config.LOG_DATE_FORMAT)

    # Console handler — output to terminal / stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler — daily rotation, retain last 7 days
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8',
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = '%Y-%m-%d'

    # Set root logger cleanly
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def create_app(config_class=Config):
    flask_app = Flask(__name__)

    if isinstance(config_class, dict):
        flask_app.config.from_object(Config)
        flask_app.config.update(config_class)
    elif config_class is not None:
        flask_app.config.from_object(config_class)

    # Setup application logging
    setup_logging(flask_app)
    logger.info("Initializing RevoFashion Flask application")

    # SQLite compatibility: clean up pool options and ensure static pool for in-memory DB
    db_uri = flask_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite'):
        from sqlalchemy.pool import StaticPool
        flask_app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'poolclass': StaticPool,
            'connect_args': {'check_same_thread': False}
        }

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
        logger.warning("Bad request on %s: %s", request.path, err)
        return jsonify({
            "error_code": "BAD_REQUEST",
            "message": "The request body is malformed or contains invalid JSON."
        }), 400

    @flask_app.errorhandler(404)
    def handle_not_found(err):
        """Route / resource not found."""
        logger.warning("Route not found: %s %s", request.method, request.path)
        return jsonify({
            "error_code": "NOT_FOUND",
            "message": "The requested resource or endpoint does not exist."
        }), 404

    @flask_app.errorhandler(405)
    def handle_method_not_allowed(err):
        """HTTP method not allowed on this endpoint."""
        logger.warning("Method not allowed: %s on %s", request.method, request.path)
        return jsonify({
            "error_code": "METHOD_NOT_ALLOWED",
            "message": "The HTTP method used is not allowed for this endpoint."
        }), 405

    @flask_app.errorhandler(422)
    def handle_unprocessable_entity(err):
        """Flask-Smorest / Marshmallow validation failure (schema errors)."""
        # err.data is set by flask-smorest when it raises a 422
        messages = getattr(err, "data", {}).get("messages", {})
        logger.warning("Validation error on %s %s: %s", request.method, request.path, messages)
        return jsonify({
            "error_code": "VALIDATION_ERROR",
            "message": "Request body failed validation.",
            "details": messages
        }), 422

    @flask_app.errorhandler(500)
    def handle_internal_error(err):
        """Unhandled server error fallback."""
        logger.error("Unhandled internal server error on %s %s: %s", request.method, request.path, err, exc_info=True)
        return jsonify({
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later."
        }), 500

    # JWT error handlers — consistent shape for token issues
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning("Expired JWT token on %s %s", request.method, request.path)
        return jsonify({
            "error_code": "TOKEN_EXPIRED",
            "message": "Your access token has expired. Please log in again."
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        logger.warning("Invalid JWT token on %s %s: %s", request.method, request.path, reason)
        return jsonify({
            "error_code": "TOKEN_INVALID",
            "message": f"Invalid token: {reason}."
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        logger.warning("Missing JWT token on %s %s: %s", request.method, request.path, reason)
        return jsonify({
            "error_code": "TOKEN_MISSING",
            "message": "Authorization token is missing. Please include a Bearer token."
        }), 401

    @flask_app.route('/')
    def index():
        logger.info("Accessing index endpoint")
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
            logger.error("Health check failed - database disconnected: %s", e)
            return {
                "status": "unhealthy",
                "database": db_status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, 503

        logger.debug("Health check passed - database connected")
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, 200

    return flask_app

