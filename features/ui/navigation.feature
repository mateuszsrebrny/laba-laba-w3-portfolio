Feature: Navigation Between UI Pages

  Scenario: Navigating to Tokens Page
    Given I am on the main page
    When I click on the 'Manage Tokens' button
    Then I should be redirected to the 'Tokens' page

  Scenario: Navigating to Add Transaction Page
    Given I am on the main page
    When I click on the 'Add Transaction' button
    Then I should be redirected to the 'Add Transaction' page

