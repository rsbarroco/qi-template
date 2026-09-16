Feature: Track AI-assisted QA work across a ticket's life
  As a QA lead reporting to the team
  I want one honest record per ticket
  So that the sprint report counts only what actually happened

  Scenario: A ticket from intake to close
    Given a generated project
    When I start tracking "SHOP-101" in sprint "26-09" labelled "Sprint 9" with basis "ac"
    And I revise the basis of "SHOP-101" to "both"
    And I add the note "read PR #42 and the epic" to "SHOP-101"
    And I count 4 manual and 3 automated cases for "SHOP-101" because "form checks stay manual"
    Then the record for "SHOP-101" has basis "both" and label "Sprint 9"
    And the record keeps its original start time
    And the sprint report for "Sprint 9" lists "SHOP-101" with "4" manual and "3" automated

  Scenario: Counts that need a reason cannot be recorded without one
    Given a generated project
    When I start tracking "SHOP-102" in sprint "26-09" labelled "Sprint 9" with basis "ac"
    And I try to count 3 manual and 1 automated cases for "SHOP-102" without a reason
    Then the count is refused
    And the status report says "SHOP-102" is missing counts
