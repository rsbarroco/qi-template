from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

from qi.config import Config

console = Console()

_env = Environment(
    loader=PackageLoader("qi", "templates"),
    autoescape=select_autoescape([]),   # plain text / markdown — no HTML escaping
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def _always() -> list[tuple[str, str]]:
    """Templates always rendered: (template_path, output_path)."""
    return [
        ("CLAUDE.md.j2",                              "CLAUDE.md"),
        ("README.md.j2",                              "README.md"),
        ("COVERAGE.md.j2",                            "COVERAGE.md"),
        ("WATCH_CANDIDATES.md.j2",                    "WATCH_CANDIDATES.md"),
        ("requirements.txt.j2",                       "requirements.txt"),
        ("PREREQUISITES.md.j2",                       "PREREQUISITES.md"),
        # Rules — always applicable
        ("rules/assertion-validity.md.j2",            ".claude/rules/assertion-validity.md"),
        ("rules/evidence-based-qa.md.j2",             ".claude/rules/evidence-based-qa.md"),
        ("rules/environment-safety.md.j2",            ".claude/rules/environment-safety.md"),
        ("rules/connection-validation.md.j2",         ".claude/rules/connection-validation.md"),
        ("rules/coverage-sync.md.j2",                 ".claude/rules/coverage-sync.md"),
        ("rules/feedback-loop.md.j2",                 ".claude/rules/feedback-loop.md"),
        ("rules/reusable-test-data.md.j2",            ".claude/rules/reusable-test-data.md"),
        # Core skills — always useful
        ("skills/fix-tests.md.j2",                   ".claude/skills/fix-tests.md"),
        ("skills/diagnose.md.j2",                    ".claude/skills/diagnose.md"),
        ("skills/report-bug.md.j2",                  ".claude/skills/report-bug.md"),
        ("skills/verify-ticket.md.j2",               ".claude/skills/verify-ticket.md"),
        ("skills/gap-analysis.md.j2",                ".claude/skills/gap-analysis.md"),
        ("skills/sprint-report.md.j2",               ".claude/skills/sprint-report.md"),
        ("skills/json-schema.md.j2",                 ".claude/skills/json-schema.md"),
        # References — living cache files (always scaffolded)
        ("references/project-constants.md.j2",       ".claude/references/project-constants.md"),
        # Scripts
        ("scripts/qa_track.py.j2",                   "scripts/qa_track.py"),
        ("scripts/coverage_report.py.j2",            "scripts/coverage_report.py"),
        ("scripts/README-qa-activity.md.j2",          "scripts/README-qa-activity.md"),
        # Specs
        ("specs/README.md.j2",                       "specs/README.md"),
        # Ticket dossiers (written by ticket-intake Step 2)
        ("qa/dossiers/README.md.j2",                 "qa/dossiers/README.md"),
        ("qa/dossiers/TEMPLATE.md.j2",               "qa/dossiers/TEMPLATE.md"),
    ]


def _conditional(cfg: Config) -> list[tuple[str, str]]:
    """Templates rendered only when the matching stack option is selected."""
    pairs: list[tuple[str, str]] = []

    # ---- Full 4-phase agent pipeline (requires tracker + doc or test repo) ----
    if cfg.has_pipeline:
        pairs += [
            ("agents/test-design-agent.md.j2",         ".claude/agents/test-design-agent.md"),
            ("skills/handoff-protocol.md.j2",          ".claude/skills/handoff-protocol.md"),
            ("skills/convention-check.md.j2",          ".claude/skills/convention-check.md"),
            ("skills/discovery.md.j2",                 ".claude/skills/discovery.md"),
            ("skills/ticket-intake.md.j2",             ".claude/skills/ticket-intake.md"),
        ]

    if cfg.has_pipeline and cfg.has_test_repo:
        pairs += [
            ("agents/bdd-agent.md.j2",                 ".claude/agents/bdd-agent.md"),
            ("agents/manual-agent.md.j2",              ".claude/agents/manual-agent.md"),
            ("agents/automation-agent.md.j2",          ".claude/agents/automation-agent.md"),
            ("skills/bdd-writer.md.j2",                ".claude/skills/bdd-writer.md"),
            ("references/automation-coverage.md.j2",   ".claude/references/automation-coverage.md"),
            ("references/test-sections.md.j2",         ".claude/references/test-sections.md"),
        ]
    elif not cfg.has_pipeline:
        # Simple workflow: no agent pipeline, just the ticket-intake skill
        pairs.append(("skills/ticket-intake.md.j2", ".claude/skills/ticket-intake.md"))

    # ---- Communication platform ----
    if cfg.has_comm_platform:
        pairs.append(("skills/comm-broadcast.md.j2", ".claude/skills/comm-broadcast.md"))

    # ---- Database skills ----
    if cfg.has_sql:
        pairs.append(("skills/sql-query.md.j2", ".claude/skills/sql-query.md"))
    if cfg.has_nosql:
        pairs += [
            ("skills/nosql-query.md.j2",  ".claude/skills/nosql-query.md"),
            ("scripts/nosql_query.py.j2", "scripts/nosql_query.py"),
        ]

    # ---- UI skills ----
    if cfg.ui_web:
        pairs += [
            ("skills/web-ui.md.j2",                    ".claude/skills/web-ui.md"),
            ("rules/test-execution-path.md.j2",        ".claude/rules/test-execution-path.md"),
        ]
    if cfg.has_mobile:
        pairs.append(("skills/mobile.md.j2", ".claude/skills/mobile.md"))

    # ---- Infrastructure skills ----
    if cfg.has_cloud:
        pairs.append(("skills/cloud-logs.md.j2", ".claude/skills/cloud-logs.md"))
    if cfg.has_queues:
        pairs.append(("skills/queue-testing.md.j2", ".claude/skills/queue-testing.md"))
    if cfg.has_performance:
        pairs.append(("skills/performance.md.j2", ".claude/skills/performance.md"))

    # ---- Doc platform extras ----
    if cfg.doc_platform == "confluence":
        pairs.append(("rules/confluence-editing.md.j2", ".claude/rules/confluence-editing.md"))

    # ---- CI/CD ----
    if cfg.ci == "github_actions":
        pairs.append(("ci/github-actions.yml.j2", ".github/workflows/tests.yml"))
    elif cfg.ci == "gitlab_ci":
        pairs.append(("ci/gitlab-ci.yml.j2", ".gitlab-ci.yml"))
    elif cfg.ci == "jenkins":
        pairs.append(("ci/jenkins.yml.j2", "Jenkinsfile"))

    return pairs


def list_files(cfg: Config) -> list[str]:
    """Return the list of output paths that would be generated (for --dry-run)."""
    return [out for _, out in _always() + _conditional(cfg)]


def generate(cfg: Config, target: Path) -> None:
    target = target.resolve()
    pairs = _always() + _conditional(cfg)
    ctx = _build_context(cfg)

    for tpl_path, out_path in pairs:
        out = target / out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        tpl = _env.get_template(tpl_path)
        out.write_text(tpl.render(**ctx), encoding="utf-8")
        console.print(f"  [green]create[/green]  {out_path}")


def _build_context(cfg: Config) -> dict:
    tracker_label = {
        "jira": "Jira",
        "github_issues": "GitHub Issues",
        "linear": "Linear",
        "azure_devops": "Azure DevOps",
        "none": "None",
    }.get(cfg.tracker, cfg.tracker)

    doc_label = {
        "confluence": "Confluence",
        "notion": "Notion",
        "github_wiki": "GitHub Wiki",
        "none": "Local files",
    }.get(cfg.doc_platform, cfg.doc_platform)

    test_repo_label = {
        "testrail": "TestRail",
        "zephyr": "Zephyr Scale",
        "xray": "Xray",
        "azure_test_plans": "Azure Test Plans",
        "local_files": "Local Markdown files",
        "none": "None",
    }.get(cfg.test_repo, cfg.test_repo)

    comm_platform_label = {
        "slack": "Slack",
        "teams": "Microsoft Teams",
        "discord": "Discord",
        "none": "None",
    }.get(cfg.comm_platform, cfg.comm_platform)

    cloud_label = {
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "none": "None",
    }.get(cfg.cloud, cfg.cloud)

    framework_label = {
        "playwright": "Playwright",
        "robot": "Robot Framework",
        "pytest": "pytest",
        "webdriverio": "WebdriverIO",
        "cypress": "Cypress",
        "jest": "Jest / Vitest",
        "junit": "JUnit / TestNG",
        "custom": "Custom",
        "none": "TBD",
    }.get(cfg.test_framework, cfg.test_framework)

    return {
        "project_name":           cfg.project_name,
        "project_slug":           cfg.project_slug,
        "tracker":                cfg.tracker,
        "tracker_label":          tracker_label,
        "tracker_project_key":    cfg.tracker_project_key,
        "doc_platform":           cfg.doc_platform,
        "doc_label":              doc_label,
        "test_repo":              cfg.test_repo,
        "test_repo_label":        test_repo_label,
        "test_repo_project_key":  cfg.test_repo_project_key,
        "comm_platform":          cfg.comm_platform,
        "comm_platform_label":    comm_platform_label,
        "comm_platform_channel":  cfg.comm_platform_channel,
        "sql_dbs":                cfg.sql_dbs,
        "nosql_dbs":              cfg.nosql_dbs,
        "ui_web":                 cfg.ui_web,
        "ui_mobile_ios":          cfg.ui_mobile_ios,
        "ui_mobile_android":      cfg.ui_mobile_android,
        "ui_mobile_framework":    cfg.ui_mobile_framework,
        "test_framework":         cfg.test_framework,
        "framework_label":        framework_label,
        "cloud":                  cfg.cloud,
        "cloud_label":            cloud_label,
        "queues":                 cfg.queues,
        "ci":                     cfg.ci,
        "performance":            cfg.performance,
        "has_sql":                cfg.has_sql,
        "has_nosql":              cfg.has_nosql,
        "has_ui":                 cfg.has_ui,
        "has_mobile":             cfg.has_mobile,
        "has_queues":             cfg.has_queues,
        "has_cloud":              cfg.has_cloud,
        "has_performance":        cfg.has_performance,
        "has_test_repo":          cfg.has_test_repo,
        "has_comm_platform":      cfg.has_comm_platform,
        "has_pipeline":           cfg.has_pipeline,
    }
