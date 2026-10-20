"""
Pytest Fixtures for CareerKit AI Test Suite
Provides test application client and isolated temporary SQLite database.
"""

import os
import tempfile
import pytest
from app import create_app
from config import TestConfig
from services.database import init_db


@pytest.fixture
def app():
    """Creates a test Flask application configured with a temporary SQLite DB."""
    # Create isolated temp database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    class CurrentTestConfig(TestConfig):
        DATABASE_PATH = db_path
        WTF_CSRF_ENABLED = False

    test_app = create_app(CurrentTestConfig)
    with test_app.app_context():
        init_db(db_path)
        yield test_app

    # Teardown: Remove temporary database file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture
def client(app):
    """Provides a test client for simulating HTTP requests."""
    return app.test_client()
