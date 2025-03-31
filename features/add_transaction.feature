Feature: Adding transactions

  Scenario: Adding a sell BTC to DAI transaction
    Given the API is running
    And "DAI" is marked as a stablecoin
    When I add a transaction with timestamp "2025-03-30 10:00:00", from_token "BTC", to_token "DAI", from_amount "0.5", and to_amount "15000.0"
    Then the transaction should be recorded with timestamp "2025-03-30 10:00:00", token "BTC", amount "-0.5", stable_coin "DAI", and total_usd "-15000.0"

  Scenario: Adding a buy BTC with DAI transaction
    Given the API is running
    And "DAI" is marked as a stablecoin
    When I add a transaction with timestamp "2025-03-30 11:00:00", from_token "DAI", to_token "BTC", from_amount "15000.0", and to_amount "0.5"
    Then the transaction should be recorded with timestamp "2025-03-30 11:00:00", token "BTC", amount "0.5", stable_coin "DAI", and total_usd "15000.0"

  Scenario: Adding a transaction between BTC and ETH (neither is a stablecoin)
    Given the API is running
    And neither "BTC" nor "ETH" is marked as a stablecoin
    When I try to add a transaction with timestamp "2025-03-30 12:00:00", from_token "BTC", to_token "ETH", from_amount "1.0", and to_amount "15.0"
    Then I should get an error with code 400 saying "One of the tokens must be a stablecoin"

  Scenario: Adding a transaction between DAI and USDC (both are stablecoins)
    Given the API is running
    And both "DAI" and "USDC" are marked as stablecoins
    When I try to add a transaction with timestamp "2025-03-30 12:05:00", from_token "DAI", to_token "USDC", from_amount "1000.0", and to_amount "1000.0"
    Then I should get an error with code 400 saying "Both tokens cannot be stablecoins"

  Scenario: Adding a transaction between an unknown token and DAI
    Given the API is running
    And only "DAI" is marked as a stablecoin
    When I try to add a transaction with timestamp "2025-03-30 12:10:00", from_token "UNKNOWN", to_token "DAI", from_amount "1.0", and to_amount "1000.0"
    Then I should get an error with code 400 saying "'UNKNOWN' is not recognized. Please add it first."

  Scenario: Preventing duplicate transactions for the same token at the same timestamp
    Given the API is running
    And I add a transaction with timestamp "2025-03-30 13:00:00", token "BTC", amount "-0.5", stable_coin "DAI", and total_usd "-15000.0"
    When I try to add another transaction with the same timestamp and token ("BTC")
    Then I should get an error with code 409 saying "'BTC' already has a transaction at '2025-03-30 13:00:00'"

  Scenario: Allowing transactions with the same timestamp but different tokens
    Given the API is running
    And I add a transaction with timestamp "2025-03-30 14:00:00", token "BTC", amount "-1.0", stable_coin "DAI", and total_usd "-30000.0"
    When I add another transaction with the same timestamp but different token ("ETH"), amount "-2.0", stable_coin "DAI", and total_usd "-6000.0"
    Then both transactions should be recorded successfully in the system

