Feature: Manage Tokens

  Scenario: Successfully adding a new token
    Given I am on the 'Tokens' page
    When I fill in the 'Add Token' form with valid data
    And I submit the form
    Then I should see the token in the list

