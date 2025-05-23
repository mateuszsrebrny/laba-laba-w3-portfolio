Feature: Extract transactions from Debank screenshots

  Scenario: Extracting transaction data from a Debank screenshot
    Given the API is running
    And "DAI" is marked as a stablecoin
    And "AAVE" is marked as a non-stablecoin
    When I upload a Debank screenshot containing transactions
    #Then the transactions should be extracted and stored in the database
    #And I should see the extracted transactions in the response

  Scenario: Handling an invalid image upload
    Given the API is running
    When I upload an invalid image file
    #Then I should get an error with code 400 saying "Invalid image file"

