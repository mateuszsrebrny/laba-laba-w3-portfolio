from pytest_bdd import given, scenarios, then, when

scenarios("ui/manage_token.feature")


@given("I am on the 'Tokens' page")
def navigate_to_tokens_page(page):
    page.goto("http://127.0.0.1:11111/ui/tokens")  # Navigate to the Tokens page


@when("I fill in the 'Add Token' form with valid data")
def fill_add_token_form(page):
    page.fill('input[name="token"]', "AAVE")  # Fill token name field
    page.click('input[value="false"]')  # Select non-stablecoin option


@when("I click on the 'Add Token' button")
def submit_form(page):
    page.click("text=Add Token")  # Click form submit button


@then("I should see a success message \"Token 'AAVE' marked as non-stablecoin\"")
def verify_success_message(page):
    success_message = page.locator(
        "#message .alert-success"
    ).inner_text()  # Locate success message
    assert "'AAVE' marked as non-stablecoin" in success_message


@then("I should see the token in the list")
def verify_token_in_list(page):
    token_row = page.locator("table tbody tr td:text('AAVE')")
    assert token_row.is_visible()  # Verify that BTC appears in the table


@then("the 'Add Token' form should remain visible")
def check_token_form_visible(page):
    # Check that the form with id "token-form" is still visible on the page.
    assert page.is_visible("form#token-form"), "Token form is not visible!"


@then("the 'Token' field should be empty")
def check_token_field_empty(page):
    # Verify that the token input field has an empty value.
    token_value = page.input_value("input[name='token']")
    assert token_value == "", f"Token field is not empty: '{token_value}'"
