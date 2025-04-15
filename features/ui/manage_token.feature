Feature: Manage Tokens

  Scenario: Successfully adding a new token
    Given I am on the 'Tokens' page
    When I fill in the 'Add Token' form with valid data
    And I click on the 'Add Token' button 
    Then I should see a success message "Token 'AAVE' marked as non-stablecoin"
    And I should see the token in the list
    And the 'Add Token' form should remain visible
    And the 'Token' field should be empty

