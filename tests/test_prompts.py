"""prompts.ask() drives questionary; we script the answers and check the Config it builds.

The normalisation rules matter: templates branch on the exact strings
(`postgresql`, `mssql`, `pubsub`), so a prompt that emits `ms_sql_server` or `pub_sub`
silently disables the branch that was meant for it.
"""
from __future__ import annotations

import pytest

from qi import prompts
from qi.prompts import _slug


# --- _slug ---------------------------------------------------------------------------

@pytest.mark.parametrize("name, slug", [
    ("Acme Shop QA", "acme-shop-qa"),
    ("  Spaces   everywhere  ", "spaces-everywhere"),
    ("Under_scores & symbols!", "under-scores-symbols"),
    ("UPPER", "upper"),
    ("já-com-hífen", "j-com-h-fen"),   # non-ascii is dropped, not transliterated
    ("123 numbers", "123-numbers"),
])
def test_slug(name, slug):
    assert _slug(name) == slug


def test_slug_never_starts_or_ends_with_dash():
    assert _slug("--weird--") == "weird"


# --- scripted questionary ----------------------------------------------------------------

class _Answer:
    def __init__(self, value):
        self.value = value

    def ask(self):
        return self.value


class ScriptedQuestionary:
    """Feeds answers in order; records the prompts it was asked so tests can assert flow."""

    def __init__(self, answers: list):
        self.answers = list(answers)
        self.asked: list[str] = []

    def _next(self, message, **_):
        self.asked.append(message)
        if not self.answers:
            raise AssertionError(f"ask() asked an unexpected question: {message!r}")
        return _Answer(self.answers.pop(0))

    text = select = checkbox = _next

    class Choice:  # questionary.Choice stand-in
        def __init__(self, title, value=None):
            self.title, self.value = title, value


@pytest.fixture
def scripted(monkeypatch):
    def _install(answers):
        fake = ScriptedQuestionary(answers)
        monkeypatch.setattr(prompts, "questionary", fake)
        return fake
    return _install


def test_full_jira_flow_builds_expected_config(scripted):
    fake = scripted([
        "Acme Shop QA",                        # project name
        "jira",                                # tracker
        "SHOP",                                # jira key
        "confluence",                          # docs
        "testrail",                            # test case repository
        "2",                                   # test repo project id (asked for testrail)
        "slack",                               # comm platform
        "#qa",                                 # channel (asked because slack)
        ["PostgreSQL", "MS SQL Server"],       # sql
        ["Redis"],                             # nosql
        ["Web (browser)", "Mobile — Android"], # ui
        "detox",                               # mobile framework (asked because mobile)
        "playwright",                          # framework
        "k6",                                  # performance
        "aws",                                 # cloud
        ["SQS", "Pub/Sub"],                    # queues
        "github_actions",                      # ci
    ])
    cfg = prompts.ask()
    assert cfg.project_name == "Acme Shop QA" and cfg.project_slug == "acme-shop-qa"
    assert cfg.tracker == "jira" and cfg.tracker_project_key == "SHOP"
    assert cfg.test_repo == "testrail" and cfg.test_repo_project_key == "2"
    assert cfg.comm_platform == "slack" and cfg.comm_platform_channel == "#qa"
    assert cfg.has_pipeline
    assert cfg.sql_dbs == ["postgresql", "mssql"]
    assert cfg.nosql_dbs == ["redis"]
    assert cfg.ui_web and cfg.ui_mobile_android and not cfg.ui_mobile_ios
    assert cfg.ui_mobile_framework == "detox"
    assert cfg.queues == ["sqs", "pubsub"]
    assert cfg.ci == "github_actions"
    assert fake.answers == []                  # every scripted answer was consumed


def test_tracker_key_is_only_asked_for_trackers_that_need_it(scripted):
    fake = scripted(["P", "none", "none", "none", "none", [], [], [], "none", "none", "none", [], "none"])
    cfg = prompts.ask()
    assert cfg.tracker_project_key == ""
    assert not any(q.startswith(("Jira project key", "GitHub repo", "Linear team", "Azure DevOps project")) for q in fake.asked)
    assert not any("suite ID" in q or "channel" in q for q in fake.asked)   # test repo / comm keys not asked either


def test_mobile_framework_is_not_asked_without_a_mobile_surface(scripted):
    fake = scripted(["P", "none", "none", "none", "none", [], [], ["Web (browser)"], "none", "none", "none", [], "none"])
    cfg = prompts.ask()
    assert cfg.ui_mobile_framework == "appium"          # default untouched
    assert not any("Mobile test framework" in q for q in fake.asked)


def test_cancelled_checkboxes_become_empty_lists(scripted):
    # questionary returns None when the user hits ctrl-c on a checkbox
    scripted(["P", "none", "none", "none", "none", None, None, None, "none", "none", "none", None, "none"])
    cfg = prompts.ask()
    assert cfg.sql_dbs == [] and cfg.nosql_dbs == [] and cfg.queues == []
    assert not cfg.has_ui


@pytest.mark.parametrize("label, expected", [
    ("PostgreSQL", "postgresql"), ("MySQL", "mysql"), ("SQLite", "sqlite"), ("MS SQL Server", "mssql"),
])
def test_sql_labels_map_to_the_values_templates_branch_on(scripted, label, expected):
    scripted(["P", "none", "none", "none", "none", [label], [], [], "none", "none", "none", [], "none"])
    assert prompts.ask().sql_dbs == [expected]


@pytest.mark.parametrize("label, expected", [
    ("SQS", "sqs"), ("Pub/Sub", "pubsub"), ("Kafka", "kafka"), ("RabbitMQ", "rabbitmq"),
])
def test_queue_labels_map_to_the_values_templates_branch_on(scripted, label, expected):
    scripted(["P", "none", "none", "none", "none", [], [], [], "none", "none", "none", [label], "none"])
    assert prompts.ask().queues == [expected]


def test_test_repo_and_comm_keys_are_asked_only_when_selected(scripted):
    fake = scripted(["P", "none", "none", "local_files", "teams", "QA Team", [], [], [], "none", "none", "none", [], "none"])
    cfg = prompts.ask()
    assert cfg.test_repo == "local_files" and cfg.test_repo_project_key == ""
    assert cfg.comm_platform == "teams" and cfg.comm_platform_channel == "QA Team"
    assert not cfg.has_pipeline          # no tracker
