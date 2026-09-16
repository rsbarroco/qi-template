"""
Tests for the generator engine.

Strategy: use three representative configs that cover the main branches —
minimal (no optional stack), full (all options), and mobile-only (no web/SQL).
Assert that the right files are created and that rendered content contains
expected strings for each config.
"""

from pathlib import Path

import pytest

from qi.config import Config
from qi.generator import generate, list_files


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _minimal_cfg() -> Config:
    """No optional connectors — only the always-generated files."""
    return Config(
        project_name="Minimal Project",
        project_slug="minimal-project",
        tracker="none",
        doc_platform="none",
        sql_dbs=[],
        nosql_dbs=[],
        ui_web=False,
        ui_mobile_ios=False,
        ui_mobile_android=False,
        test_framework="none",
        cloud="none",
        queues=[],
        ci="none",
    )


def _full_cfg() -> Config:
    """All optional connectors selected."""
    return Config(
        project_name="Full Stack Project",
        project_slug="full-stack-project",
        tracker="jira",
        tracker_project_key="FULL",
        doc_platform="confluence",
        sql_dbs=["postgresql"],
        nosql_dbs=["mongodb"],
        ui_web=True,
        ui_mobile_ios=True,
        ui_mobile_android=True,
        test_framework="robot",
        cloud="gcp",
        queues=["sqs", "pubsub"],
        ci="github_actions",
    )


def _mobile_cfg() -> Config:
    """Mobile only — no web UI, no SQL, GitHub Issues tracker."""
    return Config(
        project_name="Mobile App Tests",
        project_slug="mobile-app-tests",
        tracker="github_issues",
        tracker_project_key="my-org/my-app",
        doc_platform="notion",
        sql_dbs=[],
        nosql_dbs=["dynamodb"],
        ui_web=False,
        ui_mobile_ios=True,
        ui_mobile_android=True,
        test_framework="custom",
        cloud="aws",
        queues=[],
        ci="gitlab_ci",
    )


# ---------------------------------------------------------------------------
# list_files tests
# ---------------------------------------------------------------------------

ALWAYS_FILES = {
    "CLAUDE.md",
    "README.md",
    "COVERAGE.md",
    "PREREQUISITES.md",
    ".claude/rules/assertion-validity.md",
    ".claude/rules/evidence-based-qa.md",
    ".claude/rules/environment-safety.md",
    ".claude/rules/connection-validation.md",
    ".claude/rules/coverage-sync.md",
    ".claude/rules/feedback-loop.md",
    ".claude/rules/reusable-test-data.md",
    ".claude/skills/ticket-intake.md",
    ".claude/skills/verify-ticket.md",
    ".claude/skills/gap-analysis.md",
    ".claude/skills/sprint-report.md",
    ".claude/skills/json-schema.md",
    "scripts/qa_track.py",
    "scripts/coverage_report.py",
    "scripts/README-qa-activity.md",
    "specs/README.md",
}


def test_minimal_file_list_contains_always_files():
    files = set(list_files(_minimal_cfg()))
    assert ALWAYS_FILES.issubset(files)


def test_minimal_file_list_has_no_conditional_files():
    files = set(list_files(_minimal_cfg()))
    assert ".claude/skills/sql-query.md" not in files
    assert ".claude/skills/nosql-query.md" not in files
    assert ".claude/skills/web-ui.md" not in files
    assert ".claude/skills/mobile.md" not in files
    assert ".claude/skills/cloud-logs.md" not in files
    assert ".claude/skills/queue-testing.md" not in files
    assert ".github/workflows/tests.yml" not in files


def test_full_config_includes_all_conditional_skills():
    files = set(list_files(_full_cfg()))
    assert ".claude/skills/sql-query.md" in files
    assert ".claude/skills/nosql-query.md" in files
    assert ".claude/skills/web-ui.md" in files
    assert ".claude/skills/mobile.md" in files
    assert ".claude/skills/cloud-logs.md" in files
    assert ".claude/skills/queue-testing.md" in files
    assert ".github/workflows/tests.yml" in files


def test_mobile_config_includes_mobile_not_web_ui(tmp_path):
    files = set(list_files(_mobile_cfg()))
    assert ".claude/skills/mobile.md" in files
    assert ".claude/skills/web-ui.md" not in files
    assert ".claude/skills/sql-query.md" not in files
    assert ".claude/skills/nosql-query.md" in files       # DynamoDB selected
    assert ".gitlab-ci.yml" in files
    assert ".github/workflows/tests.yml" not in files


# ---------------------------------------------------------------------------
# generate() — file creation and content tests
# ---------------------------------------------------------------------------

def test_generate_minimal_creates_all_files(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    for rel in list_files(_minimal_cfg()):
        assert (tmp_path / rel).exists(), f"Missing: {rel}"


def test_generate_full_creates_all_files(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    for rel in list_files(_full_cfg()):
        assert (tmp_path / rel).exists(), f"Missing: {rel}"


def test_claude_md_contains_project_name(tmp_path: Path):
    cfg = _full_cfg()
    generate(cfg, tmp_path)
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Full Stack Project" in content


def test_claude_md_contains_tracker_label(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Jira" in content


def test_claude_md_minimal_has_no_sql_section(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "SQL DB" not in content
    assert "NoSQL" not in content


def test_claude_md_full_has_sql_and_nosql(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "SQL" in content
    assert "NoSQL" in content


def test_ticket_intake_skill_references_tracker(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/ticket-intake.md").read_text(encoding="utf-8")
    assert "Jira" in content           # tracker_label in step 2
    assert "FULL" in content           # tracker_project_key in step 2
    assert "Confluence" in content     # doc_platform in step 7


def test_github_issues_tracker_in_ticket_intake(tmp_path: Path):
    generate(_mobile_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/ticket-intake.md").read_text(encoding="utf-8")
    assert "GitHub Issues" in content  # tracker_label in step 2
    assert "my-org/my-app" in content  # tracker_project_key in step 2


def test_mobile_skill_mentions_ios_and_android(tmp_path: Path):
    generate(_mobile_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/mobile.md").read_text(encoding="utf-8")
    assert "iOS" in content
    assert "Android" in content


def test_queue_testing_skill_mentions_sqs(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/queue-testing.md").read_text(encoding="utf-8")
    assert "SQS" in content


def test_cloud_logs_skill_mentions_gcp(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/cloud-logs.md").read_text(encoding="utf-8")
    assert "GCP" in content or "Cloud Logging" in content


def test_github_actions_ci_is_generated(tmp_path: Path):
    generate(_full_cfg(), tmp_path)
    ci_file = tmp_path / ".github/workflows/tests.yml"
    assert ci_file.exists()
    content = ci_file.read_text(encoding="utf-8")
    assert "actions/checkout" in content


def test_gitlab_ci_is_generated(tmp_path: Path):
    generate(_mobile_cfg(), tmp_path)
    ci_file = tmp_path / ".gitlab-ci.yml"
    assert ci_file.exists()
    content = ci_file.read_text(encoding="utf-8")
    assert "stages:" in content


def test_qa_track_script_is_generated_and_runnable(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    script = tmp_path / "scripts/qa_track.py"
    assert script.exists()
    # Verify it's valid Python by compiling it
    compile(script.read_text(encoding="utf-8"), str(script), "exec")


def test_coverage_report_script_is_valid_python(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    script = tmp_path / "scripts/coverage_report.py"
    assert script.exists()
    compile(script.read_text(encoding="utf-8"), str(script), "exec")


# ---------------------------------------------------------------------------
# Performance skill tests
# ---------------------------------------------------------------------------

def _k6_cfg() -> Config:
    return Config(
        project_name="Perf Project",
        project_slug="perf-project",
        performance="k6",
    )


def _locust_cfg() -> Config:
    return Config(
        project_name="Perf Project",
        project_slug="perf-project",
        performance="locust",
    )


def test_performance_skill_generated_when_selected(tmp_path: Path):
    generate(_k6_cfg(), tmp_path)
    skill = tmp_path / ".claude/skills/performance.md"
    assert skill.exists()


def test_performance_skill_not_generated_when_none(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    assert not (tmp_path / ".claude/skills/performance.md").exists()


def test_performance_skill_k6_contains_k6_content(tmp_path: Path):
    generate(_k6_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/performance.md").read_text(encoding="utf-8")
    assert "k6" in content
    assert "http_req_duration" in content


def test_performance_skill_locust_contains_locust_content(tmp_path: Path):
    generate(_locust_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/performance.md").read_text(encoding="utf-8")
    assert "locust" in content.lower()
    assert "HttpUser" in content


# ---------------------------------------------------------------------------
# Mobile framework variant tests
# ---------------------------------------------------------------------------

def _detox_cfg() -> Config:
    return Config(
        project_name="Mobile Project",
        project_slug="mobile-project",
        ui_mobile_ios=True,
        ui_mobile_framework="detox",
    )


def _espresso_cfg() -> Config:
    return Config(
        project_name="Native Mobile",
        project_slug="native-mobile",
        ui_mobile_android=True,
        ui_mobile_framework="espresso_xcuitest",
    )


def test_mobile_skill_detox_mentions_react_native(tmp_path: Path):
    generate(_detox_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/mobile.md").read_text(encoding="utf-8")
    assert "Detox" in content
    assert "React Native" in content


def test_mobile_skill_detox_has_setup_commands(tmp_path: Path):
    generate(_detox_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/mobile.md").read_text(encoding="utf-8")
    assert "detox-cli" in content or "npx detox" in content


def test_mobile_skill_espresso_mentions_espresso(tmp_path: Path):
    generate(_espresso_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/mobile.md").read_text(encoding="utf-8")
    assert "Espresso" in content


def test_mobile_skill_appium_default(tmp_path: Path):
    generate(_mobile_cfg(), tmp_path)
    content = (tmp_path / ".claude/skills/mobile.md").read_text(encoding="utf-8")
    assert "Appium" in content


# ---------------------------------------------------------------------------
# PREREQUISITES.md tests
# ---------------------------------------------------------------------------

def test_prerequisites_generated_for_minimal(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    prereq = tmp_path / "PREREQUISITES.md"
    assert prereq.exists()
    content = prereq.read_text(encoding="utf-8")
    assert "Python 3" in content


def test_prerequisites_mentions_node_for_playwright(tmp_path: Path):
    cfg = Config(
        project_name="Playwright Project",
        project_slug="playwright-project",
        test_framework="playwright",
    )
    generate(cfg, tmp_path)
    content = (tmp_path / "PREREQUISITES.md").read_text(encoding="utf-8")
    assert "Node.js" in content


def test_prerequisites_mentions_java_for_jmeter(tmp_path: Path):
    cfg = Config(
        project_name="Perf Project",
        project_slug="perf-project",
        performance="jmeter",
    )
    generate(cfg, tmp_path)
    content = (tmp_path / "PREREQUISITES.md").read_text(encoding="utf-8")
    assert "Java" in content


def test_prerequisites_no_node_for_minimal(tmp_path: Path):
    generate(_minimal_cfg(), tmp_path)
    content = (tmp_path / "PREREQUISITES.md").read_text(encoding="utf-8")
    assert "Node.js" not in content


def test_dossier_templates_and_intake_step_are_generated(tmp_path):
    generate(_minimal_cfg(), tmp_path)
    assert (tmp_path / "qa/dossiers/README.md").exists()
    template = (tmp_path / "qa/dossiers/TEMPLATE.md").read_text()
    assert "Traversal log" in template and "NOT FOUND" in template
    intake = (tmp_path / ".claude/skills/ticket-intake.md").read_text()
    assert "Step 2 — Dossier" in intake
    assert "at most 8 fetched items" in intake
    assert "tickets/<KEY>.md" in intake          # tracker == none branch
    claude = (tmp_path / "CLAUDE.md").read_text()
    assert "2. Dossier" in claude and "Three hard gates" in claude


def test_intake_dossier_names_the_tracker_api(tmp_path):
    generate(_full_cfg(), tmp_path)   # jira
    intake = (tmp_path / ".claude/skills/ticket-intake.md").read_text()
    assert "issuelinks" in intake and "tickets/<KEY>.md" not in intake
