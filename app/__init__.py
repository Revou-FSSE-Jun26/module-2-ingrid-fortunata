from flask import Flask
from app.config import Config
from app.extensions import db, migrate, api, jwt

def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize extensions
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


    @flask_app.route('/')
    def index():
        return {
            "name": "RevoShop API",
            "version": "1.0",
            "checkpoint": 2,
            "status": "online"
        }

    return flask_app

