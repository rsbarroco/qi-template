from __future__ import annotations

import json
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("qa_track.feature")


@given("a generated project", target_fixture="ctx")
def project(render, run_script, tmp_path, monkeypatch):
    activity = tmp_path / "activity"
    monkeypatch.setenv("QI_ACTIVITY_DIR", str(activity))
    monkeypatch.setenv("QA_NAME", "rodrigo")
    proj = render()

    class Ctx:
        def track(self, *args, expect_fail=False):
            proc = run_script(proj, "scripts/qa_track.py", *args)
            assert (proc.returncode != 0) is expect_fail, proc.stdout + proc.stderr
            self.last = proc
            return proc

        def record(self, ticket):
            return json.loads((activity / f"{ticket}.json").read_text())

    return Ctx()


@when(parsers.parse('I start tracking "{t}" in sprint "{s}" labelled "{label}" with basis "{basis}"'))
def start(ctx, t, s, label, basis):
    ctx.track("start", "--ticket", t, "--title", "Coupon codes", "--sprint", s, "--sprint-label", label,
              "--basis", basis, "--activity", "qa,automation")
    ctx.started_at = ctx.record(t)["started_at"]


@when(parsers.parse('I revise the basis of "{t}" to "{basis}"'))
def revise(ctx, t, basis):
    ctx.track("basis", "--ticket", t, "--basis", basis)


@when(parsers.parse('I add the note "{text}" to "{t}"'))
def note(ctx, text, t):
    ctx.track("note", "--ticket", t, text)


@when(parsers.parse('I count {m:d} manual and {a:d} automated cases for "{t}" because "{reason}"'))
def count(ctx, m, a, t, reason):
    ctx.track("count", "--ticket", t, "--manual", str(m), "--automated", str(a), "--reason", reason)


@when(parsers.parse('I try to count {m:d} manual and {a:d} automated cases for "{t}" without a reason'))
def count_no_reason(ctx, m, a, t):
    ctx.track("count", "--ticket", t, "--manual", str(m), "--automated", str(a), expect_fail=True)


@then(parsers.parse('the record for "{t}" has basis "{basis}" and label "{label}"'))
def record_has(ctx, t, basis, label):
    r = ctx.record(t)
    assert r["basis"] == basis and r["sprint_label"] == label


@then("the record keeps its original start time")
def keeps_start(ctx):
    assert ctx.record("SHOP-101")["started_at"] == ctx.started_at


@then(parsers.parse('the sprint report for "{label}" lists "{t}" with "{m}" manual and "{a}" automated'))
def report_lists(ctx, label, t, m, a):
    out = ctx.track("report", "--sprint", label).stdout
    row = next(line for line in out.splitlines() if line.startswith(t))
    assert f" {m} " in row and f" {a} " in row


@then("the count is refused")
def refused(ctx):
    assert "reason" in (ctx.last.stderr + ctx.last.stdout).lower()


@then(parsers.parse('the status report says "{t}" is missing counts'))
def status_missing(ctx, t):
    assert f"Missing counts for: {t}" in ctx.track("status").stdout
