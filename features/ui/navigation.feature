Feature: Application Navigation

  Scenario: Navigating to Tokens Page
    Given I am on the main page
    When I click on the 'Manage Tokens' button
    Then I should be redirected to the 'Tokens' page
    When I click on the 'Back to Transactions' button
    Then I should be redirected to the main page

  Scenario: Navigating to Add Transaction Page
    Given I am on the main page
    When I click on the 'Add Transaction' button
    Then I should be redirected to the 'Add Transaction' page
    When I click on the 'Back to Transactions' button
    Then I should be redirected to the main page

