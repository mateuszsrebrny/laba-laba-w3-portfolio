import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("add_transaction.feature")

@given("the API is running")
def api_is_running(client):
    response = client.get("/")
    assert response.status_code == 200

@when(parsers.parse(
    'I add a transaction with timestamp "{timestamp:ti}", from_token "{from_token}", to_token "{to_token}", from_amount "{from_amount:f}", and to_amount "{to_amount:f}"'
))
def add_transaction(timestamp, from_token, to_token, from_amount, to_amount, client):
    payload = {
        "timestamp": str(timestamp),
        "from_token": from_token,
        "to_token": to_token,
        "from_amount": from_amount,
        "to_amount": to_amount,
    }
    pytest.last_payload = payload
    response = client.post("/add", json=payload) 
    pytest.last_response = response
    assert response.status_code == 200

@given(parsers.parse('"{token}" is marked as a stablecoin'))
def mark_as_stablecoin(token, mark_token):
    mark_token("DAI", is_stable=True)

@then(parsers.parse(
    'the transaction should be visible with timestamp "{timestamp:ti}", token "{token}", amount "{amount:f}" and total_usd "{total_usd:f}"'
))
def transaction_should_be_visible(timestamp, token, amount, total_usd, client):
    response = client.get("/")
    assert str(timestamp) in response.text
    assert token in response.text
    assert str(amount) in response.text
    assert str(total_usd) in response.text

@given(parsers.parse('neither "{token1}" nor "{token2}" is marked as a stablecoin'))
def neither_tokens_are_stablecoins(token1, token2, mark_token):
    # Use the mark_token fixture to mark both tokens as non-stablecoins
    mark_token(token1, is_stable=False)
    mark_token(token2, is_stable=False)

@given(parsers.parse('both "{token1}" and "{token2}" are marked as stablecoins'))
def both_tokens_are_stablecoins(token1, token2, mark_token):
    # Use the mark_token fixture to mark both tokens as stablecoins
    mark_token(token1, is_stable=True)
    mark_token(token2, is_stable=True)


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


@when(parsers.parse(
    'I try to add a transaction with timestamp "{timestamp:ti}", from_token "{from_token}", to_token "{to_token}", from_amount "{from_amount:f}", and to_amount "{to_amount:f}"'
))
def try_add_transaction(timestamp, from_token, to_token, from_amount, to_amount, client):
    # Prepare the payload for the transaction
    payload = {
        "timestamp": str(timestamp),
        "from_token": from_token,
        "to_token": to_token,
        "from_amount": from_amount,
        "to_amount": to_amount,
    }

    # Store the payload for later verification
    pytest.last_payload = payload

    # Send the POST request to the /add endpoint
    response = client.post("/add", json=payload)

    # Store the response for later verification
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

