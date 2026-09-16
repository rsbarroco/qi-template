"""`python -m evals` end to end through typer's CliRunner, with the fake claude."""
from __future__ import annotations

import json
import shutil
import stat

import pytest
from typer.testing import CliRunner

from evals import __main__ as evals_cli
from evals import runner

from tests.test_evals_runner import FAKE_CLAUDE

cli = CliRunner()


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    skill_copy = tmp_path / "evals" / "ticket-intake"
    shutil.copytree(runner.EVALS_DIR / "ticket-intake", skill_copy)
    for f in ("runs.jsonl", "labels.jsonl"):
        (skill_copy / f).unlink(missing_ok=True)
    monkeypatch.setattr(runner, "EVALS_DIR", tmp_path / "evals")
    monkeypatch.setattr(runner, "RUNS_ROOT", tmp_path / "runs")
    fake = tmp_path / "fake-claude"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("QI_EVAL_CLAUDE_BIN", str(fake))
    monkeypatch.setenv("QA_NAME", "tester")
    return skill_copy


def test_run_dry_prints_a_verdict_per_case_and_costs_nothing(isolated):
    result = cli.invoke(evals_cli.app, ["run", "ticket-intake", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert result.output.count("FAIL") >= 4          # every case fails on the untouched fixture
    assert "total cost $0.00" in result.output
    assert not (isolated / "runs.jsonl").exists()      # dry runs are not data


def test_run_single_case_with_repetitions(isolated):
    result = cli.invoke(evals_cli.app, ["run", "ticket-intake", "--case", "happy-path", "--runs", "2"])
    assert result.exit_code == 0, result.output
    assert result.output.count("PASS  happy-path") == 2
    assert "total cost $0.84" in result.output
    assert len((isolated / "runs.jsonl").read_text().splitlines()) == 2


def test_run_unknown_case_fails_loudly(isolated):
    result = cli.invoke(evals_cli.app, ["run", "ticket-intake", "--case", "nope"])
    assert result.exit_code != 0
    assert "no case named" in (result.output + str(result.exception))


def test_label_walks_pending_runs_and_records_verdicts(isolated):
    cli.invoke(evals_cli.app, ["run", "ticket-intake", "--case", "happy-path", "--runs", "2"])
    result = cli.invoke(evals_cli.app, ["label", "ticket-intake"], input="f\nsaid tested, showed nothing\nq\n")
    assert result.exit_code == 0, result.output
    labels = [json.loads(l) for l in (isolated / "labels.jsonl").read_text().splitlines()]
    assert len(labels) == 1
    assert labels[0]["verdict"] == "fail" and labels[0]["labeler"] == "tester"
    assert labels[0]["critique"] == "said tested, showed nothing"


def test_label_skip_leaves_run_unlabeled(isolated):
    cli.invoke(evals_cli.app, ["run", "ticket-intake", "--case", "happy-path"])
    result = cli.invoke(evals_cli.app, ["label", "ticket-intake"], input="s\n")
    assert result.exit_code == 0
    assert not (isolated / "labels.jsonl").exists()
    again = cli.invoke(evals_cli.app, ["label", "ticket-intake"], input="p\nclean run\n")
    assert "recorded" in again.output


def test_label_with_nothing_pending(isolated):
    result = cli.invoke(evals_cli.app, ["label", "ticket-intake"])
    assert "Nothing to label" in result.output


def test_report_after_runs_and_labels(isolated):
    cli.invoke(evals_cli.app, ["run", "ticket-intake", "--case", "happy-path"])
    cli.invoke(evals_cli.app, ["label", "ticket-intake"], input="f\nno evidence\n")
    result = cli.invoke(evals_cli.app, ["report", "ticket-intake"])
    assert result.exit_code == 0, result.output
    assert "happy-path" in result.output and "labeled 1/30" in result.output


def test_unknown_skill_is_an_error(isolated):
    result = cli.invoke(evals_cli.app, ["report", "does-not-exist"])
    assert result.exit_code != 0
