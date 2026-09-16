"""Aggregate runs and labels per case."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from evals.labels import read_jsonl


def build_report(skill_dir: Path) -> dict:
    runs = [r for r in read_jsonl(skill_dir / "runs.jsonl") if not r.get("dry_run")]
    labels = {l["run_id"]: l for l in read_jsonl(skill_dir / "labels.jsonl")}

    per_case: dict[str, dict] = defaultdict(lambda: {
        "runs": 0, "graders_pass": 0, "labeled": 0, "human_pass": 0, "agree": 0, "cost": 0.0,
    })
    for r in runs:
        c = per_case[r["case"]]
        c["runs"] += 1
        c["graders_pass"] += int(r["all_graders_passed"])
        c["cost"] += float(r.get("total_cost_usd") or 0)
        label = labels.get(r["run_id"])
        if label:
            c["labeled"] += 1
            human = label["verdict"] == "pass"
            c["human_pass"] += int(human)
            c["agree"] += int(human == r["all_graders_passed"])

    rows = []
    for case, c in sorted(per_case.items()):
        rows.append({
            "case": case,
            "runs": c["runs"],
            "graders": _pct(c["graders_pass"], c["runs"]),
            "labeled": c["labeled"],
            "human": _pct(c["human_pass"], c["labeled"]),
            "agree": _pct(c["agree"], c["labeled"]),
            "cost": round(c["cost"] / c["runs"], 3) if c["runs"] else 0.0,
        })

    total_labeled = sum(c["labeled"] for c in per_case.values())
    return {
        "skill": skill_dir.name,
        "total_runs": len(runs),
        "total_labeled": total_labeled,
        "judge_unlocked": total_labeled >= 30,
        "rows": rows,
    }


def render_report(report: dict) -> str:
    head = f"{'case':<32} {'runs':>4} {'graders':>8} {'labeled':>7} {'human':>6} {'agree':>6} {'cost':>7}"
    lines = [f"Evals — {report['skill']}", "", head, "-" * len(head)]
    for r in report["rows"]:
        lines.append(
            f"{r['case']:<32} {r['runs']:>4} {_fmt(r['graders']):>8} {r['labeled']:>7} "
            f"{_fmt(r['human']):>6} {_fmt(r['agree']):>6} {('$' + str(r['cost'])):>7}"
        )
    lines.append("")
    lines.append(f"labeled {report['total_labeled']}/30 needed before an LLM judge is calibrated"
                 + (" — unlocked" if report["judge_unlocked"] else ""))
    return "\n".join(lines)


def _pct(n: int, d: int) -> float | None:
    return None if d == 0 else round(100 * n / d)


def _fmt(v: float | None) -> str:
    return "—" if v is None else f"{v:.0f}%"
