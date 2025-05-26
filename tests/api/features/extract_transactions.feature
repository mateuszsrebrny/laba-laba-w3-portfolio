Feature: Extract transactions from Debank screenshots

  @slow
  Scenario: Extracting transaction data from a Debank screenshot
    Given the API is running
    And "DAI" is marked as a stablecoin
    And "AAVE" is marked as a non-stablecoin
    When I upload a real Debank screenshot
    Then the response should include a transaction with timestamp "2025-02-03T04:02:29", token "AAVE", amount "0.4612", stable_coin "DAI", and total_usd "-100.0"

  @slow
  Scenario: Handling an invalid image upload
    Given the API is running
    When I upload an invalid image file
    Then I should get an error with code 400 saying "Invalid image file"
  
  @fast
  Scenario: Parsing multiple transactions including a failed one from mocked OCR
    Given OCR is mocked to return multiple transactions
    And "DAI" is marked as a stablecoin
    And "AAVE" is marked as a non-stablecoin
    And "USDC" is marked as a stablecoin
    And "WBTC" is marked as a non-stablecoin
    When I upload a fake Debank screenshot
    Then the response should include a transaction with timestamp "2025-02-04T04:02:29", token "AAVE", amount "0.4612", stable_coin "DAI", and total_usd "-100.0"
    And the response should include a transaction with timestamp "2025-02-04T04:37:39", token "AAVE", amount "3.9982", stable_coin "DAI", and total_usd "-900.0"
    And the response should include 1 failed section with error
