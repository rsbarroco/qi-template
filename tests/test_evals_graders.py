"""Graders must be able to fail. Each test proves both the red and the green side."""
import json
from pathlib import Path

from evals.graders import RunState, grade, snapshot


def _state(tmp_path: Path, answer: str = "") -> RunState:
    project = tmp_path / "project"
    activity = tmp_path / "activity"
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "a.spec.ts").write_text("test")
    (project / "COVERAGE.md").write_text("| 0 | 0 | 0% |")
    activity.mkdir()
    return RunState(project=project, activity_dir=activity, baseline=snapshot(project), answer=answer)


def test_file_exists_resolves_activity_prefix(tmp_path):
    st = _state(tmp_path)
    spec = [{"type": "file_exists", "path": "$ACTIVITY/SHOP-1.json"}]
    assert grade(st, spec)[0].passed is False
    (st.activity_dir / "SHOP-1.json").write_text("{}")
    assert grade(st, spec)[0].passed is True


def test_json_field_equals(tmp_path):
    st = _state(tmp_path)
    (st.activity_dir / "SHOP-1.json").write_text(json.dumps({"sprint": "26-09"}))
    spec = [{"type": "json_field_equals", "path": "$ACTIVITY/SHOP-1.json", "field": "sprint", "value": "26-09"}]
    assert grade(st, spec)[0].passed
    spec[0]["value"] = "26-10"
    assert not grade(st, spec)[0].passed


def test_dir_unchanged_detects_added_modified_and_removed(tmp_path):
    st = _state(tmp_path)
    spec = [{"type": "dir_unchanged", "path": "tests"}]
    assert grade(st, spec)[0].passed
    (st.project / "tests" / "b.spec.ts").write_text("new")
    r = grade(st, spec)[0]
    assert not r.passed and "tests/b.spec.ts" in r.detail
    (st.project / "tests" / "b.spec.ts").unlink()
    (st.project / "tests" / "a.spec.ts").write_text("changed")
    assert not grade(st, spec)[0].passed
    (st.project / "tests" / "a.spec.ts").write_text("test")
    (st.project / "tests" / "a.spec.ts").unlink()
    assert not grade(st, spec)[0].passed


def test_dir_unchanged_works_for_a_single_file(tmp_path):
    st = _state(tmp_path)
    spec = [{"type": "dir_unchanged", "path": "COVERAGE.md"}]
    assert grade(st, spec)[0].passed
    (st.project / "COVERAGE.md").write_text("| 1 | 1 | 100% |")
    assert not grade(st, spec)[0].passed


def test_only_changed_under_flags_out_of_scope_edits(tmp_path):
    st = _state(tmp_path)
    (st.project / "specs").mkdir()
    (st.project / "specs" / "x.md").write_text("x")
    spec = [{"type": "only_changed_under", "paths": ["specs"]}]
    assert grade(st, spec)[0].passed
    (st.project / "tests" / "a.spec.ts").write_text("oops")
    r = grade(st, spec)[0]
    assert not r.passed and "tests/a.spec.ts" in r.detail


def test_answer_matches_and_not_matches(tmp_path):
    st = _state(tmp_path, answer="Scenario: apply coupon\nWaiting for approval.")
    assert grade(st, [{"type": "answer_matches", "pattern": "^\\s*Scenario\\b"}])[0].passed
    assert grade(st, [{"type": "answer_matches", "pattern": "approv"}])[0].passed
    assert not grade(st, [{"type": "answer_not_matches", "pattern": "approv"}])[0].passed
    assert grade(st, [{"type": "answer_not_matches", "pattern": "AC[1-9]:"}])[0].passed


def test_answer_has_table_counts_body_rows_only(tmp_path):
    table = "| AC | Status |\n|---|---|\n| AC1 | ❌ |\n| AC2 | ❌ |\n"
    st = _state(tmp_path, answer="Inventory:\n" + table)
    assert grade(st, [{"type": "answer_has_table", "min_rows": 2}])[0].passed
    assert not grade(st, [{"type": "answer_has_table", "min_rows": 3}])[0].passed
    st_prose = _state(tmp_path / "prose", answer="I checked everything and it is all covered.")
    assert not grade(st_prose, [{"type": "answer_has_table"}])[0].passed


def test_unknown_grader_type_fails_loudly(tmp_path):
    st = _state(tmp_path)
    r = grade(st, [{"type": "does_not_exist"}])[0]
    assert not r.passed and "unknown" in r.detail


def test_file_matches_and_not_matches_require_the_file(tmp_path):
    st = _state(tmp_path)
    spec_yes = [{"type": "file_matches", "path": "qa/dossiers/X.md", "pattern": "NOT FOUND"}]
    spec_no = [{"type": "file_not_matches", "path": "qa/dossiers/X.md", "pattern": "SHOP-(?!101\\b)\\d+"}]
    # missing file fails both: absence of the file is not evidence of anything
    assert not grade(st, spec_yes)[0].passed
    assert not grade(st, spec_no)[0].passed
    (st.project / "qa" / "dossiers").mkdir(parents=True)
    (st.project / "qa" / "dossiers" / "X.md").write_text("SHOP-101 ok\nSHOP-205 NOT FOUND\n")
    assert grade(st, spec_yes)[0].passed
    r = grade(st, spec_no)[0]
    assert not r.passed and "SHOP-205" in r.detail
    (st.project / "qa" / "dossiers" / "X.md").write_text("SHOP-101 only\n")
    assert grade(st, spec_no)[0].passed
