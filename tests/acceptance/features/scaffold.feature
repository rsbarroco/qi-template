Feature: Scaffold a Claude-first QA constitution
  As a QA lead onboarding a team
  I want `qi` to generate only what my stack needs
  So that the agent reads rules that apply and nothing that does not

  Scenario: A Jira team with PostgreSQL and a Playwright web app
    Given a team that tracks work in Jira project "SHOP"
    And they test a web app with Playwright on PostgreSQL
    When I scaffold the project
    Then CLAUDE.md names "Jira" as the task tracker
    And the skills include "sql-query" and "web-ui"
    And the skills do not include "mobile"
    And no generated file contains unrendered template markup

  Scenario: Choosing "None" everywhere generates the core only
    Given a team with no tracker, no database and no UI
    When I scaffold the project
    Then exactly the core skills are generated
    And there is no CI workflow

  Scenario: A mobile team gets the mobile skill for its framework
    Given a team that tests an Android app with Detox
    When I scaffold the project
    Then the skills include "mobile"
    And the mobile skill mentions "Detox"

  Scenario: Dry run shows the plan and writes nothing
    Given a team that tracks work in Jira project "SHOP"
    When I run qi with --dry-run
    Then the output lists "CLAUDE.md"
    And no project directory is created
