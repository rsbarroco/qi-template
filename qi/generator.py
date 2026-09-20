from datetime import date
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

from qi.config import Config
from qi.skills import SKILLS, skill

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
        ("rules/dependencies.md.j2",                  ".claude/rules/dependencies.md"),
        # Hooks — the gates as code (settings.json wires them; AUTONOMY.md explains the levels)
        ("hooks/settings.json.j2",                    ".claude/settings.json"),
        ("hooks/_lib.py.j2",                          ".claude/hooks/_lib.py"),
        ("hooks/protect_paths.py.j2",                 ".claude/hooks/protect_paths.py"),
        ("hooks/guard_bash.py.j2",                    ".claude/hooks/guard_bash.py"),
        ("hooks/stop_gate.py.j2",                     ".claude/hooks/stop_gate.py"),
        ("hooks/autonomy.json.j2",                    ".claude/autonomy.json"),
        ("AUTONOMY.md.j2",                            "AUTONOMY.md"),
        # Architecture decision records
        ("decisions/README.md.j2",                    "docs/decisions/README.md"),
        ("decisions/TEMPLATE.md.j2",                  "docs/decisions/TEMPLATE.md"),
        ("decisions/0001-hooks-enforce-the-constitution.md.j2", "docs/decisions/0001-hooks-enforce-the-constitution.md"),
        # Core skills — always useful
        skill("fix-tests"),
        skill("diagnose"),
        skill("report-bug"),
        skill("verify-ticket"),
        skill("gap-analysis"),
        skill("sprint-report"),
        skill("json-schema"),
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
            ("rules/pipeline.md.j2",                   ".claude/rules/pipeline.md"),
            ("agents/test-design-agent.md.j2",         ".claude/agents/test-design-agent.md"),
            skill("handoff-protocol"),
            skill("convention-check"),
            skill("discovery"),
            skill("ticket-intake"),
        ]

    if cfg.has_pipeline and cfg.has_test_repo:
        pairs += [
            ("agents/bdd-agent.md.j2",                 ".claude/agents/bdd-agent.md"),
            ("agents/manual-agent.md.j2",              ".claude/agents/manual-agent.md"),
            ("agents/automation-agent.md.j2",          ".claude/agents/automation-agent.md"),
            skill("bdd-writer"),
            ("references/automation-coverage.md.j2",   ".claude/references/automation-coverage.md"),
            ("references/test-sections.md.j2",         ".claude/references/test-sections.md"),
        ]
    elif not cfg.has_pipeline:
        # Simple workflow: no agent pipeline, just the ticket-intake skill
        pairs.append(skill("ticket-intake"))

    # ---- Communication platform ----
    if cfg.has_comm_platform:
        pairs.append(skill("comm-broadcast"))

    # ---- Database skills ----
    if cfg.has_sql:
        pairs.append(skill("sql-query"))
    if cfg.has_nosql:
        pairs += [
            skill("nosql-query"),
            ("scripts/nosql_query.py.j2", "scripts/nosql_query.py"),
        ]

    # ---- UI skills ----
    if cfg.ui_web:
        pairs += [
            skill("web-ui"),
            ("rules/test-execution-path.md.j2",        ".claude/rules/test-execution-path.md"),
        ]
    if cfg.has_mobile:
        pairs.append(skill("mobile"))

    # ---- Infrastructure skills ----
    if cfg.has_cloud:
        pairs.append(skill("cloud-logs"))
    if cfg.has_queues:
        pairs.append(skill("queue-testing"))
    if cfg.has_performance:
        pairs.append(skill("performance"))

    # ---- Doc platform extras ----
    if cfg.doc_platform == "confluence":
        pairs.append(("rules/confluence-editing.md.j2", ".claude/rules/confluence-editing.md"))

    # ---- CI/CD ----
    if cfg.ci == "github_actions":
        pairs += [
            ("ci/github-actions.yml.j2", ".github/workflows/tests.yml"),
            ("ci/dependabot.yml.j2",     ".github/dependabot.yml"),
        ]
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
        text = tpl.render(**ctx)
        if out_path.startswith(".claude/skills/"):
            name = out_path.split("/")[2]
            text = SKILLS[name].frontmatter() + text
        out.write_text(text, encoding="utf-8")
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
        "uses_npm":               cfg.uses_npm,
        "generated_on":           date.today().isoformat(),
        "side_effect_skills":     sorted(m.name for m in SKILLS.values() if m.side_effect),
    }
