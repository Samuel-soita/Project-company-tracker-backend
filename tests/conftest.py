# tests/conftest.py
import pytest
from unittest.mock import patch
from run import create_app
from app.models import db, User
from flask import request as flask_request
import os

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:newpassword@localhost:5432/projectx_db"
        ),
        "SECRET_KEY": "testsecretkey",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        db.create_all()  # Ensure tables exist
        yield app
        db.session.remove()
        db.drop_all()  # Clean up after tests

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# -----------------------------
# Mock email sending for 2FA
# -----------------------------
@pytest.fixture(autouse=True)
def mock_email_sending(app):
    """
    Mock email sending functions to avoid external calls during tests.
    """
    from app.utils import email_utils

    # Mock 2FA email sending
    with patch("app.utils.email_utils.send_2fa_code_email") as mock_send:
        mock_send.return_value = True
        yield mock_send

# -----------------------------
# Ensure admin exists
# -----------------------------
@pytest.fixture(autouse=True)
def ensure_admin_exists(app):
    """Ensure an admin user exists in the test DB."""
    with app.app_context():
        manager = User.query.filter_by(email="manager@test.com").first()
        if not manager:
            manager = User(
                name="Manager",
                email="manager@test.com",
                role="Manager"
            )
            manager.set_password("adminpass")
            db.session.add(manager)
            db.session.commit()

# -----------------------------
# Seed a test student
# -----------------------------
@pytest.fixture(autouse=True)
def seed_test_users(app):
    """Ensure a test student user exists in the test DB."""
    with app.app_context():
        employee = User.query.filter_by(email="employee1@company.com").first()
        if not employee:
            employee = User(
                name="Employee 1",
                email="employee1@company.com",
                role="Employee"
            )
            employee.set_password("employeepass")
            db.session.add(employee)
            db.session.commit()
