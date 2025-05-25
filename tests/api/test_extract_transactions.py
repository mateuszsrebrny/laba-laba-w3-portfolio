import os

import pytest
from pytest_bdd import parsers, scenarios, then, when

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

    print(response)
    print(response.json())
    pytest.last_response = response
    assert response.status_code == 200


@then(
    parsers.parse(
        'the response should include a transaction with timestamp "{timestamp}", token "{token}", amount "{amount:f}", stable_coin "{stable_coin}", and total_usd "{total_usd:f}"'
    )
)
def check_transaction_detail_fields(timestamp, token, amount, stable_coin, total_usd):
    details = pytest.last_response.json().get("details", [])
    assert any(
        tx["timestamp"] == timestamp
        and tx["token"] == token
        and tx["amount"] == amount
        and tx["stable_coin"] == stable_coin
        and tx["total_usd"] == total_usd
        for tx in details
    ), "Expected transaction not found in response"


@when("I upload an invalid image file")
def upload_invalid_file(client):
    """Upload an invalid file to the extract endpoint."""
    invalid_content = b"This is not an image file"
    files = {"image": ("invalid.txt", invalid_content, "text/plain")}
    response = client.post(EXTRACT_ENDPOINT, files=files)

    pytest.last_response = response
