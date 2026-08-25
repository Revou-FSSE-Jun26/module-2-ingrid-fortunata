"""Tests for seed_data script."""

import pytest
from app.extensions import db
from app.seed_data import seed_database
from app.models.category import Category
from app.models.product import Product
from app.models.user import User


def test_seed_database_execution(app):
    """Verify seed_database executes and populates fashion categories, products, and users on clean and existing DB."""
    with app.app_context():
        db.drop_all()
        db.create_all()

    # 1. First run: Seeds clean database from scratch
    seed_database(app)

    with app.app_context():
        assert Category.query.count() >= 8
        assert Product.query.count() >= 15
        assert User.query.filter_by(username="alice_smith").first() is not None

    # 2. Second run: Tests idempotency (all entities already exist)
    seed_database(app)


def test_seed_database_default_app(app):
    """Verify seed_database when app=None calls create_app."""
    from unittest.mock import patch
    with patch("app.seed_data.create_app", return_value=app):
        seed_database(None)
