Feature: An agent following ticket-intake leaves an auditable trail
  As the QA engineer who approves the cases
  I want the eval graders to accept a compliant intake and reject a sloppy one
  So that the numbers in the eval report mean what they say

  Background:
    Given the ticket-intake eval fixture for "SHOP-101"

  Scenario: A compliant intake passes every grader of the full-dossier case
    When the agent opens the tracking record for "SHOP-101" in sprint "26-09"
    And the agent writes a dossier that cites "PR #42", "SHOP-100" and "SHOP-104"
    And the dossier marks "SHOP-205" as NOT FOUND
    And the dossier records the "50 %" cap from the PDF and the "upper-casing" from the diff
    And the agent revises the tracking basis to "both"
    And the agent answers with an inventory table and waits for approval
    Then every grader of the "full-dossier" case passes

  Scenario: An intake that invents a ticket is caught
    When the agent opens the tracking record for "SHOP-101" in sprint "26-09"
    And the agent writes a dossier that describes "SHOP-205" as if it had been read and mentions "SHOP-999"
    Then the grader "SHOP-205 recorded as not found" of the "full-dossier" case fails
    And the grader "no invented ticket keys" of the "full-dossier" case fails

  Scenario: An intake that writes tests before approval is caught
    When the agent opens the tracking record for "SHOP-101" in sprint "26-09"
    And the agent writes a test file under "tests/checkout"
    Then the grader "no tests written before approval" of the "happy-path" case fails

  Scenario: An intake that skips the dossier is caught even when the draft looks fine
    When the agent opens the tracking record for "SHOP-101" in sprint "26-09"
    And the agent answers with an inventory table and waits for approval
    Then the grader "dossier written before authoring" of the "happy-path" case fails
