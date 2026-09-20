"""CLI: python -m evals run|label|report <skill>"""
from __future__ import annotations

import os
import sys

import typer
from rich.console import Console

from evals import labels as labels_mod
from evals import report as report_mod
from evals.runner import load_cases, run_case, skill_dir

app = typer.Typer(name="evals", help="Run, label and report skill evals.", add_completion=False)
console = Console()


def grader_marks(encoding: str | None) -> tuple[str, str]:
    """(pass, fail) marks the current console can actually print.

    The baseline is run on the QA engineer's own machine, and on Windows that console is
    cp1252, which has no U+2713 or U+2717. Printing them there raised UnicodeEncodeError
    out of rich and took the whole run down after the grading had already happened.
    """
    try:
        "✓✗".encode(encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        return "+", "x"
    return "✓", "✗"


@app.command()
def run(
    skill: str,
    case: str | None = typer.Option(None, "--case", help="Run only this case id."),
    runs: int = typer.Option(1, "--runs", min=1, help="Repetitions per case."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Render + seed + grade, no claude call."),
    model: str | None = typer.Option(None, "--model", help="Model for claude -p (default: your CLI default)."),
    max_budget_usd: float = typer.Option(2.0, "--max-budget-usd", help="Hard cap per run."),
) -> None:
    """Run every case (or one) for a skill and append results to runs.jsonl."""
    cases = load_cases(skill, case)
    total_cost = 0.0
    for c in cases:
        for i in range(runs):
            rec = run_case(skill, c, dry_run=dry_run, model=model,
                           max_budget_usd=max_budget_usd)
            total_cost += float(rec.get("total_cost_usd") or 0)
            status = "[green]PASS[/green]" if rec["all_graders_passed"] else "[red]FAIL[/red]"
            console.print(f"{status}  {rec['case']}  run {i + 1}/{runs}  "
                          f"${rec.get('total_cost_usd') or 0:.3f}  {len(rec['changed_files'])} files changed")
            ok_mark, bad_mark = grader_marks(getattr(sys.stdout, "encoding", None))
            for g in rec["graders"]:
                mark = ok_mark if g["passed"] else bad_mark
                console.print(f"       {mark} {g['name']}  [dim]{g['detail']}[/dim]")
            if rec.get("is_error") and not dry_run:
                console.print(f"       [yellow]claude exited {rec['exit_code']}[/yellow] {rec['stderr_tail'][-300:]}")
    console.print(f"\n[bold]total cost[/bold] ${total_cost:.2f} across {len(cases) * runs} run(s)")


@app.command()
def label(skill: str, labeler: str | None = typer.Option(None, "--labeler")) -> None:
    """Walk through unlabeled runs and record pass/fail + critique."""
    sd = skill_dir(skill)
    pending = labels_mod.unlabeled_runs(sd)
    if not pending:
        console.print("Nothing to label.")
        return
    who = labeler or os.environ.get("QA_NAME") or os.environ.get("USER") or "unknown"
    console.print(f"{len(pending)} unlabeled run(s). Verdict: p = pass, f = fail, s = skip, q = quit.\n")
    for run_rec in pending:
        console.rule(run_rec["run_id"])
        console.print(labels_mod.summarize_run(run_rec))
        choice = typer.prompt("verdict [p/f/s/q]").strip().lower()
        if choice == "q":
            break
        if choice == "s":
            continue
        if choice not in ("p", "f"):
            console.print("[yellow]skipped (unknown key)[/yellow]")
            continue
        critique = typer.prompt("critique (one sentence)")
        labels_mod.append_label(sd, run_rec["run_id"], "pass" if choice == "p" else "fail", critique, who)
        console.print("[green]recorded[/green]\n")


@app.command()
def report(skill: str) -> None:
    """Pass rates by case, human agreement, cost."""
    console.print(report_mod.render_report(report_mod.build_report(skill_dir(skill))))


if __name__ == "__main__":
    sys.exit(app())
