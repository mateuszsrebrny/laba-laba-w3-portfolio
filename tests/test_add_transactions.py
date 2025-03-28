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
@given(parsers.parse(
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
    assert str(timestamp) in response.text
    assert token in response.text
    assert str(amount) in response.text

@when("I try to add the same transaction again")
def try_to_add_same_transaction_again(client):
    response = client.post("/add", data=pytest.last_payload)
    pytest.last_response = response

@then(parsers.parse('I should get an error with code {error_code:d} saying "{error_msg}"'))
def check_error_message(error_code, error_msg):
    assert pytest.last_response.status_code == error_code
    json_body = pytest.last_response.json()
    assert "error" in json_body
    assert error_msg in json_body["error"]
