"""Human labels: pass/fail plus a one-sentence critique per run."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


AGENT_PREFIX = "agent:"


def is_agent(label: dict) -> bool:
    """A label written by an agent, not a person. The promotion rule in AUTONOMY.md and
    the LLM judge both rest on human verdicts; an agent grading its own run is evidence,
    never a substitute."""
    return str(label.get("labeler", "")).lower().startswith(AGENT_PREFIX)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unlabeled_runs(skill_dir: Path) -> list[dict]:
    runs = read_jsonl(skill_dir / "runs.jsonl")
    labeled = {l["run_id"] for l in read_jsonl(skill_dir / "labels.jsonl")}
    return [r for r in runs if r["run_id"] not in labeled and not r.get("dry_run")]


def append_label(skill_dir: Path, run_id: str, verdict: str, critique: str, labeler: str) -> dict:
    if verdict not in ("pass", "fail"):
        raise ValueError("verdict must be 'pass' or 'fail'")
    if not critique.strip():
        raise ValueError("critique is required — one sentence on why")
    label = {
        "run_id": run_id,
        "verdict": verdict,
        "critique": critique.strip(),
        "labeler": labeler,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    with (skill_dir / "labels.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(label, ensure_ascii=False) + "\n")
    return label


def summarize_run(run: dict, answer_chars: int = 1200) -> str:
    lines = [
        f"run      {run['run_id']}",
        f"case     {run['case']}",
        f"query    {run['query']}",
        f"cost     ${run.get('total_cost_usd') or 0:.3f}   turns {run.get('num_turns')}   {run.get('duration_ms', 0) // 1000}s",
        "",
        "expected behaviour:",
        *[f"  - {e}" for e in run.get("expected_behavior", [])],
        "",
        "changed files:",
        *([f"  {f}" for f in run["changed_files"]] or ["  (none)"]),
        "",
        "graders:",
        *[f"  {'PASS' if g['passed'] else 'FAIL'}  {g['name']}  {g['detail']}" for g in run["graders"]],
        "",
        "final answer:",
        run["answer"][:answer_chars] + ("…" if len(run["answer"]) > answer_chars else ""),
    ]
    return "\n".join(lines)
