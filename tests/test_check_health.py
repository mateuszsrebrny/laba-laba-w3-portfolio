from pytest_bdd import given, scenarios, then

# Load the feature file
scenarios("check_health.feature")


@given("I navigate to the health check endpoint")
def navigate_to_health_check(page):
    page.goto("http://127.0.0.1:11111/health")  # Navigate to the health check endpoint


@then('I should see the status "healthy"')
def verify_health_status(page):
    response = page.locator("body").inner_text()
    assert (
        response == '{"status":"healthy","components":{"api":"healthy","ui":"healthy"}}'
    )
