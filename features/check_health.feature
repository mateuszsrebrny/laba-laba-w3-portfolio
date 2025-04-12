Feature: API Health Check

  Scenario: Verify the API is running
    Given I navigate to the health check endpoint
    Then I should see the status "healthy"

