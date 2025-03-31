import os

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# make sure nothing connects to postgres
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models import Base
from app.main import app
from fastapi.testclient import TestClient

# Create a test database engine
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

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

