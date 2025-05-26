import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from app import ocr

# Load the scenarios
scenarios("features/extract_transactions.feature")

# Constants
EXTRACT_ENDPOINT = "/api/transactions/extract"
SAMPLE_IMAGE_PATH = "tests/fixtures/debank_screenshot.jpg"
FAKE_IMAGE_PATH = "tests/fixtures/fake_image.jpg"


def _upload_image(client, filename: str):
    """Upload a test Debank screenshot to the extract endpoint."""
    with open(filename, "rb") as f:
        files = {"image": (os.path.basename(filename), f, "image/jpeg")}
        response = client.post(EXTRACT_ENDPOINT, files=files)

    print(response)
    print(response.json())
    pytest.last_response = response
    assert response.status_code == 200


@when("I upload a real Debank screenshot")
def upload_real_debank_screenshot(client):
    _upload_image(client, SAMPLE_IMAGE_PATH)


@when("I upload a fake Debank screenshot")
def upload_fake_debank_screenshot(client):
    _upload_image(client, FAKE_IMAGE_PATH)


@then(
    parsers.parse(
        'the response should include a transaction with timestamp "{timestamp}", token "{token}", amount "{amount:f}", stable_coin "{stable_coin}", and total_usd "{total_usd:f}"'
    )
)
def check_transaction_detail_fields(timestamp, token, amount, stable_coin, total_usd):
    details = pytest.last_response.json().get("details", [])

    # Check if each field has at least one match
    assert any(
        tx["timestamp"] == timestamp for tx in details
    ), f"No match found for timestamp={timestamp}"
    assert any(
        tx["token"] == token for tx in details
    ), f"No match found for token={token}"
    assert any(
        tx["amount"] == amount for tx in details
    ), f"No match found for amount={amount}"
    assert any(
        tx["stable_coin"] == stable_coin for tx in details
    ), f"No match found for stable_coin={stable_coin}"
    assert any(
        tx["total_usd"] == total_usd for tx in details
    ), f"No match found for total_usd={total_usd}"

    # If all individual matches passed, check for full match
    assert any(
        tx["timestamp"] == timestamp
        and tx["token"] == token
        and tx["amount"] == amount
        and tx["stable_coin"] == stable_coin
        and tx["total_usd"] == total_usd
        for tx in details
    ), "Expected transaction not found with all matching fields"


@then("the response should include 1 failed section with error")
def check_failed_section():
    data = pytest.last_response.json()
    failed = data.get("failed", [])
    assert len(failed) == 1
    assert "section" in failed[0]
    assert "error" in failed[0]


@when("I upload an invalid image file")
def upload_invalid_file(client):
    """Upload an invalid file to the extract endpoint."""
    invalid_content = b"This is not an image file"
    files = {"image": ("invalid.txt", invalid_content, "text/plain")}
    response = client.post(EXTRACT_ENDPOINT, files=files)

    pytest.last_response = response


@given("OCR is mocked to return multiple transactions")
def mock_ocr(monkeypatch):
    def fake_get_extracted_text(_: bytes) -> str:
        return """
Contract Interaction
linch
-900 DAI
($899.91)
+3.9982 AAVE
($1,112.67)
2025/02/04 04.37.39
Contract Interaction
quickswap
100 DAI
(s99.99)
+0.4612 AAVE
($128.36)
2025/02/05 04.02.29
Contract Interaction
1inch
-100 DAI
(s99.99)
+0.4612 AAVE
($128.36)
2025/02/04 04.02.29
        """

    monkeypatch.setattr(ocr, "get_extracted_text", fake_get_extracted_text)
