from playwright.sync_api import expect
from pytest_bdd import given, scenarios, then, when

# Load the feature file
scenarios("ui/add_transaction.feature")


@given("I am on the 'Add Transaction' page")
def navigate_to_add_transaction_page(page):
    page.goto("http://127.0.0.1:11111/ui/add")  # Navigate to the Add Transaction page


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


@when("I click on the 'Add Transaction' button")
def submit_form(page):
    page.get_by_role("button", name="Add Transaction").click()


@then("I should see a success message mentioning BTC and DAI")
def verify_success_message(page):
    success_message = page.locator(
        "#message .alert-success"
    ).inner_text()  # Locate success message
    assert "Transaction added: timestamp" in success_message
    assert "token 'BTC'" in success_message
    assert "stable_coin 'DAI'" in success_message


@then("the transaction form should be reloaded")
def verify_transaction_form_reloaded(page):
    # Wait for the form element to be available
    # page.wait_for_selector("form[hx-post='/ui/transactions']", timeout=1000)
    form = page.locator("form[hx-post='/ui/transactions']")
    expect(form).to_be_visible(timeout=1000)

    from_token_input = form.locator('input[name="from_token"]')
    expect(from_token_input).to_be_visible(timeout=1000)

    # Check that key input fields are in their default state (e.g., empty)
    from_token_value = page.locator('input[name="from_token"]').input_value()
    to_token_value = page.locator('input[name="to_token"]').input_value()
    from_amount_value = page.locator('input[name="from_amount"]').input_value()
    to_amount_value = page.locator('input[name="to_amount"]').input_value()

    # You might also check other fields if applicable—for example, that they are empty.
    assert (
        from_token_value == ""
    ), f"Expected empty from_token, got '{from_token_value}'"
    assert to_token_value == "", f"Expected empty to_token, got '{to_token_value}'"
    assert (
        from_amount_value == ""
    ), f"Expected empty from_amount, got '{from_amount_value}'"
    assert to_amount_value == "", f"Expected empty to_amount, got '{to_amount_value}'"

    # Optionally, check that the submit button exists
    expect(page.locator("button", has_text="Add Transaction")).to_be_visible()
