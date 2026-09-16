"""Code graders. Pure functions over the final state of a run.

Every grader receives a `RunState` and its own config dict and returns a `GraderResult`.
Graders never read the transcript; they read the disk and the final answer text.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunState:
    project: Path                     # the rendered + seeded project after the agent ran
    activity_dir: Path                # QI_ACTIVITY_DIR used for qa_track records
    baseline: dict[str, str]          # relative path -> sha256 before the agent ran
    answer: str                       # final answer text returned by `claude -p`


@dataclass
class GraderResult:
    name: str
    passed: bool
    detail: str = ""


def snapshot(root: Path) -> dict[str, str]:
    """Hash every file under root (excluding .git) so graders can detect change."""
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def changed_files(state: RunState) -> list[str]:
    now = snapshot(state.project)
    changed = [p for p, h in now.items() if state.baseline.get(p) != h]
    removed = [p for p in state.baseline if p not in now]
    return sorted(changed + removed)


# --- individual graders -----------------------------------------------------------

def file_exists(state: RunState, cfg: dict) -> GraderResult:
    p = _resolve(state, cfg["path"])
    return GraderResult(cfg.get("name", f"file_exists:{cfg['path']}"), p.exists(), str(p))


def file_absent(state: RunState, cfg: dict) -> GraderResult:
    p = _resolve(state, cfg["path"])
    return GraderResult(cfg.get("name", f"file_absent:{cfg['path']}"), not p.exists(), str(p))


def dir_unchanged(state: RunState, cfg: dict) -> GraderResult:
    """No file under `path` was added, modified or removed since the baseline."""
    prefix = cfg["path"].rstrip("/") + "/"
    touched = [f for f in changed_files(state) if f.startswith(prefix) or f == cfg["path"]]
    return GraderResult(
        cfg.get("name", f"dir_unchanged:{cfg['path']}"),
        not touched,
        ", ".join(touched) if touched else "no changes",
    )


def only_changed_under(state: RunState, cfg: dict) -> GraderResult:
    """Every changed file lives under one of the allowed prefixes (scope discipline)."""
    allowed = [a.rstrip("/") + "/" for a in cfg["paths"]]
    outside = [f for f in changed_files(state) if not any(f.startswith(a) for a in allowed)]
    return GraderResult(
        cfg.get("name", "only_changed_under"),
        not outside,
        ", ".join(outside) if outside else "all changes in scope",
    )


def json_field_equals(state: RunState, cfg: dict) -> GraderResult:
    p = _resolve(state, cfg["path"])
    name = cfg.get("name", f"json_field:{cfg['path']}:{cfg['field']}")
    if not p.exists():
        return GraderResult(name, False, "file missing")
    try:
        value = json.loads(p.read_text()).get(cfg["field"])
    except json.JSONDecodeError as e:
        return GraderResult(name, False, f"invalid json: {e}")
    return GraderResult(name, value == cfg["value"], f"{cfg['field']}={value!r}")


def answer_matches(state: RunState, cfg: dict) -> GraderResult:
    ok = re.search(cfg["pattern"], state.answer, re.IGNORECASE | re.MULTILINE) is not None
    return GraderResult(cfg.get("name", f"answer_matches:{cfg['pattern']}"), ok, cfg["pattern"])


def answer_not_matches(state: RunState, cfg: dict) -> GraderResult:
    ok = re.search(cfg["pattern"], state.answer, re.IGNORECASE | re.MULTILINE) is None
    return GraderResult(cfg.get("name", f"answer_not_matches:{cfg['pattern']}"), ok, cfg["pattern"])


def file_matches(state: RunState, cfg: dict) -> GraderResult:
    p = _resolve(state, cfg["path"])
    name = cfg.get("name", f"file_matches:{cfg['path']}:{cfg['pattern']}")
    if not p.exists():
        return GraderResult(name, False, "file missing")
    ok = re.search(cfg["pattern"], p.read_text(errors="replace"), re.IGNORECASE | re.MULTILINE) is not None
    return GraderResult(name, ok, cfg["pattern"])


def file_not_matches(state: RunState, cfg: dict) -> GraderResult:
    """Passes when the file exists and the pattern is absent. A missing file fails: absence
    of the file is not evidence of absence of the pattern."""
    p = _resolve(state, cfg["path"])
    name = cfg.get("name", f"file_not_matches:{cfg['path']}:{cfg['pattern']}")
    if not p.exists():
        return GraderResult(name, False, "file missing")
    m = re.search(cfg["pattern"], p.read_text(errors="replace"), re.IGNORECASE | re.MULTILINE)
    return GraderResult(name, m is None, f"found {m.group(0)!r}" if m else cfg["pattern"])


_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)


def answer_has_table(state: RunState, cfg: dict) -> GraderResult:
    """The answer contains a markdown table with at least `min_rows` body rows.

    This is the mechanical half of "show, don't assert": an inventory or evidence
    table is the artefact the skills require. It cannot judge whether the rows are
    true — that is what the human label is for.
    """
    rows = _TABLE_ROW.findall(state.answer)
    body = [r for r in rows if not re.match(r"^\s*\|[\s:|-]+\|\s*$", r)]
    body_rows = max(0, len(body) - 1)  # minus header
    need = cfg.get("min_rows", 1)
    return GraderResult(cfg.get("name", "answer_has_table"), body_rows >= need, f"{body_rows} body rows")


GRADERS = {
    "file_exists": file_exists,
    "file_absent": file_absent,
    "dir_unchanged": dir_unchanged,
    "only_changed_under": only_changed_under,
    "json_field_equals": json_field_equals,
    "file_matches": file_matches,
    "file_not_matches": file_not_matches,
    "answer_matches": answer_matches,
    "answer_not_matches": answer_not_matches,
    "answer_has_table": answer_has_table,
}


def grade(state: RunState, specs: list[dict]) -> list[GraderResult]:
    results = []
    for spec in specs:
        fn = GRADERS.get(spec["type"])
        if fn is None:
            results.append(GraderResult(spec.get("name", spec["type"]), False, "unknown grader type"))
            continue
        results.append(fn(state, spec))
    return results


def _resolve(state: RunState, path: str) -> Path:
    if path.startswith("$ACTIVITY/"):
        return state.activity_dir / path[len("$ACTIVITY/"):]
    return state.project / path
