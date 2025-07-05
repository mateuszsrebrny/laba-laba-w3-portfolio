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

  @fast
  Scenario Outline: Parsing valid transactions from mocked OCR
    Given OCR is mocked to return "<ocr_text>"
    When I upload a fake Debank screenshot
    Then the response should include a transaction with timestamp "<timestamp>", token "<token>", amount "<amount>", stable_coin "<stable_coin>", and total_usd "<total_usd>"
  
    Examples:
      | ocr_text                                  | timestamp             | token | amount  | stable_coin | total_usd |
      | Contract Interaction\nlinch\n-900 DAI\n($899.91)\n+3.9982 AAVE\n($1,112.67)\n2025/02/06 05.47.49 | 2025-02-06T05:47:49   | AAVE  | 3.9982     | DAI        | -900.0    |
      | Contract Interaction\nquickswap\n800 DAI\n(s799.91)\n+3.1982 AAVE\n($1,142.67)\n2025/02/07 06.57.59 | 2025-02-07T06:57:59 | AAVE | 3.1982     | DAI        | -800.0    |
      | Contract Interaction\nquickswap\n2.005 AAVE\n(s499.91)\n+500.01 DAI\n($1,312.67)\n2025/02/08 07.07.09 | 2025-02-08T07:07:09 | AAVE | -2.005   | DAI        | 500.01    |


