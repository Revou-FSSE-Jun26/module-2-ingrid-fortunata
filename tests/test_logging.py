import os
import logging
from unittest.mock import patch
import pytest
from app.config import Config
from app import create_app, setup_logging


def test_config_log_level_direct_override():
    """Verify LOG_LEVEL env override takes top priority."""
    with patch.dict(os.environ, {"LOG_LEVEL": "warning", "FLASK_ENV": "local"}):
        with patch.object(Config, 'LOG_LEVEL', 'warning'):
            assert Config.get_log_level() == "WARNING"


def test_config_log_level_by_flask_env():
    """Verify log levels mapped by FLASK_ENV when LOG_LEVEL is not set."""
    with patch.object(Config, 'LOG_LEVEL', None):
        with patch.dict(os.environ, {"FLASK_ENV": "local"}):
            assert Config.get_log_level() == "DEBUG"

        with patch.dict(os.environ, {"FLASK_ENV": "development"}):
            assert Config.get_log_level() == "INFO"

        with patch.dict(os.environ, {"FLASK_ENV": "production"}):
            assert Config.get_log_level() == "WARNING"

        with patch.dict(os.environ, {"FLASK_ENV": "unknown_env"}):
            assert Config.get_log_level() == "DEBUG"


def test_setup_logging_attaches_handlers(app):
    """Verify setup_logging attaches StreamHandler and TimedRotatingFileHandler."""
    setup_logging(app)
    root_logger = logging.getLogger()
    handler_types = [type(h).__name__ for h in root_logger.handlers]

    assert "StreamHandler" in handler_types
    assert "TimedRotatingFileHandler" in handler_types


def test_logging_writes_to_file_and_stream(client):
    """Verify logging functions normally during app execution and writes to log file."""
    res = client.get('/')
    assert res.status_code == 200

    log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    assert os.path.exists(log_file_path)

    with open(log_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "Initializing RevoFashion Flask application" in content or "Accessing index endpoint" in content
