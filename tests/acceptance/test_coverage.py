from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("coverage.feature")


def _spec(auto: int, partial: int, manual: int) -> str:
    rows = ["| Feature | Status | Test file | Notes |", "|---|---|---|---|"]
    rows += [f"| auto {i} | ✅ | tests/a{i}.spec.ts | — |" for i in range(auto)]
    rows += [f"| partial {i} | ⚠️ | tests/p{i}.spec.ts | — |" for i in range(partial)]
    rows += [f"| manual {i} | ❌ | — | — |" for i in range(manual)]
    return "\n".join(rows) + "\n"


@given(parsers.parse('a generated project with a "{domain}" spec of {auto:d} automated, {partial:d} partial and {manual:d} manual rows'),
       target_fixture="ctx")
def project_with_spec(render, run_script, domain, auto, partial, manual):
    proj = render()
    (proj / "specs").mkdir(exist_ok=True)
    (proj / "specs" / f"{domain}.md").write_text(_spec(auto, partial, manual), encoding="utf-8")
    return {"project": proj, "run": run_script, "last": None}


@when("I recompute coverage")
def recompute(ctx):
    ctx["last"] = ctx["run"](ctx["project"], "scripts/coverage_report.py")
    assert ctx["last"].returncode == 0, ctx["last"].stderr


@when(parsers.parse('the "{domain}" spec flips one manual row to automated'))
def flip_row(ctx, domain):
    p = ctx["project"] / "specs" / f"{domain}.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| ❌ |", "| ✅ |", 1), encoding="utf-8")


@when("I run the coverage check")
def run_check(ctx):
    ctx["last"] = ctx["run"](ctx["project"], "scripts/coverage_report.py", "--check")


@then(parsers.parse('COVERAGE.md reports {total:d} cases, {auto:d} automated and "{pct}"'))
def coverage_reports(ctx, total, auto, pct):
    assert f"| {total} | {auto} | {pct} |" in (ctx["project"] / "COVERAGE.md").read_text(encoding="utf-8")


@then(parsers.parse('the check fails mentioning "{text}"'))
def check_fails(ctx, text):
    assert ctx["last"].returncode == 1 and text in ctx["last"].stdout


@then("the check passes")
def check_passes(ctx):
    assert ctx["last"].returncode == 0, ctx["last"].stdout + ctx["last"].stderr
