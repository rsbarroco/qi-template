from qi.config import Config


def test_has_sql_true():
    cfg = Config(sql_dbs=["postgresql", "mysql"])
    assert cfg.has_sql is True


def test_has_sql_false():
    cfg = Config(sql_dbs=[])
    assert cfg.has_sql is False


def test_has_nosql_true():
    cfg = Config(nosql_dbs=["mongodb"])
    assert cfg.has_nosql is True


def test_has_nosql_false():
    cfg = Config()
    assert cfg.has_nosql is False


def test_has_ui_web():
    cfg = Config(ui_web=True)
    assert cfg.has_ui is True


def test_has_ui_mobile():
    cfg = Config(ui_mobile_ios=True)
    assert cfg.has_ui is True


def test_has_ui_false():
    cfg = Config(ui_web=False, ui_mobile_ios=False, ui_mobile_android=False)
    assert cfg.has_ui is False


def test_has_queues_true():
    cfg = Config(queues=["sqs"])
    assert cfg.has_queues is True


def test_has_queues_false():
    cfg = Config(queues=[])
    assert cfg.has_queues is False


def test_has_cloud_true():
    cfg = Config(cloud="aws")
    assert cfg.has_cloud is True


def test_has_cloud_false():
    cfg = Config(cloud="none")
    assert cfg.has_cloud is False


# --- config file (non-interactive) ------------------------------------------------------

import pytest
from qi.config import config_from_dict


def test_config_from_dict_derives_the_slug_and_keeps_defaults():
    cfg = config_from_dict({"project_name": "Acme Shop QA", "tracker": "jira", "tracker_project_key": "SHOP"})
    assert cfg.project_slug == "acme-shop-qa" and cfg.tracker == "jira"
    assert cfg.doc_platform == "none" and cfg.sql_dbs == [] and cfg.ui_web is False


def test_config_from_dict_lists_every_problem_at_once():
    with pytest.raises(ValueError) as exc:
        config_from_dict({"tracker": "trello", "sql_dbs": "postgresql", "ui_web": "yes", "colour": "blue"})
    msg = str(exc.value)
    for needle in ["project_name is required", "tracker: 'trello'", "sql_dbs must be a list", "ui_web must be true or false", "unknown key 'colour'"]:
        assert needle in msg, needle


def test_config_from_dict_rejects_values_the_menus_do_not_offer():
    with pytest.raises(ValueError, match="queues: 'nats'"):
        config_from_dict({"project_name": "x", "queues": ["sqs", "nats"]})
