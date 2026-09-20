"""Every eval suite must be shaped so its numbers mean something.

The promotion rule in the generated AUTONOMY.md moves a task up a level only when the
skill has a suite with at least three cases, one of them a refusal case. These tests hold
that shape for every suite in the repo, and re-run the anti-vacuous gate — a case whose
graders all pass on an untouched fixture proves nothing — across all of them, not just
the first one anybody wrote.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals import runner
from evals.graders import GRADERS
from qi.config import Config

MIN_CASES = 3


def suites() -> list[str]:
    return sorted(
        p.name for p in runner.EVALS_DIR.iterdir()
        if p.is_dir() and (p / "cases").is_dir() and not p.name.startswith((".", "__"))
    )


def test_there_is_at_least_one_suite():
    assert suites()


@pytest.mark.parametrize("skill", suites())
def test_fixture_builds_a_real_config(skill):
    data = json.loads((runner.skill_dir(skill) / "fixture.json").read_text())
    cfg = Config(**data)                       # unknown keys would raise here
    assert cfg.project_name and cfg.project_slug


@pytest.mark.parametrize("skill", suites())
def test_suite_has_enough_cases_and_one_refusal(skill):
    cases = runner.load_cases(skill)
    assert len(cases) >= MIN_CASES, f"{skill}: {len(cases)} case(s), promotion needs {MIN_CASES}"
    assert any(c.get("kind") == "refusal" for c in cases), f"{skill}: no case marked kind=refusal"


@pytest.mark.parametrize("skill", suites())
def test_every_case_is_complete_and_uses_known_graders(skill):
    ids = set()
    for case in runner.load_cases(skill):
        where = f"{skill}/{case['id']}"
        assert case["id"] not in ids, f"duplicate case id {where}"
        ids.add(case["id"])
        assert case.get("query", "").strip(), f"{where}: empty query"
        assert case.get("expected_behavior"), f"{where}: no expected behaviour to label against"
        assert case.get("graders"), f"{where}: no graders"
        for grader in case["graders"]:
            assert grader["type"] in GRADERS, f"{where}: unknown grader {grader['type']!r}"
            assert grader.get("name"), f"{where}: a grader with no name is unreadable in a report"


@pytest.mark.parametrize("skill", suites())
def test_seed_paths_referenced_by_a_query_exist(skill):
    """A query that points the agent at a file the seed never ships tests nothing."""
    seed = runner.skill_dir(skill) / "seed"
    for case in runner.load_cases(skill):
        for token in case["query"].replace("(", " ").replace(")", " ").split():
            candidate = token.rstrip(".,")
            if "/" in candidate and candidate.endswith((".md", ".json", ".ts", ".py")):
                assert (seed / candidate).exists(), f"{skill}/{case['id']}: {candidate} not in seed/"


@pytest.mark.parametrize("skill", suites())
def test_dry_run_leaves_at_least_one_grader_failing_per_case(skill, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "RUNS_ROOT", tmp_path / "runs")
    for case in runner.load_cases(skill):
        rec = runner.run_case(skill, case, dry_run=True, model=None, max_budget_usd=1.0)
        assert rec["all_graders_passed"] is False, f"{skill}/{case['id']} passes without the agent doing anything"
