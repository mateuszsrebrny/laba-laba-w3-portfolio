Feature: Adding transactions

  Scenario: Adding a BTC transaction
    Given the API is running
    When I add a transaction with timestamp "2025-03-25 10:00:00", token "BTC", amount 100.0
    Then the transaction should be visible with timestamp "2025-03-25 10:00:00", token "BTC", amount 100.0

  Scenario: Preventing duplicate transaction
    Given the API is running
    And I add a transaction with timestamp "2025-03-25 11:00:00", token "ETH", amount 100.0
    When I try to add the same transaction again
    Then I should get an error with code 409 saying "Transaction with timestamp '2025-03-25 11:00:00' and token 'ETH' already exists"

  Scenario: Allowing same timestamp with different token
    Given the API is running
    And I add a transaction with timestamp "2025-03-25 12:00:00", token "BTC", amount 50.0
    When I add a transaction with timestamp "2025-03-25 12:00:00", token "ETH", amount 10.0
    Then the transaction should be visible with timestamp "2025-03-25 12:00:00", token "ETH", amount 10.0
