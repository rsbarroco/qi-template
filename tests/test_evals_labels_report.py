"""Labels and report: the human half of the eval loop."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.labels import append_label, read_jsonl, summarize_run, unlabeled_runs
from evals.report import _pct, build_report, render_report


def _run(run_id="happy-path-1", case="happy-path", passed=True, cost=0.5, dry=False, answer="x" * 50) -> dict:
    return {
        "run_id": run_id, "case": case, "query": "q", "dry_run": dry,
        "expected_behavior": ["does the thing"], "changed_files": ["qa/dossiers/SHOP-101.md"],
        "graders": [{"name": "g1", "passed": passed, "detail": "d"}],
        "all_graders_passed": passed, "total_cost_usd": cost, "num_turns": 3, "duration_ms": 4500,
        "answer": answer,
    }


def _write_runs(skill_dir: Path, runs: list[dict]) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))


def test_read_jsonl_missing_file_is_empty(tmp_path):
    assert read_jsonl(tmp_path / "nope.jsonl") == []


def test_read_jsonl_skips_blank_lines(tmp_path):
    p = tmp_path / "a.jsonl"
    p.write_text('{"a": 1}\n\n{"a": 2}\n')
    assert [r["a"] for r in read_jsonl(p)] == [1, 2]


def test_unlabeled_excludes_dry_runs_and_already_labeled(tmp_path):
    _write_runs(tmp_path, [_run("r1"), _run("r2", dry=True), _run("r3")])
    append_label(tmp_path, "r1", "pass", "fine", "me")
    assert [r["run_id"] for r in unlabeled_runs(tmp_path)] == ["r3"]


@pytest.mark.parametrize("verdict, critique", [("maybe", "x"), ("pass", ""), ("fail", "   ")])
def test_append_label_rejects_bad_input(tmp_path, verdict, critique):
    with pytest.raises(ValueError):
        append_label(tmp_path, "r1", verdict, critique, "me")


def test_append_label_records_who_and_when(tmp_path):
    label = append_label(tmp_path, "r1", "fail", "Asserted without showing.", "rodrigo")
    assert label["labeler"] == "rodrigo" and label["at"].endswith("+00:00")
    assert read_jsonl(tmp_path / "labels.jsonl") == [label]


def test_summarize_run_shows_what_a_labeler_needs(tmp_path):
    text = summarize_run(_run(answer="A" * 2000), answer_chars=100)
    for needle in ("happy-path-1", "expected behaviour:", "does the thing", "qa/dossiers/SHOP-101.md", "PASS  g1", "$0.500", "4s"):
        assert needle in text
    assert text.endswith("A" * 100 + "…")          # truncated, and says so


def test_pct_is_none_when_there_is_no_denominator():
    assert _pct(0, 0) is None
    assert _pct(1, 3) == 33


def test_build_report_aggregates_per_case_and_ignores_dry_runs(tmp_path):
    _write_runs(tmp_path, [
        _run("a1", "alpha", passed=True, cost=1.0),
        _run("a2", "alpha", passed=False, cost=3.0),
        _run("b1", "beta", passed=True, cost=0.2),
        _run("dry", "beta", passed=True, dry=True),
    ])
    append_label(tmp_path, "a1", "fail", "showed nothing", "me")   # graders pass, human fails
    append_label(tmp_path, "a2", "fail", "wrong", "me")            # both fail -> agree
    report = build_report(tmp_path)
    assert report["total_runs"] == 3 and report["total_labeled"] == 2
    alpha = next(r for r in report["rows"] if r["case"] == "alpha")
    assert alpha == {"case": "alpha", "runs": 2, "graders": 50, "labeled": 2, "human": 0, "agree": 50,
                     "agent": None, "cost": 2.0}
    beta = next(r for r in report["rows"] if r["case"] == "beta")
    assert beta["labeled"] == 0 and beta["human"] is None and beta["agree"] is None


def test_judge_unlocks_at_thirty_labels(tmp_path):
    runs = [_run(f"r{i}") for i in range(30)]
    _write_runs(tmp_path, runs)
    for r in runs[:29]:
        append_label(tmp_path, r["run_id"], "pass", "ok", "me")
    assert build_report(tmp_path)["judge_unlocked"] is False
    append_label(tmp_path, "r29", "pass", "ok", "me")
    assert build_report(tmp_path)["judge_unlocked"] is True


def test_render_report_is_a_readable_table(tmp_path):
    _write_runs(tmp_path, [_run("a1", "alpha")])
    text = render_report(build_report(tmp_path))
    assert "Evals — " in text and "alpha" in text and "100%" in text and "—" in text
    assert "labeled 0/30" in text


# --- an agent label is not a human label ---------------------------------------------------

def test_agent_labels_are_reported_apart_and_never_unlock_the_judge(tmp_path):
    """The promotion rule and the LLM judge both rest on 30 *human* verdicts. A label
    written by the agent under review cannot stand in for one, so it is counted, shown
    and kept out of the human column."""
    _write_runs(tmp_path, [_run(f"r{i}") for i in range(31)])
    for i in range(31):
        append_label(tmp_path, f"r{i}", "pass", "looks right", "agent:claude-code")
    report = build_report(tmp_path)
    assert report["total_labeled"] == 0
    assert report["total_agent_labeled"] == 31
    assert report["judge_unlocked"] is False
    assert report["rows"][0]["human"] is None and report["rows"][0]["agree"] is None
    assert report["rows"][0]["agent"] == 100
    out = render_report(report)
    assert "31 agent label(s) shown separately; they never count as human" in out


def test_human_labels_still_count_when_agent_labels_exist(tmp_path):
    _write_runs(tmp_path, [_run("r1"), _run("r2", passed=False)])
    append_label(tmp_path, "r1", "pass", "right", "rsbarroco")
    append_label(tmp_path, "r2", "pass", "graders too strict", "agent:claude-code")
    report = build_report(tmp_path)
    assert report["total_labeled"] == 1 and report["total_agent_labeled"] == 1
    assert report["rows"][0]["human"] == 100 and report["rows"][0]["agree"] == 100
