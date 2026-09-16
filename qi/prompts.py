import re
import questionary
from qi.config import Config


# Menu label -> the value templates branch on. Keep in sync with Config's docstrings and
# the `{% if 'mssql' in sql_dbs %}`-style checks in qi/templates/.
SQL_VALUES = {"PostgreSQL": "postgresql", "MySQL": "mysql", "SQLite": "sqlite", "MS SQL Server": "mssql"}
QUEUE_VALUES = {"SQS": "sqs", "Pub/Sub": "pubsub", "Kafka": "kafka", "RabbitMQ": "rabbitmq"}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def ask() -> Config:
    cfg = Config()

    cfg.project_name = questionary.text(
        "Project name?",
        validate=lambda v: bool(v.strip()) or "Name cannot be empty",
    ).ask()
    cfg.project_slug = _slug(cfg.project_name)

    cfg.tracker = questionary.select(
        "Task / issue tracker?",
        choices=[
            questionary.Choice("Jira", "jira"),
            questionary.Choice("GitHub Issues", "github_issues"),
            questionary.Choice("Linear", "linear"),
            questionary.Choice("Azure DevOps", "azure_devops"),
            questionary.Choice("None", "none"),
        ],
    ).ask()

    if cfg.tracker == "jira":
        cfg.tracker_project_key = questionary.text(
            "Jira project key (e.g. PROJ)?",
            validate=lambda v: bool(v.strip()) or "Required",
        ).ask()
    elif cfg.tracker == "github_issues":
        cfg.tracker_project_key = questionary.text(
            "GitHub repo (owner/repo)?",
            validate=lambda v: bool(v.strip()) or "Required",
        ).ask()
    elif cfg.tracker == "linear":
        cfg.tracker_project_key = questionary.text(
            "Linear team identifier?",
            validate=lambda v: bool(v.strip()) or "Required",
        ).ask()

    cfg.doc_platform = questionary.select(
        "Documentation platform?",
        choices=[
            questionary.Choice("Confluence", "confluence"),
            questionary.Choice("Notion", "notion"),
            questionary.Choice("GitHub Wiki", "github_wiki"),
            questionary.Choice("None", "none"),
        ],
    ).ask()

    sql_choices = questionary.checkbox(
        "SQL databases? (space to select, enter to confirm)",
        choices=list(SQL_VALUES),
    ).ask()
    cfg.sql_dbs = [SQL_VALUES[c] for c in (sql_choices or [])]

    nosql_choices = questionary.checkbox(
        "NoSQL databases?",
        choices=["MongoDB", "Redis", "DynamoDB", "Firestore"],
    ).ask()
    cfg.nosql_dbs = [c.lower() for c in (nosql_choices or [])]

    ui_choices = questionary.checkbox(
        "UI / frontend surfaces to test?",
        choices=["Web (browser)", "Mobile — iOS", "Mobile — Android"],
    ).ask()
    ui_choices = ui_choices or []
    cfg.ui_web = "Web (browser)" in ui_choices
    cfg.ui_mobile_ios = "Mobile — iOS" in ui_choices
    cfg.ui_mobile_android = "Mobile — Android" in ui_choices

    if cfg.has_mobile:
        cfg.ui_mobile_framework = questionary.select(
            "Mobile test framework?",
            choices=[
                questionary.Choice("Appium (cross-platform)", "appium"),
                questionary.Choice("Detox (React Native)", "detox"),
                questionary.Choice("Espresso / XCUITest (native)", "espresso_xcuitest"),
            ],
        ).ask()

    cfg.test_framework = questionary.select(
        "Primary test framework?",
        choices=[
            questionary.Choice("Robot Framework", "robot"),
            questionary.Choice("Playwright (Python/JS)", "playwright"),
            questionary.Choice("WebdriverIO", "webdriverio"),
            questionary.Choice("Cypress", "cypress"),
            questionary.Choice("Jest / Vitest", "jest"),
            questionary.Choice("Custom / other", "custom"),
            questionary.Choice("None / TBD", "none"),
        ],
    ).ask()

    cfg.performance = questionary.select(
        "Performance / load testing?",
        choices=[
            questionary.Choice("k6", "k6"),
            questionary.Choice("Locust (Python)", "locust"),
            questionary.Choice("JMeter", "jmeter"),
            questionary.Choice("Gatling", "gatling"),
            questionary.Choice("Artillery", "artillery"),
            questionary.Choice("None", "none"),
        ],
    ).ask()

    cfg.cloud = questionary.select(
        "Cloud provider / log platform?",
        choices=[
            questionary.Choice("AWS (CloudWatch, SQS…)", "aws"),
            questionary.Choice("GCP (Cloud Run, Pub/Sub…)", "gcp"),
            questionary.Choice("Azure", "azure"),
            questionary.Choice("None", "none"),
        ],
    ).ask()

    queue_choices = questionary.checkbox(
        "Async queues / message brokers?",
        choices=list(QUEUE_VALUES),
    ).ask()
    cfg.queues = [QUEUE_VALUES[c] for c in (queue_choices or [])]

    cfg.ci = questionary.select(
        "CI/CD platform?",
        choices=[
            questionary.Choice("GitHub Actions", "github_actions"),
            questionary.Choice("GitLab CI", "gitlab_ci"),
            questionary.Choice("Jenkins", "jenkins"),
            questionary.Choice("None", "none"),
        ],
    ).ask()

    return cfg
