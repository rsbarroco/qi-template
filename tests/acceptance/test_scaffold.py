from __future__ import annotations

import re
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when
from typer.testing import CliRunner

from qi import cli
from qi.config import Config
from qi.generator import generate

scenarios("scaffold.feature")

CORE_SKILLS = {"ticket-intake.md", "verify-ticket.md", "gap-analysis.md", "sprint-report.md", "json-schema.md"}


@given(parsers.parse('a team that tracks work in Jira project "{key}"'), target_fixture="config")
def jira_team(key):
    return Config(project_name="Acme Shop QA", project_slug="acme-shop-qa", tracker="jira", tracker_project_key=key)


@given("they test a web app with Playwright on PostgreSQL")
def web_playwright_postgres(config):
    config.ui_web = True
    config.test_framework = "playwright"
    config.sql_dbs = ["postgresql"]


@given("a team with no tracker, no database and no UI", target_fixture="config")
def bare_team():
    return Config(project_name="Bare", project_slug="bare")


@given("a team that tests an Android app with Detox", target_fixture="config")
def android_detox():
    return Config(project_name="App", project_slug="app", ui_mobile_android=True, ui_mobile_framework="detox")


@when("I scaffold the project", target_fixture="project")
def scaffold(config, tmp_path) -> Path:
    target = tmp_path / config.project_slug
    generate(config, target)
    return target


@when("I run qi with --dry-run", target_fixture="dry_run")
def run_dry(config, tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: config)
    target = tmp_path / config.project_slug
    result = CliRunner().invoke(cli.app, [str(target), "--dry-run"])
    assert result.exit_code == 0, result.output
    return {"output": result.output, "target": target}


@then(parsers.parse('CLAUDE.md names "{tracker}" as the task tracker'))
def claude_names_tracker(project, tracker):
    assert re.search(rf"Task tracker.*\b{re.escape(tracker)}\b", (project / "CLAUDE.md").read_text())


@then(parsers.parse('the skills include "{a}" and "{b}"'))
def skills_include_two(project, a, b):
    for name in (a, b):
        assert (project / ".claude/skills" / f"{name}.md").exists(), name


@then(parsers.parse('the skills include "{a}"'))
def skills_include_one(project, a):
    assert (project / ".claude/skills" / f"{a}.md").exists(), a


@then(parsers.parse('the skills do not include "{name}"'))
def skills_exclude(project, name):
    assert not (project / ".claude/skills" / f"{name}.md").exists()


@then("no generated file contains unrendered template markup")
def no_jinja_left(project):
    for p in project.rglob("*"):
        if p.is_file():
            assert not re.search(r"(?<!\$){{|{%|%}", p.read_text()), p


@then("exactly the core skills are generated")
def only_core(project):
    assert {p.name for p in (project / ".claude/skills").iterdir()} == CORE_SKILLS


@then("there is no CI workflow")
def no_ci(project):
    assert not (project / ".github").exists() and not (project / ".gitlab-ci.yml").exists()


@then(parsers.parse('the mobile skill mentions "{framework}"'))
def mobile_mentions(project, framework):
    assert framework in (project / ".claude/skills/mobile.md").read_text()


@then(parsers.parse('the output lists "{name}"'))
def output_lists(dry_run, name):
    assert name in dry_run["output"]


@then("no project directory is created")
def nothing_written(dry_run):
    assert not dry_run["target"].exists()
