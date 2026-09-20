from __future__ import annotations

import re
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from qi.config import Config

scenarios("pipeline.feature")


@given(parsers.parse('a team on Jira project "{key}" with Confluence and TestRail'), target_fixture="config")
def full_team(key):
    return Config(project_name="Shop QA", project_slug="shop-qa", tracker="jira", tracker_project_key=key,
                  doc_platform="confluence", test_repo="testrail", test_repo_project_key="2")


@given(parsers.parse('a team on Jira project "{key}" with Confluence and no test repo'), target_fixture="config")
def design_only_team(key):
    return Config(project_name="Shop QA", project_slug="shop-qa", tracker="jira", tracker_project_key=key,
                  doc_platform="confluence")


def _names(quoted: str) -> list[str]:
    return re.findall(r'"([^"]+)"', quoted)


@then(parsers.re(r'the agents (?P<quoted>.+) are generated$'))
def agents_present(project, quoted):
    for name in _names(quoted):
        assert (project / ".claude/agents" / f"{name}.md").exists(), name


@then(parsers.re(r'the agents (?P<quoted>.+) are not generated$'))
def agents_absent(project, quoted):
    for name in _names(quoted):
        assert not (project / ".claude/agents" / f"{name}.md").exists(), name


@then("CLAUDE.md drives tickets with a phase-derivation table")
def has_table(project):
    assert "Phase-derivation table" in (project / "CLAUDE.md").read_text(encoding="utf-8")


@then("the first probe in CLAUDE.md is the ticket dossier")
def first_probe_is_dossier(project):
    claude = (project / "CLAUDE.md").read_text(encoding="utf-8")
    table = claude[claude.index("Phase-derivation table"):claude.index("## 0. Pre-flight")]
    rows = [r for r in table.splitlines() if r.startswith("|") and not r.startswith("|---") and "Probe" not in r]
    assert "qa/dossiers/<KEY>.md" in rows[0]


@then("the test-design-agent takes the dossier as input")
def agent_takes_dossier(project):
    assert '"dossier_path"' in (project / ".claude/agents/test-design-agent.md").read_text(encoding="utf-8")
