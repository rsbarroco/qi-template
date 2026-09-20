"""Runner tests use a fake `claude` binary so no tokens are spent."""
import json
import os
import stat
import sys
from pathlib import Path

import pytest

from evals import runner
from evals.labels import append_label, unlabeled_runs
from evals.report import build_report

FAKE_CLAUDE = r'''#!/usr/bin/env python3
"""Fake claude -p: opens the tracking record like the skill says, prints a JSON result."""
import json, os, subprocess, sys
args = sys.argv[1:]
query = args[args.index("-p") + 1]
ticket = next(w for w in query.replace("(", " ").replace(")", " ").split() if w.startswith("SHOP-")).rstrip(".,")
subprocess.run([sys.executable, "scripts/qa_track.py", "start", "--ticket", ticket, "--title", "fake",
                "--sprint", "26-09", "--basis", "ac", "--activity", "qa"], check=True)
os.makedirs("qa/dossiers", exist_ok=True)
with open(f"qa/dossiers/{ticket}.md", "w", encoding="utf-8") as fh:
    fh.write(f"# Dossier — {ticket}\n\n| Item | Found in | Followed? |\n|---|---|---|\n| PR #42 | ticket | yes |\n")
answer = "| AC | Status |\n|---|---|\n| AC1 | ❌ |\n| AC2 | ❌ |\n\nScenario: draft\n\nWaiting for approval."
print(json.dumps({"type": "result", "result": answer, "total_cost_usd": 0.42,
                  "duration_ms": 1234, "num_turns": 7, "session_id": "fake", "is_error": False}))
'''


@pytest.fixture
def isolated_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "RUNS_ROOT", tmp_path / "runs")
    # keep runs.jsonl out of the repo: point skill_dir at a copy of the real skill folder
    import shutil
    skill_copy = tmp_path / "evals" / "ticket-intake"
    shutil.copytree(runner.EVALS_DIR / "ticket-intake", skill_copy)
    for f in ("runs.jsonl", "labels.jsonl"):
        (skill_copy / f).unlink(missing_ok=True)
    monkeypatch.setattr(runner, "EVALS_DIR", tmp_path / "evals")
    return skill_copy


def install_fake_claude(directory: Path) -> Path:
    """Write the fake `claude` into `directory` and return something exec'able here.

    POSIX runs the script itself, on the shebang. Windows cannot exec an extensionless
    script at all, so it gets a `.cmd` shim next to the source — the same shape as the
    real CLI, which installs as `claude.CMD`.
    """
    script = directory / "fake-claude.py"
    script.write_text(FAKE_CLAUDE, encoding="utf-8")
    if os.name != "nt":
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return script
    shim = directory / "fake-claude.cmd"
    shim.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    return shim


@pytest.fixture
def fake_claude(tmp_path, monkeypatch):
    bin_path = install_fake_claude(tmp_path)
    monkeypatch.setenv("QI_EVAL_CLAUDE_BIN", str(bin_path))
    return bin_path


def test_prepare_project_renders_fixture_and_seeds(isolated_runs, tmp_path):
    project, activity = runner.prepare_project("ticket-intake", tmp_path / "r1")
    assert (project / "CLAUDE.md").exists()
    assert (project / ".claude" / "skills" / "ticket-intake" / "SKILL.md").exists()
    assert (project / "tickets" / "SHOP-101.md").exists()
    assert (project / "specs" / "cart.md").exists()
    assert (project / ".git").is_dir()
    assert activity.is_dir()


def test_dry_run_grades_untouched_fixture_and_at_least_one_grader_fails_per_case(isolated_runs):
    """A case whose graders all pass on the untouched fixture proves nothing."""
    for case in runner.load_cases("ticket-intake"):
        rec = runner.run_case("ticket-intake", case, dry_run=True, model=None, max_budget_usd=1.0)
        assert rec["dry_run"] is True
        assert rec["all_graders_passed"] is False, case["id"]


def test_run_case_with_fake_claude_records_cost_and_grades(isolated_runs, fake_claude):
    case = runner.load_cases("ticket-intake", "happy-path")[0]
    rec = runner.run_case("ticket-intake", case, dry_run=False, model=None, max_budget_usd=1.0)
    assert rec["total_cost_usd"] == 0.42
    assert rec["num_turns"] == 7
    names = {g["name"]: g["passed"] for g in rec["graders"]}
    assert names["tracking record opened"] is True
    assert names["sprint recorded"] is True
    assert names["gherkin draft present"] is True
    assert names["inventory shown as table"] is True
    assert names["no tests written before approval"] is True
    assert rec["all_graders_passed"] is True
    # persisted
    lines = (isolated_runs / "runs.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["run_id"] == rec["run_id"]
    assert (Path(rec["run_dir"]) / "run.json").exists()


def test_activity_dir_is_isolated_from_the_real_home(isolated_runs, fake_claude):
    case = runner.load_cases("ticket-intake", "happy-path")[0]
    rec = runner.run_case("ticket-intake", case, dry_run=False, model=None, max_budget_usd=1.0)
    assert (Path(rec["run_dir"]) / "home" / "qi-activity" / "SHOP-101.json").exists()
    assert not (Path.home() / ".config" / "qi-activity" / "SHOP-101.json").exists()


def test_labels_and_report(isolated_runs, fake_claude):
    case = runner.load_cases("ticket-intake", "happy-path")[0]
    rec = runner.run_case("ticket-intake", case, dry_run=False, model=None, max_budget_usd=1.0)
    assert [r["run_id"] for r in unlabeled_runs(isolated_runs)] == [rec["run_id"]]

    with pytest.raises(ValueError):
        append_label(isolated_runs, rec["run_id"], "pass", "", "tester")
    append_label(isolated_runs, rec["run_id"], "fail", "Asserted coverage without showing the grep.", "tester")
    assert unlabeled_runs(isolated_runs) == []

    report = build_report(isolated_runs)
    row = next(r for r in report["rows"] if r["case"] == "happy-path")
    assert row["runs"] == 1 and row["graders"] == 100
    assert row["labeled"] == 1 and row["human"] == 0
    assert row["agree"] == 0          # graders said pass, human said fail — the gap we want to see
    assert report["judge_unlocked"] is False
    assert row["cost"] == 0.42
