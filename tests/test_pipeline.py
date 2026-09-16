"""The 4-phase agent pipeline: when it is generated, what it contains, and that it never
authors from the ticket description alone (the dossier gate applies to it too).

Written red-first against the pipeline commit, which shipped without tests.
"""
from __future__ import annotations

import py_compile
import re
from pathlib import Path

import pytest
import yaml

from qi.config import Config
from qi.generator import _build_context, generate

PIPELINE_ONLY = {
    ".claude/agents/test-design-agent.md",
    ".claude/skills/handoff-protocol.md",
    ".claude/skills/convention-check.md",
    ".claude/skills/discovery.md",
}
TEST_REPO_ONLY = {
    ".claude/agents/bdd-agent.md",
    ".claude/agents/manual-agent.md",
    ".claude/agents/automation-agent.md",
    ".claude/skills/bdd-writer.md",
    ".claude/references/automation-coverage.md",
    ".claude/references/test-sections.md",
}


def _cfg(**over) -> Config:
    base = dict(project_name="Pipeline Test", project_slug="pipeline-test", tracker="jira",
                tracker_project_key="SHOP", doc_platform="confluence")
    base.update(over)
    return Config(**base)


def _files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


# --- when is the pipeline generated -------------------------------------------------------

@pytest.mark.parametrize("tracker, doc, repo, expected", [
    ("none", "none", "none", False),
    ("none", "confluence", "testrail", False),     # no tracker: nothing to drive
    ("jira", "none", "none", False),               # tracker alone: nowhere to publish
    ("jira", "confluence", "none", True),
    ("jira", "none", "testrail", True),
    ("github_issues", "github_wiki", "local_files", True),
])
def test_has_pipeline_truth_table(tracker, doc, repo, expected):
    assert _cfg(tracker=tracker, doc_platform=doc, test_repo=repo).has_pipeline is expected


def test_pipeline_without_test_repo_generates_only_the_design_phase(tmp_path):
    generate(_cfg(), tmp_path)
    files = _files(tmp_path)
    assert PIPELINE_ONLY <= files
    assert not (TEST_REPO_ONLY & files)
    assert ".claude/skills/ticket-intake.md" in files          # intake still exists in pipeline mode


def test_pipeline_with_test_repo_generates_all_four_phases(tmp_path):
    generate(_cfg(test_repo="testrail", test_repo_project_key="2"), tmp_path)
    files = _files(tmp_path)
    assert PIPELINE_ONLY | TEST_REPO_ONLY <= files


def test_simple_mode_has_no_agents(tmp_path):
    generate(_cfg(tracker="none", doc_platform="none"), tmp_path)
    files = _files(tmp_path)
    assert not (PIPELINE_ONLY & files) and not (TEST_REPO_ONLY & files)
    assert not (tmp_path / ".claude/agents").exists()
    assert ".claude/skills/ticket-intake.md" in files


# --- optional extras ------------------------------------------------------------------

def test_comm_platform_adds_broadcast_skill_with_channel(tmp_path):
    generate(_cfg(comm_platform="slack", comm_platform_channel="#qa-alerts"), tmp_path)
    text = (tmp_path / ".claude/skills/comm-broadcast.md").read_text()
    assert "Slack" in text and "#qa-alerts" in text and "notify-only" in text.lower()


def test_no_comm_platform_no_broadcast_skill(tmp_path):
    generate(_cfg(), tmp_path)
    assert not (tmp_path / ".claude/skills/comm-broadcast.md").exists()


@pytest.mark.parametrize("doc, present", [("confluence", True), ("notion", False), ("none", False)])
def test_confluence_editing_rule_only_for_confluence(tmp_path, doc, present):
    generate(_cfg(doc_platform=doc, test_repo="testrail"), tmp_path)
    assert (tmp_path / ".claude/rules/confluence-editing.md").exists() is present


@pytest.mark.parametrize("web, present", [(True, True), (False, False)])
def test_execution_path_rule_only_for_web_ui(tmp_path, web, present):
    generate(_cfg(ui_web=web), tmp_path)
    assert (tmp_path / ".claude/rules/test-execution-path.md").exists() is present


def test_watch_candidates_is_always_generated(tmp_path):
    generate(_cfg(tracker="none", doc_platform="none"), tmp_path)
    text = (tmp_path / "WATCH_CANDIDATES.md").read_text()
    assert "the project tracker" in text
    generate(_cfg(), tmp_path / "jira")
    assert "Jira" in (tmp_path / "jira" / "WATCH_CANDIDATES.md").read_text()


# --- generated code and config ------------------------------------------------------------

def test_nosql_script_is_generated_per_store_and_compiles(tmp_path):
    generate(_cfg(nosql_dbs=["mongodb", "redis"]), tmp_path)
    script = tmp_path / "scripts/nosql_query.py"
    text = script.read_text()
    assert "def query_mongodb" in text and "def query_redis" in text
    assert "def query_dynamodb" not in text and "firestore" not in text
    assert "_check_env" in text and "MONGODB_URI" in text
    py_compile.compile(str(script), doraise=True)


def test_no_nosql_no_script(tmp_path):
    generate(_cfg(), tmp_path)
    assert not (tmp_path / "scripts/nosql_query.py").exists()


def test_jenkinsfile_declares_a_credential_per_store(tmp_path):
    generate(_cfg(ci="jenkins", sql_dbs=["postgresql", "mssql"], nosql_dbs=["redis"], comm_platform="teams",
                  comm_platform_channel="QA"), tmp_path)
    text = (tmp_path / "Jenkinsfile").read_text()
    assert text.startswith("pipeline {")
    for line in ("POSTGRESQL_URL = credentials('qa-postgresql-url')", "MSSQL_URL = credentials('qa-mssql-url')",
                 "REDIS_URI = credentials('qa-redis-uri')", "COMM_WEBHOOK = credentials('qa-teams-webhook')"):
        assert line in text, line
    assert not re.search(r"(?<!\$){{|{%|%}", text)


@pytest.mark.parametrize("framework, expect, absent", [
    ("playwright", ["playwright>=1.40", "pytest-playwright"], ["selenium"]),
    ("robot", ["robotframework>=7.0"], ["playwright"]),
    ("custom", ["selenium>=4.15"], ["playwright"]),      # web UI without a first-class framework
])
def test_requirements_follow_the_framework(tmp_path, framework, expect, absent):
    generate(_cfg(test_framework=framework, ui_web=True), tmp_path)
    text = (tmp_path / "requirements.txt").read_text()
    for e in expect:
        assert e in text, e
    for a in absent:
        assert a not in text, a


def test_requirements_add_db_drivers(tmp_path):
    generate(_cfg(sql_dbs=["postgresql", "mssql"], nosql_dbs=["mongodb"]), tmp_path)
    text = (tmp_path / "requirements.txt").read_text()
    assert "psycopg2-binary" in text and "pyodbc" in text and "pymongo" in text
    assert "mysql-connector" not in text


@pytest.mark.parametrize("field, value, key, expect", [
    ("test_repo", "zephyr", "test_repo_label", "Zephyr Scale"),
    ("test_repo", "local_files", "test_repo_label", "Local Markdown files"),
    ("comm_platform", "teams", "comm_platform_label", "Microsoft Teams"),
    ("doc_platform", "none", "doc_label", "Local files"),
])
def test_new_context_labels(field, value, key, expect):
    assert _build_context(_cfg(**{field: value}))[key] == expect


# --- agents ---------------------------------------------------------------------------------

def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    assert text.startswith("---\n"), path
    block = text.split("---\n")[1]
    return yaml.safe_load(block)


def test_every_agent_has_valid_frontmatter_named_after_its_file(tmp_path):
    generate(_cfg(test_repo="testrail", test_repo_project_key="2"), tmp_path)
    agents = sorted((tmp_path / ".claude/agents").glob("*.md"))
    assert len(agents) == 4
    for path in agents:
        fm = _frontmatter(path)
        assert fm["name"] == path.stem
        assert fm["description"].strip() and fm["tools"]


def test_every_agent_speaks_the_handoff_contract(tmp_path):
    generate(_cfg(test_repo="testrail", test_repo_project_key="2"), tmp_path)
    for path in (tmp_path / ".claude/agents").glob("*.md"):
        text = path.read_text()
        assert '"ticket_key"' in text and '"routing"' in text, path.name


# --- the dossier gate applies to the pipeline too ---------------------------------------

def test_pipeline_claude_md_probes_the_dossier_before_any_sub_agent(tmp_path):
    generate(_cfg(), tmp_path)
    claude = (tmp_path / "CLAUDE.md").read_text()
    assert "Phase-derivation table" in claude
    assert "## 00. Ticket intake" not in claude            # simple-mode section is not rendered
    table = claude[claude.index("Phase-derivation table"):claude.index("Dispatch + handoff rules")]
    rows = [r for r in table.splitlines() if r.startswith("|") and not r.startswith("|---") and "Probe" not in r]
    assert "qa/dossiers/<KEY>.md" in rows[0], "the dossier must be the first probe"
    assert "ticket-intake" in rows[0]
    assert "Never spawn a sub-agent" in claude or "no sub-agent" in claude.lower()


def test_simple_claude_md_keeps_the_intake_section(tmp_path):
    generate(_cfg(tracker="none", doc_platform="none"), tmp_path)
    claude = (tmp_path / "CLAUDE.md").read_text()
    assert "## 00. Ticket intake" in claude and "Phase-derivation table" not in claude


def test_test_design_agent_reads_the_dossier_not_the_raw_ticket(tmp_path):
    generate(_cfg(), tmp_path)
    text = (tmp_path / ".claude/agents/test-design-agent.md").read_text()
    assert '"dossier_path"' in text
    assert "qa/dossiers/" in text
    assert "requirements found outside the acs" in text.lower()


def test_handoff_contract_carries_the_dossier_path(tmp_path):
    generate(_cfg(), tmp_path)
    text = (tmp_path / ".claude/skills/handoff-protocol.md").read_text()
    assert '"dossier_path"' in text and "REQUIRED" in text.split('"dossier_path"')[1].split("\n")[0]
