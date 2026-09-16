Feature: Coverage numbers never drift
  As a QA lead publishing coverage to the team
  I want COVERAGE.md computed from the specs, never typed by hand
  So that a stale or contradictory number cannot reach a stakeholder

  Scenario: Recomputing after a spec row flips to automated
    Given a generated project with a "checkout" spec of 3 automated, 1 partial and 2 manual rows
    When I recompute coverage
    Then COVERAGE.md reports 6 cases, 3 automated and "50%"
    When the "checkout" spec flips one manual row to automated
    And I recompute coverage
    Then COVERAGE.md reports 6 cases, 4 automated and "67%"

  Scenario: The CI gate blocks while manual-only rows remain
    Given a generated project with a "checkout" spec of 3 automated, 1 partial and 2 manual rows
    When I run the coverage check
    Then the check fails mentioning "2 manual-only cases remain"

  Scenario: The CI gate passes once nothing is manual-only
    Given a generated project with a "cart" spec of 2 automated, 1 partial and 0 manual rows
    When I run the coverage check
    Then the check passes
