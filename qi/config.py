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
    sql_dbs: list[str] = field(default_factory=list)    # postgres | mysql | sqlite | mssql
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
