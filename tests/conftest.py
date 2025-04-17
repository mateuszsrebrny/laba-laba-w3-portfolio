import os
from multiprocessing import Process

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from uvicorn import run

from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Base
from tests.config import HEALTH_ENDPOINT

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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def http_server(db):
    """Start a live HTTP server with overridden dependencies."""

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    # Override get_db() to use the test database
    app.dependency_overrides[get_db] = override_get_db

    # Start the server in a separate process
    process = Process(
        target=run, kwargs={"app": app, "host": "127.0.0.1", "port": 11111}
    )
    process.start()
    yield  # Tests will run while this fixture is active
    process.terminate()  # Stop the server after tests are done

    # Clear overrides after stopping the server
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def page(playwright, http_server):  # Ensure http_server is started before tests
    browser = playwright.chromium.launch(headless=True)  # Run in headless mode
    context = browser.new_context()
    yield context.new_page()
    browser.close()


@pytest.fixture
def mark_token(client):
    def _mark_token(token, is_stable):
        payload = {"token": token, "is_stable": is_stable}
        response = client.post("/api/tokens", json=payload)
        assert response.status_code == 200

    return _mark_token


@given(parsers.parse('"{token}" is marked as a stablecoin'))
def mark_as_stablecoin(token, mark_token):
    mark_token(token, is_stable=True)


@given(parsers.parse('"{token}" is marked as a non-stablecoin'))
def mark_token_as_non_stablecoin(token, mark_token):
    mark_token(token, is_stable=False)


@given("the API is running")
def api_is_running(client):
    response = client.get(HEALTH_ENDPOINT)
    assert response.status_code == 200
    health_json = response.json()
    assert health_json["status"] == "healthy"
    assert health_json["components"]["api"] == "healthy"
    assert health_json["components"]["ui"] == "healthy"
