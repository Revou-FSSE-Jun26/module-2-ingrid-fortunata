import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    # Environment and secret key configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        if os.getenv('FLASK_ENV') == 'production':
            raise ValueError("CRITICAL: SECRET_KEY environment variable MUST be set in production!")
        SECRET_KEY = 'default-dev-key-revoshop'

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # CORS configuration
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', '*').split(',') if origin.strip()]
    
    # Configure PostgreSQL database URI
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://postgres:postgres@localhost:5432/revoshop_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database connection pooling settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,          # Persistent connections maintained in pool
        'max_overflow': 20,       # Extra burst connections under spike load
        'pool_timeout': 30,       # Max seconds to wait for a connection
        'pool_recycle': 1800,     # Recycle connections every 30 mins to prevent stale drops
        'pool_pre_ping': True     # Liveness health check before using pooled connection
    }

    # Supabase Storage configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://shgafjqeprksdawepfcl.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'products')

    # OpenAPI/Swagger UI configuration
    API_TITLE = "RevoFashion API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    API_SPEC_OPTIONS = {
        'components': {
            'securitySchemes': {
                'BearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT',
                    'description': 'JWT Bearer token. Enter your token (without the "Bearer " prefix, Swagger UI will add it automatically).'
                }
            }
        }
    }


    # Logging configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'local')
    LOG_LEVEL = os.getenv('LOG_LEVEL', None)
    LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_LEVEL_MAP = {
        'local': 'DEBUG',
        'development': 'INFO',
        'production': 'WARNING',
    }

    @classmethod
    def get_log_level(cls):
        """Priority: LOG_LEVEL env var > FLASK_ENV mapping > default DEBUG"""
        if cls.LOG_LEVEL:
            return cls.LOG_LEVEL.upper()
        flask_env = os.getenv('FLASK_ENV', cls.FLASK_ENV)
        return cls.LOG_LEVEL_MAP.get(flask_env, 'DEBUG')

