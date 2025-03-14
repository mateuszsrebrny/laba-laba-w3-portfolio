Scenario: Test credentials should only work from localhost
  Given the API is running
  When I log in with test credentials from localhost
  Then I should be logged in

  When I log in with test credentials from a remote IP
  Then I should be denied access
