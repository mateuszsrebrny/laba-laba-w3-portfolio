import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("add_transaction.feature")

@given("the API is running")
def api_is_running(client):
    response = client.get("/")
    assert response.status_code == 200

@when('I add a transaction with amount 100 and token "BTC"')
def add_transaction(client, db):
    payload = {"amount": 100, "token": "BTC"}
    response = client.post("/add", data=payload)
    assert response.status_code == 200

@then("the transaction should be saved in the database")
def check_transaction_saved(client, db):
    response = client.get("/")
    assert "100" in response.text and "BTC" in response.text
