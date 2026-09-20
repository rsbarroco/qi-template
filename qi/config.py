from dataclasses import dataclass, field


@dataclass
class Config:
    project_name: str = ""
    project_slug: str = ""           # kebab-case, used in file paths

    # Task / issue tracking
    tracker: str = "none"            # jira | github_issues | linear | azure_devops | none
    tracker_project_key: str = ""    # e.g. "PROJ", "my-org/my-repo"
    doc_platform: str = "none"       # confluence | notion | github_wiki | none

    # Test case repository
    test_repo: str = "none"          # testrail | zephyr | xray | azure_test_plans | local_files | none
    test_repo_project_key: str = ""  # project/suite ID in the test management system

    # Communication
    comm_platform: str = "none"      # slack | teams | discord | none
    comm_platform_channel: str = ""  # channel name or ID

    # Databases
    sql_dbs: list[str] = field(default_factory=list)    # postgresql | mysql | sqlite | mssql
    nosql_dbs: list[str] = field(default_factory=list)  # mongodb | redis | dynamodb | firestore

    # UI / mobile
    ui_web: bool = False
    ui_mobile_ios: bool = False
    ui_mobile_android: bool = False
    ui_mobile_framework: str = "appium"  # appium | detox | espresso_xcuitest

    # Test framework (determines what specs automation-agent generates)
    test_framework: str = "none"     # robot | playwright | cypress | jest | webdriverio | custom | none

    # Performance testing
    performance: str = "none"        # k6 | locust | jmeter | gatling | artillery | none

    # Infrastructure
    cloud: str = "none"              # aws | gcp | azure | none
    queues: list[str] = field(default_factory=list)  # sqs | pubsub | kafka | rabbitmq
    ci: str = "none"                 # github_actions | gitlab_ci | jenkins | none

    # ---------- Derived helpers ----------

    @property
    def has_sql(self) -> bool:
        return bool(self.sql_dbs)

    @property
    def has_nosql(self) -> bool:
        return bool(self.nosql_dbs)

    @property
    def has_ui(self) -> bool:
        return self.ui_web or self.ui_mobile_ios or self.ui_mobile_android

    @property
    def has_mobile(self) -> bool:
        return self.ui_mobile_ios or self.ui_mobile_android

    @property
    def has_queues(self) -> bool:
        return bool(self.queues)

    @property
    def has_cloud(self) -> bool:
        return self.cloud != "none"

    @property
    def has_performance(self) -> bool:
        return self.performance != "none"

    @property
    def has_test_repo(self) -> bool:
        return self.test_repo != "none"

    @property
    def has_comm_platform(self) -> bool:
        return self.comm_platform != "none"

    @property
    def has_pipeline(self) -> bool:
        """True when the full 4-phase QA agent pipeline is warranted.

        Requires a tracker (to get tickets) plus at least one of: a doc platform
        (to publish Test Design docs) or a test repo (to publish cases).
        """
        return self.tracker != "none" and (
            self.doc_platform != "none" or self.test_repo != "none"
        )


# Values the menus offer; a config file must use the same ones (qi/prompts.py).
ALLOWED = {
    "tracker": {"jira", "github_issues", "linear", "azure_devops", "none"},
    "doc_platform": {"confluence", "notion", "github_wiki", "none"},
    "test_repo": {"testrail", "zephyr", "xray", "azure_test_plans", "local_files", "none"},
    "comm_platform": {"slack", "teams", "discord", "none"},
    "sql_dbs": {"postgresql", "mysql", "sqlite", "mssql"},
    "nosql_dbs": {"mongodb", "redis", "dynamodb", "firestore"},
    "ui_mobile_framework": {"appium", "detox", "espresso_xcuitest"},
    "test_framework": {"robot", "playwright", "pytest", "cypress", "jest", "webdriverio", "junit", "custom", "none"},
    "performance": {"k6", "locust", "jmeter", "gatling", "artillery", "none"},
    "cloud": {"aws", "gcp", "azure", "none"},
    "queues": {"sqs", "pubsub", "kafka", "rabbitmq"},
    "ci": {"github_actions", "gitlab_ci", "jenkins", "none"},
}


LIST_FIELDS = {"sql_dbs", "nosql_dbs", "queues"}


def slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def config_from_dict(data: dict) -> Config:
    """Build a Config from a JSON/dict answer set (the non-interactive path).

    Unknown keys, wrong types and values the menus do not offer raise ValueError with
    every problem listed, so a CI run fails once with the whole list.
    """
    from dataclasses import fields
    known = {f.name: f for f in fields(Config)}
    errors: list[str] = []
    for key in data:
        if key not in known:
            errors.append(f"unknown key {key!r}")
    if not str(data.get("project_name", "")).strip():
        errors.append("project_name is required")
    for key, allowed in ALLOWED.items():
        if key not in data:
            continue
        value = data[key]
        values = value if isinstance(value, list) else [value]
        if key in LIST_FIELDS and not isinstance(value, list):
            errors.append(f"{key} must be a list, got {value!r}")
            continue
        for v in values:
            if v not in allowed:
                errors.append(f"{key}: {v!r} is not one of {sorted(allowed)}")
    for key in ("ui_web", "ui_mobile_ios", "ui_mobile_android"):
        if key in data and not isinstance(data[key], bool):
            errors.append(f"{key} must be true or false")
    if errors:
        raise ValueError("invalid config:\n  - " + "\n  - ".join(errors))
    cfg = Config(**{k: v for k, v in data.items() if k in known})
    if not cfg.project_slug:
        cfg.project_slug = slugify(cfg.project_name)
    return cfg
