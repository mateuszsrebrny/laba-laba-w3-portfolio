import pytest
import requests
from pytest_bdd import scenarios, given, when, then

API_URL = "http://localhost:8000"  

scenarios("add_transaction.feature")

@given("the API is running")
def api_is_running():
    response = requests.get(f"{API_URL}/")
    assert response.status_code == 200

@when('I add a transaction with amount 100 and token "BTC"')
def add_transaction():
    payload = {"amount": 100, "token": "BTC"}
    response = requests.post(f"{API_URL}/add", data=payload)
    assert response.status_code == 200

@then("the transaction should be saved in the database")
def check_transaction_saved():
    response = requests.get(f"{API_URL}/")
    assert "100" in response.text and "BTC" in response.text
