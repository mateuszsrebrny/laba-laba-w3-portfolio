import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("add_transaction.feature")

@pytest.fixture
def base_payload():
    return {
        "type": "buy",
        "exchange_platform": "TestPlatform"
    }

@given("the API is running")
def api_is_running(client):
    response = client.get("/")
    assert response.status_code == 200

@when(parsers.parse(
    'I add a transaction with timestamp "{timestamp:ti}", token "{token}", amount {amount:F}'
))
def add_transaction(timestamp, token, amount, client, base_payload):
    payload = {
        **base_payload,
        "timestamp": timestamp,
        "token": token,
        "amount": amount,
    }

    pytest.last_payload = payload
    response = client.post("/add", data=payload)
    pytest.last_response = response
    assert response.status_code == 200


@then(parsers.parse(
    'the transaction should be visible with timestamp "{timestamp:ti}", token "{token}", amount {amount:F}'
))
def transaction_should_be_visible(timestamp, token, amount, client):
    response = client.get("/")
    #assert timestamp in response.text
    assert token in response.text
    assert str(amount) in response.text
