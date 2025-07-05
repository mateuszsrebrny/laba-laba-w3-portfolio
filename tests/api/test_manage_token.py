import pytest
from pytest_bdd import parsers, scenarios, then, when

from tests.config import TOKENS_ENDPOINT

scenarios("features/manage_token.feature")


@then(
    parsers.parse(
        'the system should record that "{token}" is now recognized as a stablecoin'
    )
)
def verify_token_is_stablecoin(token, client):
    response = client.get(f"{TOKENS_ENDPOINT}/{token}")
    assert response.status_code == 200
    token_data = response.json()
    assert token_data["name"] == token
    assert token_data["is_stable"] is True


# Scenario: Marking a token as a non-stablecoin
@when(parsers.parse('I mark the token "{token}" as a non-stablecoin'))
def mark_as_non_stablecoin(token, mark_token):
    pytest.last_response = mark_token(token, False)


@then(
    parsers.parse(
        'the system should record that "{token}" is now recognized as a non-stablecoin'
    )
)
def verify_token_is_non_stablecoin(token, client):
    response = client.get(f"{TOKENS_ENDPOINT}/{token}")
    assert response.status_code == 200
    token_data = response.json()
    assert token_data["name"] == token
    assert token_data["is_stable"] is False


@when(parsers.parse('I try to mark "{token}" as a non-stablecoin'))
def try_to_mark_as_non_stablecoin(token, mark_token):
    response = mark_token(token, False, expected_statuses=(409,))
    pytest.last_response = response


@then(
    parsers.parse('I should get an error with code {error_code:d} saying "{error_msg}"')
)
def verify_error_message(error_code, error_msg):
    assert pytest.last_response.status_code == error_code
    json_body = pytest.last_response.json()
    assert "error" in json_body
    assert json_body["error"] == error_msg


@when(parsers.parse('I mark the token "{token}" as a stablecoin'))
def mark_token_first_time(token, mark_token):
    pytest.response = mark_token(token, is_stable=True, expected_statuses=(201,))


@when(parsers.parse('I mark the token "{token}" as a stablecoin again'))
def mark_token_second_time(token, mark_token):
    pytest.response = mark_token(token, is_stable=True, expected_statuses=(200,))


@then(parsers.parse("the response status code should be {code:d}"))
def assert_status_code(code):
    assert pytest.response.status_code == code
