Feature: Managing tokens

  Scenario: Marking "DAI" as a stablecoin
    Given the API is running
    When I mark the token "DAI" as a stablecoin
    Then the system should record that "DAI" is now recognized as a stablecoin

  Scenario: Marking "BTC" as non-stablecoin
    Given the API is running
    When I mark the token "BTC" as a non-stablecoin
    Then the system should record that "BTC" is now recognized as a non-stablecoin

  Scenario: Trying to mark "DAI" as both stablecoin and non-stablecoin
    Given the API is running
    And "DAI" is marked as a stablecoin
    When I try to mark "DAI" as a non-stablecoin
    Then I should get an error with code 409 saying "'DAI' is already marked as a stablecoin."

  
