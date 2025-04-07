import os

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import get_db
from app.main import app
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


@pytest.fixture(scope="function")
def db():
    """Creates a new database session for a test."""

    Base.metadata.create_all(bind=test_engine)  # Create tables before test

    db_session = TestingSessionLocal()

    try:
        yield db_session  # Provide session to test
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)  # Cleanup after test


@pytest.fixture(scope="function")
def client(db):
    """Override the database dependency and provide a test client."""

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db  # Override get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mark_token(client):
    def _mark_token(token, is_stable):
        payload = {"token": token, "is_stable": is_stable}
        response = client.post("/tokens", json=payload)
        assert response.status_code == 200

    return _mark_token


@given("the API is running")
def api_is_running(client):
    response = client.get("/")
    assert response.status_code == 200
