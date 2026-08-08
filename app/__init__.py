from flask import Flask
from app.config import Config
from app.extensions import db, migrate

def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    # Import models to ensure they are registered with SQLAlchemy/Migrate
    import app.models

    # Register blueprints
    from app.routes.products import products_bp
    from app.routes.users import users_bp

    flask_app.register_blueprint(products_bp)
    flask_app.register_blueprint(users_bp)

    @flask_app.route('/')
    def index():
        return {
            "name": "RevoShop API",
            "version": "1.0",
            "checkpoint": 2,
            "status": "online"
        }

    return flask_app

