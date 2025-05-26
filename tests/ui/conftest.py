from multiprocessing import Process

import pytest
import requests
from uvicorn import run

from app.database import get_db
from app.main import app

# The "db" fixture from the common conftest.py is available here


# Fixture to start a live HTTP server with overridden dependencies
@pytest.fixture(scope="session")
def http_server(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Start the server on a dedicated port (e.g., 11111)
    process = Process(
        target=run, kwargs={"app": app, "host": "127.0.0.1", "port": 11111}
    )
    process.start()
    yield  # Tests will run while the server is up
    process.terminate()
    app.dependency_overrides.clear()


# Playwright page fixture for UI tests; depends on the http_server fixture
@pytest.fixture(scope="function")
def page(playwright, http_server):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    browser.close()


# mark_token version using http
@pytest.fixture
def post_token():
    def _post_token(token, is_stable):
        return requests.post(
            "http://localhost:11111/api/tokens",
            json={"token": token, "is_stable": is_stable},
        )

    return _post_token
