import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("add_transaction.feature")

@pytest.fixture
def base_payload():
    return {
    }

@given("the API is running")
def api_is_running(client):
    response = client.get("/")
    assert response.status_code == 200

@when(parsers.parse(
    'I add a transaction with timestamp "{timestamp:ti}", token "{token}", amount "{amount:f}" and total_usd "{total_usd:f}"'
))
@given(parsers.parse(
    'I add a transaction with timestamp "{timestamp:ti}", token "{token}", amount "{amount:f}" and total_usd "{total_usd:f}"'
))
def add_transaction(timestamp, token, amount, total_usd, client, base_payload):
    payload = {
        **base_payload,
        "timestamp": timestamp,
        "token": token,
        "amount": amount,
        "total_usd": total_usd,
    }

    pytest.last_payload = payload
    response = client.post("/add", data=payload)
    pytest.last_response = response
    assert response.status_code == 200


@then(parsers.parse(
    'the transaction should be visible with timestamp "{timestamp:ti}", token "{token}", amount "{amount:f}" and total_usd "{total_usd:f}"'
))
def transaction_should_be_visible(timestamp, token, amount, total_usd, client):
    response = client.get("/")
    assert str(timestamp) in response.text
    assert token in response.text
    assert str(amount) in response.text
    assert str(total_usd) in response.text

@when("I try to add another transaction with the same timestamp and token")
def try_to_add_same_transaction_again(client):
    last_payload = pytest.last_payload
    payload = {
        **last_payload,
        "amount": last_payload["amount"] + 1,
        "total_usd": last_payload["total_usd"] + 1,
    }
    response = client.post("/add", data=payload)
    pytest.last_response = response

@then(parsers.parse('I should get an error with code {error_code:d} saying "{error_msg}"'))
def check_error_message(error_code, error_msg):
    assert pytest.last_response.status_code == error_code
    json_body = pytest.last_response.json()
    assert "error" in json_body
@when('I add another transaction with the same timestamp but different token')
def add_transaction_with_different_token(client):
    last_payload = pytest.last_payload
    payload = {
        **last_payload,
        "token": "w"  + last_payload["token"],
    }

    pytest.last_payload = payload  # Update last payload for reuse
    response = client.post("/add", data=payload)
    pytest.last_response = response
    assert response.status_code == 200


@then(parsers.parse(
    'the second transaction should be visible'
))
def second_transaction_should_be_visible(client):
    last_payload = pytest.last_payload
    response = client.get("/")
    assert str(last_payload["timestamp"]) in response.text
    assert last_payload["token"] in response.text
    assert str(last_payload["amount"]) in response.text
    assert str(last_payload["total_usd"]) in response.text

