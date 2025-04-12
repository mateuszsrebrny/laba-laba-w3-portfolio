from pytest_bdd import given, scenarios, then, when

scenarios("ui/manage_token.feature")


@given("I am on the 'Tokens' page")
def navigate_to_tokens_page(page):
    page.goto("http://127.0.0.1:11111/tokens")  # Navigate to the Tokens page


@when("I fill in the 'Add Token' form with valid data")
def fill_add_token_form(page):
    page.fill('input[name="token"]', "BTC")  # Fill token name field
    page.click('input[value="false"]')  # Select non-stablecoin option


@when("I submit the form")
def submit_add_token_form(page):
    page.click('button[type="submit"]')  # Click submit button


@then("I should see the token in the list")
def verify_token_in_list(page):
    token_row = page.locator("table tbody tr td:text('BTC')")
    assert token_row.is_visible()  # Verify that BTC appears in the table
