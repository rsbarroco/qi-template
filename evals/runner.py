"""Render a fixture project, run `claude -p`, grade the final state, record the run."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from qi.config import Config
from qi.generator import generate

from evals.graders import RunState, changed_files, grade, snapshot

EVALS_DIR = Path(__file__).resolve().parent
RUNS_ROOT = EVALS_DIR / ".runs"

DEFAULT_ALLOWED_TOOLS = [
    "Read", "Glob", "Grep", "Edit", "Write",
    "Bash(python*)", "Bash(python3*)", "Bash(git *)", "Bash(ls*)", "Bash(cat*)",
]


def skill_dir(skill: str) -> Path:
    d = EVALS_DIR / skill
    if not d.is_dir():
        raise SystemExit(f"[evals] no such skill folder: {d}")
    return d


def load_cases(skill: str, only: str | None = None) -> list[dict]:
    cases = []
    for p in sorted((skill_dir(skill) / "cases").glob("*.json")):
        case = json.loads(p.read_text(encoding="utf-8"))
        case.setdefault("id", p.stem)
        if only and case["id"] != only:
            continue
        cases.append(case)
    if only and not cases:
        raise SystemExit(f"[evals] no case named {only!r} for {skill}")
    return cases


def load_fixture_config(skill: str) -> Config:
    data = json.loads((skill_dir(skill) / "fixture.json").read_text(encoding="utf-8"))
    return Config(**data)


def prepare_project(skill: str, run_dir: Path) -> tuple[Path, Path]:
    """Render the fixture with the real generator, copy seeds, commit a baseline."""
    project = run_dir / "project"
    activity = run_dir / "home" / "qi-activity"
    project.mkdir(parents=True)
    activity.mkdir(parents=True)

    generate(load_fixture_config(skill), project)

    seed = skill_dir(skill) / "seed"
    if seed.is_dir():
        shutil.copytree(seed, project, dirs_exist_ok=True)

    # Records the skill reads out of QI_ACTIVITY_DIR, which lives outside the project and
    # so cannot come from seed/. A JSON file on disk is a fixture the runner can honestly
    # provide, unlike a browser or a database (docs/decisions/0001).
    seed_activity = skill_dir(skill) / "seed-activity"
    if seed_activity.is_dir():
        shutil.copytree(seed_activity, activity, dirs_exist_ok=True)

    _git(project, "init", "-q")
    _git(project, "add", "-A")
    _git(project, "-c", "user.name=qi-evals", "-c", "user.email=evals@qi.local",
         "commit", "-q", "-m", "baseline fixture")
    return project, activity


def resolve_claude_bin(name: str) -> str:
    """The command to exec for `name`, resolved through PATH and PATHEXT.

    On Windows the Claude CLI installs as `claude.CMD`, and subprocess without a shell
    only ever appends `.exe`, so the bare name raises FileNotFoundError. The baseline is
    run on the QA engineer's Windows machine, so unresolved means no evals at all there.
    Falls back to `name` untouched so the error still names what was asked for.
    """
    return shutil.which(name) or name


def run_claude(project: Path, activity: Path, query: str, *, model: str | None,
               max_budget_usd: float, allowed_tools: list[str]) -> dict:
    """Invoke the Claude Code CLI headlessly. Uses whatever login the CLI already has."""
    claude_bin = resolve_claude_bin(os.environ.get("QI_EVAL_CLAUDE_BIN", "claude"))
    cmd = [
        claude_bin, "-p", query,
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--max-budget-usd", str(max_budget_usd),
        "--allowedTools", *allowed_tools,
    ]
    if model:
        cmd += ["--model", model]

    env = {**os.environ, "QI_ACTIVITY_DIR": str(activity)}
    started = time.time()
    proc = subprocess.run(cmd, cwd=project, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    wall = time.time() - started

    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    return {
        "exit_code": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
        "answer": payload.get("result", "") if isinstance(payload, dict) else "",
        "total_cost_usd": payload.get("total_cost_usd") if isinstance(payload, dict) else None,
        "duration_ms": payload.get("duration_ms", int(wall * 1000)) if isinstance(payload, dict) else int(wall * 1000),
        "num_turns": payload.get("num_turns") if isinstance(payload, dict) else None,
        "session_id": payload.get("session_id") if isinstance(payload, dict) else None,
        "is_error": payload.get("is_error", proc.returncode != 0) if isinstance(payload, dict) else True,
    }


def run_case(skill: str, case: dict, *, dry_run: bool, model: str | None,
             max_budget_usd: float) -> dict:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"{case['id']}-{stamp}"
    run_dir = RUNS_ROOT / skill / run_id
    project, activity = prepare_project(skill, run_dir)
    baseline = snapshot(project)

    if dry_run:
        outcome = {"exit_code": 0, "stderr_tail": "", "answer": "", "total_cost_usd": 0.0,
                   "duration_ms": 0, "num_turns": 0, "session_id": None, "is_error": False}
    else:
        outcome = run_claude(
            project, activity, case["query"], model=model, max_budget_usd=max_budget_usd,
            allowed_tools=case.get("allowed_tools", DEFAULT_ALLOWED_TOOLS),
        )

    state = RunState(project=project, activity_dir=activity, baseline=baseline, answer=outcome["answer"])
    results = grade(state, case["graders"])

    record = {
        "run_id": run_id,
        "skill": skill,
        "case": case["id"],
        "dry_run": dry_run,
        "model": model,
        "at": datetime.now(timezone.utc).isoformat(),
        "query": case["query"],
        "expected_behavior": case.get("expected_behavior", []),
        "changed_files": changed_files(state),
        "graders": [asdict(r) for r in results],
        "all_graders_passed": all(r.passed for r in results),
        **{k: v for k, v in outcome.items() if k != "answer"},
        "answer": outcome["answer"],
        "run_dir": str(run_dir),
    }
    (run_dir / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not dry_run:  # dry runs prove graders can fail; they are not data about the agent
        with (skill_dir(skill) / "runs.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)
