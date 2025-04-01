from pytest_bdd import given, when, then, parsers, scenarios
import pytest

scenarios("token_management.feature")

# Reusable fixture for marking tokens
@pytest.fixture
def mark_token(client):
    def _mark_token(token, is_stable):
        payload = {"token": token, "is_stable": is_stable}
        response = client.post("/tokens", json=payload)
        return response
    return _mark_token


# Scenario: Marking a token as a stablecoin
@when(parsers.parse('I mark the token "{token}" as a stablecoin'))
def mark_as_stablecoin(token, mark_token):
    response = mark_token(token, True)
    pytest.last_response = response


@then(parsers.parse('the system should record that "{token}" is now recognized as a stablecoin'))
def verify_token_is_stablecoin(token, client):
    response = client.get(f"/tokens/{token}")
    assert response.status_code == 200
    token_data = response.json()
    assert token_data["name"] == token
    assert token_data["is_stable"] is True


# Scenario: Marking a token as a non-stablecoin
@when(parsers.parse('I mark the token "{token}" as a non-stablecoin'))
def mark_as_non_stablecoin(token, mark_token):
    response = mark_token(token, False)
    pytest.last_response = response


@then(parsers.parse('the system should record that "{token}" is now recognized as a non-stablecoin'))
def verify_token_is_non_stablecoin(token, client):
    response = client.get(f"/tokens/{token}")
    assert response.status_code == 200
    token_data = response.json()
    assert token_data["name"] == token
    assert token_data["is_stable"] is False


# Scenario: Preventing duplicate token entries
@given(parsers.parse('"{token}" is marked as a stablecoin'))
def given_token_is_already_stablecoin(token, mark_token):
    response = mark_token(token, True)
    assert response.status_code == 200


@when(parsers.parse('I try to mark "{token}" as a non-stablecoin'))
def try_to_mark_as_non_stablecoin(token, mark_token):
    response = mark_token(token, False)
    pytest.last_response = response


@then(parsers.parse('I should get an error with code {error_code:d} saying "{error_msg}"'))
def verify_error_message(error_code, error_msg):
    assert pytest.last_response.status_code == error_code
    json_body = pytest.last_response.json()
    assert "error" in json_body
    assert json_body["error"] == error_msg

