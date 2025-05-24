import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, then

from app.database import get_db
from app.main import app
from tests.config import HEALTH_ENDPOINT

# The "db" fixture is automatically available here from the common conftest.py


# Provide a TestClient fixture that overrides the database dependency
@pytest.fixture(scope="session")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# BDD step to check that the API is running
@given("the API is running")
def api_is_running(client):
    response = client.get(HEALTH_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    health_json = response.json()
    assert health_json["status"] == "healthy"
    assert health_json["components"]["api"] == "healthy"
    assert health_json["components"]["ui"] == "healthy"


@pytest.fixture
def mark_token(client):
    def _mark_token(token, is_stable):
        payload = {"token": token, "is_stable": is_stable}
        response = client.post("/api/tokens", json=payload)
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    return _mark_token


@then(
    parsers.parse('I should get an error with code {error_code:d} saying "{error_msg}"')
)
def check_error_message(error_code, error_msg):
    assert pytest.last_response.status_code == error_code
    json_body = pytest.last_response.json()
    assert "error" in json_body
