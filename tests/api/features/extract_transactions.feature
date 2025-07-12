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
    And "DAI" is marked as a stablecoin
    And "wTAO" is marked as a non-stablecoin
    When I upload a fake Debank screenshot
    Then the response should include a transaction with timestamp "<timestamp>", token "<token>", amount "<amount>", stable_coin "<stable_coin>", and total_usd "<total_usd>"
  
    Examples:
      | ocr_text                                  | timestamp             | token | amount  | stable_coin | total_usd |
      | Contract Interaction\nlinch\n-900 DAI\n($899.91)\n+3.9982 wTAO\n($1,112.67)\n2025/02/06 05.47.49 | 2025-02-06T05:47:49   | wTAO  | 3.9982     | DAI        | -900.0    |
      | Contract Interaction\nquickswap\n800 DAI\n(s799.91)\n+3.1982 wTAO\n($1,142.67)\n2025/02/07 06.57.59 | 2025-02-07T06:57:59 | wTAO | 3.1982     | DAI        | -800.0    |
      | Contract Interaction\nquickswap\n2.005 wTAO\n(s499.91)\n+500.01 DAI\n($1,312.67)\n2025/02/08 07.07.09 | 2025-02-08T07:07:09 | wTAO | -2.005   | DAI        | 500.01    |
      | Contract Interaction 1inch 1,800 DAI ($1,799.55) +4,308.6727 wTAO (61,518.13) 2024/04/13 16.34.49 | 2024-04-13T16:34:49 | wTAO | 4308.6727   | DAI        | -1800.0   |
      | Contract Interaction 0x5b93..f995 1,008.587 DAI ($1,008.49) T +2.9089 wTAO ($932.28) 2025/02/07 15.15.11 | 2025-02-07T15:15:11 | wTAO | 2.9089 | DAI        | -1008.587 |
      | fillOrderArgs Oxa904...ed36 -0.003 wTAO ($303.33) +298.9947 DAI ($298.96) 2024/12/08 23.02.00 | 2024-12-08T23:02:00 | wTAO | -0.003 | DAI        | 298.9947 |
      | Contract Interaction linch 1,000.011 wTAO ($297.10) +178.6021DAI ($298.05) 2025/02/06 05.26.54 | 2025-02-06T05:26:54 | wTAO | -1000.011 | DAI        | 178.6021 |


