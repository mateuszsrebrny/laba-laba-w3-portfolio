Feature: Adding transactions

  Scenario: Successfully adding a transaction
    Given the API is running
    When I add a transaction with amount 100 and token "BTC"
    Then the transaction should be saved in the database
