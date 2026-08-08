import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key-revoshop')
    
    # Configure PostgreSQL database URI
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://postgres:postgres@localhost:5432/revoshop_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
