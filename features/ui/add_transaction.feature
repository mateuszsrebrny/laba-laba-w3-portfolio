Feature: UI: add a transaction

  Scenario: Successfully adding a transaction
    Given I am on the 'Add Transaction' page
    When I fill in the transaction form with valid data
    And I submit the form
    Then I should see a success message mentioning BTC and DAI
