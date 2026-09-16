Feature: The 4-phase QA pipeline for teams with a tracker and a place to publish
  As a QA lead with Jira, Confluence and TestRail
  I want qi to scaffold the agent pipeline
  So that a ticket is driven from test design to automation without a stored state machine

  Scenario: A Jira + Confluence + TestRail team gets all four phases
    Given a team on Jira project "SHOP" with Confluence and TestRail
    When I scaffold the project
    Then the agents "test-design-agent", "bdd-agent", "manual-agent" and "automation-agent" are generated
    And the skills include "handoff-protocol" and "convention-check"
    And CLAUDE.md drives tickets with a phase-derivation table

  Scenario: A Jira + Confluence team without a test repo gets only the design phase
    Given a team on Jira project "SHOP" with Confluence and no test repo
    When I scaffold the project
    Then the agents "test-design-agent" are generated
    And the agents "bdd-agent", "manual-agent" and "automation-agent" are not generated

  Scenario: The pipeline never authors from the ticket description alone
    Given a team on Jira project "SHOP" with Confluence and TestRail
    When I scaffold the project
    Then the first probe in CLAUDE.md is the ticket dossier
    And the test-design-agent takes the dossier as input
