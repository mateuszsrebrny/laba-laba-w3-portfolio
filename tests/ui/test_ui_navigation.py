from pytest_bdd import given, scenarios, then, when

# Load the feature file
scenarios("ui/navigation.feature")


@given("I am on the main page")
def navigate_to_main_page(page):
    page.goto("http://127.0.0.1:11111/")  # Navigate to main page


@when("I click on the 'Manage Tokens' button")
def click_manage_tokens_button(page):
    page.click("text=Manage Tokens")  # Click Manage Tokens button


@then("I should be redirected to the 'Tokens' page")
def verify_redirect_to_tokens_page(page):
    assert page.url == "http://127.0.0.1:11111/tokens"  # Verify URL


@when("I click on the 'Add Transaction' button")
def click_add_transaction_button(page):
    page.click("text=Add Transaction")  # Click Add Transaction button


@then("I should be redirected to the 'Add Transaction' page")
def verify_redirect_to_add_transaction_page(page):
    assert page.url == "http://127.0.0.1:11111/add"  # Verify URL


@when("I click on the 'Back to Transactions' button")
def click_back_to_main_page_button(page):
    page.click("text=Back to Transactions")  # Click Back button


@then("I should be redirected to the main page")
def verify_redirect_to_main_page(page):
    assert page.url == "http://127.0.0.1:11111/"
