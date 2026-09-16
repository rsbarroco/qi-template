"""The generated qa_track.py is real code that agents run. Exercise it end to end."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from qi.config import Config
from qi.generator import generate


@pytest.fixture
def qa_track(tmp_path, monkeypatch):
    project = tmp_path / "project"
    generate(Config(project_name="P", project_slug="p"), project)
    activity = tmp_path / "activity"
    monkeypatch.setenv("QI_ACTIVITY_DIR", str(activity))
    monkeypatch.setenv("QA_NAME", "tester")
    script = project / "scripts" / "qa_track.py"

    def run(*args: str, expect_fail: bool = False) -> subprocess.CompletedProcess:
        proc = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
        assert (proc.returncode != 0) is expect_fail, proc.stdout + proc.stderr
        return proc

    def record(ticket: str) -> dict:
        return json.loads((activity / f"{ticket}.json").read_text())

    return run, record


START = ["start", "--ticket", "T-1", "--title", "First", "--sprint", "26-09", "--basis", "ac", "--activity", "qa"]


def test_start_writes_record_in_activity_dir(qa_track):
    run, record = qa_track
    run(*START)
    r = record("T-1")
    assert r["basis"] == "ac" and r["sprint"] == "26-09" and r["qa"] == "tester"
    assert r["sprint_label"] == "26-09" and r["started_at"] and r["notes"] == []


def test_rerunning_start_keeps_started_at_label_notes_and_counts(qa_track):
    run, record = qa_track
    run(*START, "--sprint-label", "Sprint 9")
    run("note", "--ticket", "T-1", "read the epic")
    run("count", "--ticket", "T-1", "--manual", "3", "--automated", "3")
    first = record("T-1")

    run("start", "--ticket", "T-1", "--title", "First (renamed)", "--sprint", "26-09", "--basis", "both", "--activity", "qa")
    second = record("T-1")

    assert second["title"] == "First (renamed)" and second["basis"] == "both"
    assert second["started_at"] == first["started_at"]
    assert second["sprint_label"] == "Sprint 9"
    assert second["notes"] == first["notes"]
    assert second["manual"] == 3 and second["automated"] == 3


def test_basis_subcommand_changes_one_field_and_logs_it(qa_track):
    run, record = qa_track
    run(*START, "--sprint-label", "Sprint 9")
    before = record("T-1")
    run("basis", "--ticket", "T-1", "--basis", "both")
    after = record("T-1")
    assert after["basis"] == "both"
    assert {k: v for k, v in after.items() if k not in ("basis", "notes")} == \
           {k: v for k, v in before.items() if k not in ("basis", "notes")}
    assert after["notes"][-1]["text"] == "basis ac -> both"


def test_basis_requires_an_existing_record(qa_track):
    run, _ = qa_track
    proc = run("basis", "--ticket", "NOPE-1", "--basis", "plan", expect_fail=True)
    assert "Run `start` first" in proc.stderr


def test_report_finds_records_by_sprint_label_after_basis_revision(qa_track):
    run, _ = qa_track
    run(*START, "--sprint-label", "Sprint 9")
    run("basis", "--ticket", "T-1", "--basis", "both")
    run("count", "--ticket", "T-1", "--manual", "2", "--automated", "1", "--reason", "one stays manual")
    out = run("report", "--sprint", "Sprint 9").stdout
    assert "T-1" in out and "both" in out and "one stays manual" in out


def test_status_lists_missing_counts(qa_track):
    run, _ = qa_track
    run(*START)
    assert "Missing counts for: T-1" in run("status").stdout
    run("count", "--ticket", "T-1", "--manual", "0", "--automated", "0")
    assert "complete" in run("status").stdout
