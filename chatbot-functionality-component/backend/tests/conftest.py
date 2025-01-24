"""Pytest configuration file for backend tests."""

import os
import pytest
from app import create_app, db
from app.models import User

@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application."""
    app = create_app('testing')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'AWS_S3_BUCKET': 'test-bucket',
        'MAX_CONTENT_LENGTH': 50 * 1024 * 1024  # 50MB max file size
    })
    return app

@pytest.fixture(scope='session')
def test_client(app):
    """Create a test client for the application."""
    return app.test_client()

@pytest.fixture(scope='function')
def init_database(app):
    """Initialize test database before each test function."""
    with app.app_context():
        db.create_all()
        # Create test user
        user = User(id=1, username='testuser')
        db.session.add(user)
        db.session.commit()
        yield db
        db.session.rollback()
        db.drop_all()

@pytest.fixture(scope='function')
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\nTest content for PDF file\n%EOF\n')
    return str(pdf_path)

@pytest.fixture(scope='function')
def auth_headers():
    """Create authentication headers for testing."""
    return {'Authorization': 'Bearer test-token'}