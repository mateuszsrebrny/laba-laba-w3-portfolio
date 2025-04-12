from pytest_bdd import given, scenarios, then, when

# Load the feature file
scenarios("ui/add_transaction.feature")


@given("I am on the 'Add Transaction' page")
def navigate_to_add_transaction_page(page):
    page.goto("http://127.0.0.1:11111/add")  # Navigate to the Add Transaction page


@when("I fill in the transaction form with valid data")
def fill_transaction_form(page):
    page.fill('input[name="from_token"]', "BTC")  # Fill from_token field
    page.fill('input[name="to_token"]', "DAI")  # Fill to_token field
    page.fill('input[name="from_amount"]', "0.5")  # Fill from_amount field
    page.fill('input[name="to_amount"]', "1000")  # Fill to_amount field

    # Click on the timestamp input to open Flatpickr's date picker
    page.click('input[name="timestamp"]')

    # Select a date using Flatpickr's UI (if applicable)
    page.click(
        '.flatpickr-day[aria-label="April 12, 2025"]'
    )  # Adjust selector based on your Flatpickr configuration
    # page.fill('input[name="timestamp"]', '2025-04-12T12:00:00')  # Fill timestamp field


@when("I submit the form")
def submit_form(page):
    page.click('button[type="submit"]')  # Click the submit button


@then("I should see a success message mentioning BTC and DAI")
def verify_success_message(page):
    success_message = page.locator(
        "#message .alert-success"
    ).inner_text()  # Locate success message
    assert "Transaction with timestamp" in success_message
    assert "token 'BTC'" in success_message
    assert "stable_coin 'DAI'" in success_message
