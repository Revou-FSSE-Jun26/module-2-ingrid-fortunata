"""Tests for application configuration in app/config.py."""

import os
from unittest.mock import patch
import pytest


def test_production_missing_secret_key_raises():
    """Verify missing SECRET_KEY in production raises ValueError."""
    with patch.dict(os.environ, {"SECRET_KEY": "", "FLASK_ENV": "production"}):
        import importlib
        import app.config
        with pytest.raises(ValueError, match="CRITICAL: SECRET_KEY environment variable MUST be set in production!"):
            importlib.reload(app.config)


def test_development_missing_secret_key_default():
    """Verify missing SECRET_KEY in non-production defaults to dev key."""
    with patch.dict(os.environ, {"SECRET_KEY": "", "FLASK_ENV": "development"}):
        import importlib
        import app.config
        importlib.reload(app.config)
        assert app.config.Config.SECRET_KEY == "default-dev-key-revoshop"


def test_database_url_postgres_prefix_replacement():
    """Verify postgres:// is converted to postgresql://."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@localhost:5432/db", "SECRET_KEY": "dev-key", "FLASK_ENV": "development"}):
        import importlib
        import app.config
        importlib.reload(app.config)
        assert app.config.Config.SQLALCHEMY_DATABASE_URI.startswith("postgresql://")
