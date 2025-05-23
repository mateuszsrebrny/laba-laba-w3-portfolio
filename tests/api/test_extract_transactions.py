import os

import pytest
from pytest_bdd import scenarios, then, when

# Load the scenarios
scenarios("features/extract_transactions.feature")

# Constants
EXTRACT_ENDPOINT = "/api/transactions/extract"
SAMPLE_IMAGE_PATH = (
    "tests/fixtures/debank_screenshot.jpg"  # You'll need to create this test image
)


@when("I upload a Debank screenshot containing transactions")
def upload_debank_screenshot(client):
    """Upload a test Debank screenshot to the extract endpoint."""
    with open(SAMPLE_IMAGE_PATH, "rb") as f:
        files = {"image": (os.path.basename(SAMPLE_IMAGE_PATH), f, "image/jpg")}
        response = client.post(EXTRACT_ENDPOINT, files=files)

    pytest.last_response = response
    # assert response.status_code == 200


@then("the transactions should be extracted and stored in the database")
def verify_transactions_stored(client, db):
    """Verify that transactions were extracted and stored in the database."""
    response_data = pytest.last_response.json()

    # Verify the response indicates success
    assert response_data.get("status") == "success"
    assert "Added" in response_data.get("message", "")

    # Verify transactions were added to the database
    # This depends on your specific database verification approach


@then("I should see the extracted transactions in the response")
def verify_transactions_in_response():
    """Verify that transaction details are included in the response."""
    response_data = pytest.last_response.json()

    # Verify details are present
    assert "details" in response_data
    assert len(response_data["details"]) > 0


@when("I upload an invalid image file")
def upload_invalid_file(client):
    """Upload an invalid file to the extract endpoint."""
    invalid_content = b"This is not an image file"
    files = {"image": ("invalid.txt", invalid_content, "text/plain")}
    response = client.post(EXTRACT_ENDPOINT, files=files)

    pytest.last_response = response
