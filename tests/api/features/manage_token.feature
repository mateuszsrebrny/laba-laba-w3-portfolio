@fast
Feature: Managing tokens

  Scenario: Marking "GHO" as a stablecoin
    Given the API is running
    When I mark the token "GHO" as a stablecoin
    Then the system should record that "GHO" is now recognized as a stablecoin

  Scenario: Marking "BTC" as non-stablecoin
    Given the API is running
    When I mark the token "BTC" as a non-stablecoin
    Then the system should record that "BTC" is now recognized as a non-stablecoin

  Scenario: Trying to mark "GHO" as both stablecoin and non-stablecoin
    Given the API is running
    And "GHO" is marked as a stablecoin
    When I try to mark "GHO" as a non-stablecoin
    Then I should get an error with code 409 saying "'GHO' is already marked as a stablecoin."

  Scenario: Marking a token twice gives 201 then 200
    Given the API is running
    When I mark the token "USDT" as a stablecoin
    Then the response status code should be 201
    When I mark the token "USDT" as a stablecoin again
    Then the response status code should be 200
