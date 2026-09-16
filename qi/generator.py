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
        ("CLAUDE.md.j2",                          "CLAUDE.md"),
        ("README.md.j2",                          "README.md"),
        ("COVERAGE.md.j2",                        "COVERAGE.md"),
        ("rules/assertion-validity.md.j2",        ".claude/rules/assertion-validity.md"),
        ("rules/evidence-based-qa.md.j2",         ".claude/rules/evidence-based-qa.md"),
        ("rules/environment-safety.md.j2",        ".claude/rules/environment-safety.md"),
        ("rules/connection-validation.md.j2",     ".claude/rules/connection-validation.md"),
        ("rules/coverage-sync.md.j2",             ".claude/rules/coverage-sync.md"),
        ("rules/feedback-loop.md.j2",             ".claude/rules/feedback-loop.md"),
        ("rules/reusable-test-data.md.j2",        ".claude/rules/reusable-test-data.md"),
        ("skills/ticket-intake.md.j2",            ".claude/skills/ticket-intake.md"),
        ("skills/verify-ticket.md.j2",            ".claude/skills/verify-ticket.md"),
        ("skills/gap-analysis.md.j2",             ".claude/skills/gap-analysis.md"),
        ("skills/sprint-report.md.j2",            ".claude/skills/sprint-report.md"),
        ("skills/json-schema.md.j2",              ".claude/skills/json-schema.md"),
        ("scripts/qa_track.py.j2",                "scripts/qa_track.py"),
        ("scripts/coverage_report.py.j2",         "scripts/coverage_report.py"),
        ("scripts/README-qa-activity.md.j2",      "scripts/README-qa-activity.md"),
        ("specs/README.md.j2",                    "specs/README.md"),
        ("qa/dossiers/README.md.j2",              "qa/dossiers/README.md"),
        ("qa/dossiers/TEMPLATE.md.j2",            "qa/dossiers/TEMPLATE.md"),
        ("PREREQUISITES.md.j2",                   "PREREQUISITES.md"),
    ]


def _conditional(cfg: Config) -> list[tuple[str, str]]:
    """Templates rendered only when the user selected the matching stack option."""
    pairs: list[tuple[str, str]] = []

    if cfg.has_sql:
        pairs.append(("skills/sql-query.md.j2", ".claude/skills/sql-query.md"))
    if cfg.has_nosql:
        pairs.append(("skills/nosql-query.md.j2", ".claude/skills/nosql-query.md"))
    if cfg.ui_web:
        pairs.append(("skills/web-ui.md.j2", ".claude/skills/web-ui.md"))
    if cfg.ui_mobile_ios or cfg.ui_mobile_android:
        pairs.append(("skills/mobile.md.j2", ".claude/skills/mobile.md"))
    if cfg.has_cloud:
        pairs.append(("skills/cloud-logs.md.j2", ".claude/skills/cloud-logs.md"))
    if cfg.has_queues:
        pairs.append(("skills/queue-testing.md.j2", ".claude/skills/queue-testing.md"))
    if cfg.has_performance:
        pairs.append(("skills/performance.md.j2", ".claude/skills/performance.md"))
    if cfg.ci == "github_actions":
        pairs.append(("ci/github-actions.yml.j2", ".github/workflows/tests.yml"))
    elif cfg.ci == "gitlab_ci":
        pairs.append(("ci/gitlab-ci.yml.j2", ".gitlab-ci.yml"))

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
        out.write_text(tpl.render(**ctx))
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
        "none": "None",
    }.get(cfg.doc_platform, cfg.doc_platform)

    cloud_label = {
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "none": "None",
    }.get(cfg.cloud, cfg.cloud)

    return {
        "project_name": cfg.project_name,
        "project_slug": cfg.project_slug,
        "tracker": cfg.tracker,
        "tracker_label": tracker_label,
        "tracker_project_key": cfg.tracker_project_key,
        "doc_platform": cfg.doc_platform,
        "doc_label": doc_label,
        "sql_dbs": cfg.sql_dbs,
        "nosql_dbs": cfg.nosql_dbs,
        "ui_web": cfg.ui_web,
        "ui_mobile_ios": cfg.ui_mobile_ios,
        "ui_mobile_android": cfg.ui_mobile_android,
        "test_framework": cfg.test_framework,
        "cloud": cfg.cloud,
        "cloud_label": cloud_label,
        "queues": cfg.queues,
        "ci": cfg.ci,
        "has_sql": cfg.has_sql,
        "has_nosql": cfg.has_nosql,
        "has_ui": cfg.has_ui,
        "has_queues": cfg.has_queues,
        "has_cloud": cfg.has_cloud,
        "performance": cfg.performance,
        "has_performance": cfg.has_performance,
        "ui_mobile_framework": cfg.ui_mobile_framework,
        "has_mobile": cfg.has_mobile,
    }
