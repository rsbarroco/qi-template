"""Every template must render for every stack combination we ship, with no leftovers."""
from __future__ import annotations

import itertools
import re
from pathlib import Path

import pytest
import yaml

from qi.config import Config
from qi.generator import _build_context, generate, list_files

TRACKERS = ["jira", "github_issues", "linear", "azure_devops", "none"]
CIS = ["github_actions", "gitlab_ci", "jenkins", "none"]
UNRENDERED = re.compile(r"(?<!\$){{|{%|%}")   # `${{ secrets.X }}` is GitHub Actions, not Jinja


def _cfg(**over) -> Config:
    base = dict(project_name="Render Test", project_slug="render-test", tracker_project_key="KEY")
    base.update(over)
    return Config(**base)


@pytest.mark.parametrize("tracker, ci", list(itertools.product(TRACKERS, CIS)))
def test_every_tracker_ci_combination_renders_without_jinja_leftovers(tmp_path, tracker, ci):
    generate(_cfg(tracker=tracker, ci=ci, ui_web=True, sql_dbs=["postgresql"], cloud="aws",
                  queues=["sqs"], performance="k6", ui_mobile_ios=True), tmp_path)
    for path in tmp_path.rglob("*"):
        if path.is_file():
            text = path.read_text()
            assert not UNRENDERED.search(text), f"unrendered jinja in {path.relative_to(tmp_path)}"
            assert text.strip(), f"empty output {path.relative_to(tmp_path)}"


def test_list_files_matches_what_generate_writes(tmp_path):
    cfg = _cfg(ui_web=True, ci="github_actions", sql_dbs=["mysql"])
    generate(cfg, tmp_path)
    written = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file())
    assert written == sorted(list_files(cfg))


@pytest.mark.parametrize("ci, path", [("github_actions", ".github/workflows/tests.yml"), ("gitlab_ci", ".gitlab-ci.yml")])
def test_ci_files_are_valid_yaml(tmp_path, ci, path):
    generate(_cfg(ci=ci, ui_web=True, sql_dbs=["postgresql", "mssql"], nosql_dbs=["mongodb"]), tmp_path)
    data = yaml.safe_load((tmp_path / path).read_text())
    assert isinstance(data, dict) and data


def test_github_actions_uses_secrets_syntax_not_jinja(tmp_path):
    generate(_cfg(ci="github_actions", sql_dbs=["postgresql"]), tmp_path)
    text = (tmp_path / ".github/workflows/tests.yml").read_text()
    assert "${{ secrets.APP_USER }}" in text
    assert "POSTGRESQL_URL" in text


def test_every_skill_named_in_claude_md_exists(tmp_path):
    generate(_cfg(ui_web=True, sql_dbs=["postgresql"], cloud="gcp", queues=["kafka"], performance="locust"), tmp_path)
    claude = (tmp_path / "CLAUDE.md").read_text()
    for name in re.findall(r"`([a-z-]+)` skill", claude):
        assert (tmp_path / ".claude/skills" / f"{name}.md").exists(), name


def test_conditional_skills_follow_the_config(tmp_path):
    generate(_cfg(), tmp_path)   # nothing optional
    skills = {p.name for p in (tmp_path / ".claude/skills").iterdir()}
    assert skills == {"ticket-intake.md", "verify-ticket.md", "gap-analysis.md", "sprint-report.md", "json-schema.md", "fix-tests.md", "diagnose.md", "report-bug.md"}


@pytest.mark.parametrize("field, value, expect", [
    ("tracker", "jira", "Jira"), ("tracker", "github_issues", "GitHub Issues"), ("tracker", "none", "None"),
    ("doc_platform", "github_wiki", "GitHub Wiki"), ("cloud", "gcp", "GCP"),
])
def test_context_labels(field, value, expect):
    ctx = _build_context(_cfg(**{field: value}))
    key = {"tracker": "tracker_label", "doc_platform": "doc_label", "cloud": "cloud_label"}[field]
    assert ctx[key] == expect


def test_context_passes_unknown_values_through_unchanged():
    assert _build_context(_cfg(tracker="something_new"))["tracker_label"] == "something_new"


def test_prerequisites_mentions_mssql_driver_when_mssql_selected(tmp_path):
    generate(_cfg(sql_dbs=["mssql"]), tmp_path)
    assert "ODBC" in (tmp_path / "PREREQUISITES.md").read_text()
