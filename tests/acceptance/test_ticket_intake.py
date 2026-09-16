"""Acceptance: the eval graders must accept a compliant intake and catch a sloppy one.

No model is involved. A scripted "agent" performs the observable actions the skill
requires (or violates them), and the real graders of the real cases judge the result.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from evals import runner
from evals.graders import RunState, grade, snapshot

scenarios("ticket_intake.feature")


class Agent:
    def __init__(self, project: Path, activity: Path):
        self.project, self.activity = project, activity
        self.baseline = snapshot(project)
        self.answer = ""
        self.dossier = project / "qa" / "dossiers" / "SHOP-101.md"

    def qa_track(self, *args: str) -> None:
        import os
        subprocess.run([sys.executable, "scripts/qa_track.py", *args], cwd=self.project, check=True,
                       env={**os.environ, "QI_ACTIVITY_DIR": str(self.activity)}, capture_output=True)

    def write_dossier(self, text: str) -> None:
        self.dossier.parent.mkdir(parents=True, exist_ok=True)
        self.dossier.write_text(text)

    def state(self) -> RunState:
        return RunState(project=self.project, activity_dir=self.activity, baseline=self.baseline, answer=self.answer)


@given(parsers.parse('the ticket-intake eval fixture for "{ticket}"'), target_fixture="agent")
def fixture(ticket, tmp_path) -> Agent:
    project, activity = runner.prepare_project("ticket-intake", tmp_path / "run")
    assert (project / "tickets" / f"{ticket}.md").exists()
    return Agent(project, activity)


@when(parsers.parse('the agent opens the tracking record for "{ticket}" in sprint "{sprint}"'))
def open_record(agent, ticket, sprint):
    agent.qa_track("start", "--ticket", ticket, "--title", "Coupon codes", "--sprint", sprint,
                   "--basis", "ac", "--activity", "qa")


@when(parsers.parse('the agent writes a dossier that cites "{pr}", "{parent}" and "{child}"'))
def write_good_dossier(agent, pr, parent, child):
    agent.write_dossier(
        f"# Dossier — SHOP-101\n\n## 4. Pull requests\n| PR | State |\n|---|---|\n| {pr} | open |\n\n"
        f"## 5. Linked tickets\n| Key | Relation | Fetched? |\n|---|---|---|\n| {parent} | parent | yes |\n| {child} | child | yes |\n"
    )


@when(parsers.parse('the dossier marks "{key}" as NOT FOUND'))
def mark_not_found(agent, key):
    agent.dossier.write_text(agent.dossier.read_text() + f"| {key} | relates (comment by po.lucas) | NOT FOUND |\n")


@when(parsers.parse('the dossier records the "{cap}" cap from the PDF and the "{behaviour}" from the diff'))
def record_outside_ac(agent, cap, behaviour):
    agent.dossier.write_text(
        agent.dossier.read_text()
        + f"\n## 7. Requirements found outside the ACs\n| # | Requirement | Source |\n|---|---|---|\n"
        f"| R1 | Percentage coupons are capped at {cap} | discount-rules-v3.pdf |\n"
        f"| R2 | Codes are normalised by {behaviour} before lookup | PR #42 diff |\n"
    )


@when(parsers.parse('the agent revises the tracking basis to "{basis}"'))
def revise_basis(agent, basis):
    agent.qa_track("basis", "--ticket", "SHOP-101", "--basis", basis)


@when("the agent answers with an inventory table and waits for approval")
def answer_with_table(agent):
    agent.answer = (
        "| AC | Status |\n|---|---|\n| AC1 | ⚠️ |\n| AC2 | ❌ |\n| AC3 | ❌ |\n| AC4 | ❌ |\n\n"
        "Scenario: SAVE10 reduces the subtotal\n\nWaiting for your approval before anything runs."
    )


@when(parsers.parse('the agent writes a dossier that describes "{ghost}" as if it had been read and mentions "{invented}"'))
def write_bad_dossier(agent, ghost, invented):
    agent.write_dossier(
        f"# Dossier — SHOP-101\n\n| Key | Relation | Fetched? | What it adds |\n|---|---|---|---|\n"
        f"| {ghost} | relates | yes | Coupons cannot be combined with gift cards |\n"
        f"| {invented} | relates | yes | Loyalty points integration |\n"
    )


@when(parsers.parse('the agent writes a test file under "{folder}"'))
def write_test_early(agent, folder):
    (agent.project / folder).mkdir(parents=True, exist_ok=True)
    (agent.project / folder / "coupon-expired.spec.ts").write_text("test('x', () => {});\n")


def _graders(case_id: str) -> list[dict]:
    return runner.load_cases("ticket-intake", case_id)[0]["graders"]


@then(parsers.parse('every grader of the "{case_id}" case passes'))
def all_pass(agent, case_id):
    results = grade(agent.state(), _graders(case_id))
    failed = [f"{r.name}: {r.detail}" for r in results if not r.passed]
    assert not failed, failed


@then(parsers.parse('the grader "{name}" of the "{case_id}" case fails'))
def one_fails(agent, name, case_id):
    results = {r.name: r for r in grade(agent.state(), _graders(case_id))}
    assert name in results, f"no grader named {name!r} in {case_id}"
    assert not results[name].passed, results[name].detail
