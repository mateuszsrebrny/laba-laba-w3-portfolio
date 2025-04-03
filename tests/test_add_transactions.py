import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("add_transaction.feature")

@given(parsers.parse(
    'I add a transaction with timestamp "{timestamp:ti}", from_token "{from_token}", to_token "{to_token}", from_amount "{from_amount:f}", and to_amount "{to_amount:f}"'
))
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
    response = client.post("/transactions", json=payload) 
    pytest.last_response = response
    assert response.status_code == 200

@given(parsers.parse('"{token}" is marked as a stablecoin'))
def mark_as_stablecoin(token, mark_token):
    mark_token(token, is_stable=True)


@then(parsers.parse('the transaction should be recorded with timestamp "{timestamp:ti}", token "{token}", amount "{amount:f}", stable_coin "{stable_coin}", and total_usd "{total_usd:f}"'))
def verify_transaction_recorded(timestamp, token, amount, stable_coin, total_usd, client, db):
    """Verify that a transaction with the specified details is shown on the list."""
    
    response = client.get("/")
    assert response.status_code == 200
    response_text = response.text
    
    # Check that transaction details appear in the response
    assert str(timestamp) in response_text, f"Timestamp {timestamp} not found in response"
    assert token in response_text, f"Token {token} not found in response"
    assert str(amount) in response_text, f"Amount {amount} not found in response"
    assert str(total_usd) in response_text, f"Total USD {total_usd} not found in response"


@given(parsers.parse('"{token}" is marked as a non-stablecoin'))
def mark_token_as_non_stablecoin(token, mark_token):
    mark_token(token, is_stable=False)

@given(parsers.parse('"{token}" is not marked in any way'))
def token_is_not_marked(token):
    # No action needed since the database starts empty for each test
    pass


@when("I try to add another transaction with the same timestamp and token")
def try_to_add_same_transaction_again(client):
    last_payload = pytest.last_payload
    payload = {
        **last_payload,
        "amount": last_payload["amount"] + 1,
        "total_usd": last_payload["total_usd"] + 1,
    }
    response = client.post("/transactions", data=payload)
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

    # Send the POST request to the /transactions endpoint
    response = client.post("/transactions", json=payload)

    # Store the response for later verification
    pytest.last_response = response


@then(parsers.parse('I should get an error with code {error_code:d} saying "{error_msg}"'))
def check_error_message(error_code, error_msg):
    assert pytest.last_response.status_code == error_code
    json_body = pytest.last_response.json()
    assert "error" in json_body


@when(parsers.parse(
    'I try to add another transaction with the same timestamp and from_token "{from_token}" and to_token "{to_token}", from_amount "{from_amount:f}", and to_amount "{to_amount:f}"'
))
def try_add_transaction_same_timestamp(from_token, to_token, from_amount, to_amount, client):
    # Re-use the last timestamp from previous step
    last_payload = pytest.last_payload
    payload = {
        "timestamp": last_payload["timestamp"],
        "from_token": from_token,
        "to_token": to_token,
        "from_amount": from_amount,
        "to_amount": to_amount,
    }
    
    # Store for later verification
    pytest.last_payload = payload
    
    # This should fail with 409 Conflict
    response = client.post("/transactions", json=payload)
    pytest.last_response = response
    # Don't assert here - the calling test will verify the status code


@when(parsers.parse(
    'I add another transaction with the same timestamp but from_token "{from_token}" and to_token "{to_token}", from_amount "{from_amount:f}", and to_amount "{to_amount:f}"'
))
def add_transaction_different_token_same_timestamp(from_token, to_token, from_amount, to_amount, client):
    # Re-use the last timestamp
    last_payload = pytest.last_payload
    payload = {
        "timestamp": last_payload["timestamp"],
        "from_token": from_token,
        "to_token": to_token,
        "from_amount": from_amount,
        "to_amount": to_amount,
    }
    
    # This should succeed
    response = client.post("/transactions", json=payload)
    pytest.last_response = response
    assert response.status_code == 200  # This should work since it's a different token


@then("the second transactions should be recorded successfully in the system")
def second_transaction_should_be_recorded(client):
    last_payload = pytest.last_payload
    response = client.get("/")
    assert str(last_payload["timestamp"]) in response.text
    assert last_payload["from_token"] in response.text
    assert str(last_payload["from_amount"]) in response.text
    assert str(last_payload["to_amount"]) in response.text

