@slow
Feature: UI: add a transaction

  Scenario: Successfully adding a transaction
    Given I am on the 'Add Transaction' page
    And "BTC" is marked as a non-stablecoin
    And "DAI" is marked as a stablecoin
    When I fill in the transaction form with valid data
    And I click on the 'Add Transaction' button 
    Then I should see a success message mentioning BTC and DAI
    And the transaction form should be reloaded
