Feature: Adding transactions

  Scenario: Adding a buy transaction
    Given the API is running
    When I add a transaction with timestamp "2025-03-28 12:00:00", token "BTC", amount "0.5" and total_usd "-15000.0"
    Then the transaction should be visible with timestamp "2025-03-28 12:00:00", token "BTC", amount "0.5" and total_usd "-15000.0"

  Scenario: Adding a sell transaction
    Given the API is running
    When I add a transaction with timestamp "2025-03-28 12:05:00", token "ETH", amount "1.5" and total_usd "3000.0"
    Then the transaction should be visible with timestamp "2025-03-28 12:05:00", token "ETH", amount "1.5" and total_usd "3000.0"

  Scenario: Preventing duplicate transaction
    Given the API is running
    And I add a transaction with timestamp "2025-03-28 12:00:00", token "BTC", amount "0.5" and total_usd "-15000.0"
    When I try to add another transaction with the same timestamp and token
    Then I should get an error with code 409 saying "Transaction with timestamp '2025-03-28 12:00:00' and token 'BTC' already exists"

  Scenario: Allowing same timestamp with different token
    Given the API is running
    And I add a transaction with timestamp "2025-03-28 12:00:00", token "BTC", amount "0.5" and total_usd "-15000.0"
    When I add another transaction with the same timestamp but different token    
    Then the second transaction should be visible 
