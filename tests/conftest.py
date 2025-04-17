import os

import pytest
from pytest_bdd import given, parsers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.models import Base

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create a test database engine
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _configure_test_env():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    get_settings.cache_clear()  # next call to get_settings() will re-read env


@pytest.fixture(scope="session")
def db():
    """Creates a new database session for a test."""

    Base.metadata.create_all(bind=test_engine)  # Create tables before test

    db_session = TestingSessionLocal()

    try:
        yield db_session  # Provide session to test
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)  # Cleanup after test


@given(parsers.parse('"{token}" is marked as a stablecoin'))
def mark_as_stablecoin(token, mark_token):
    mark_token(token, is_stable=True)


@given(parsers.parse('"{token}" is marked as a non-stablecoin'))
def mark_token_as_non_stablecoin(token, mark_token):
    mark_token(token, is_stable=False)
