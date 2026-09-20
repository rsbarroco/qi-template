"""The generated coverage_report.py must count spec rows correctly and never drift."""
from __future__ import annotations

import re

SPEC = """# Checkout — Test Spec

| Feature | Status | Test file | Notes |
|---|---|---|---|
| Place order | ✅ | tests/checkout/place.spec.ts | SHOP-080 |
| Address validation | ✅ | tests/checkout/address.spec.ts | SHOP-083 |
| Coupon empty code | ⚠️ | tests/checkout/coupon.spec.ts | missing branch |
| Coupon expired | ❌ | — | SHOP-101 AC3 |
"""


def _seed(project, spec_text=SPEC, name="checkout.md"):
    (project / "specs").mkdir(exist_ok=True)
    (project / "specs" / name).write_text(spec_text)


def test_counts_automated_partial_and_manual_rows(render, run_script):
    project = render()
    _seed(project)
    out = run_script(project, "scripts/coverage_report.py")
    assert out.returncode == 0, out.stderr
    assert "Total cases : 4" in out.stdout
    assert "Automated   : 2 (50%)" in out.stdout
    assert "Partial     : 1" in out.stdout
    assert "Manual only : 1" in out.stdout


def test_header_and_separator_rows_are_not_counted(render, run_script):
    project = render()
    _seed(project, "| Feature | Status | Test | Notes |\n|---|---|---|---|\n")
    out = run_script(project, "scripts/coverage_report.py")
    assert "Total cases : 0" in out.stdout


def test_summary_row_in_coverage_md_is_rewritten(render, run_script):
    project = render()
    _seed(project)
    before = (project / "COVERAGE.md").read_text()
    assert "| 0 | 0 | 0% |" in before                      # the seed row the regex targets
    run_script(project, "scripts/coverage_report.py")
    after = (project / "COVERAGE.md").read_text()
    assert "| 4 | 2 | 50% |" in after
    assert "| 0 | 0 | 0% |" not in after
    # only the summary row changed
    assert re.sub(r"\| \d+ \| \d+ \| \d+% \|", "X", before) == re.sub(r"\| \d+ \| \d+ \| \d+% \|", "X", after)


def test_check_fails_while_manual_rows_remain(render, run_script):
    project = render()
    _seed(project)
    out = run_script(project, "scripts/coverage_report.py", "--check")
    assert out.returncode == 1
    assert "1 manual-only cases remain" in out.stdout


def test_check_passes_when_nothing_is_manual_only(render, run_script):
    project = render()
    _seed(project, SPEC.replace("| Coupon expired | ❌ |", "| Coupon expired | ✅ |"))
    out = run_script(project, "scripts/coverage_report.py", "--check")
    assert out.returncode == 0, out.stdout


def test_multiple_domains_are_summed_and_listed(render, run_script):
    project = render()
    _seed(project)
    _seed(project, "| F | Status |\n|---|---|\n| A | ✅ |\n| B | ✅ |\n", name="cart.md")
    out = run_script(project, "scripts/coverage_report.py")
    assert "Total cases : 6" in out.stdout
    assert re.search(r"cart\s+2\s+0\s+0", out.stdout)
    assert re.search(r"checkout\s+2\s+1\s+1", out.stdout)


def test_no_specs_dir_reports_zero_without_crashing(render, run_script):
    project = render()
    out = run_script(project, "scripts/coverage_report.py")
    assert out.returncode == 0, out.stderr
    assert "Total cases : 0" in out.stdout


def test_verify_fails_when_coverage_md_is_stale_and_writes_nothing(render, run_script):
    project = render()
    _seed(project)
    before = (project / "COVERAGE.md").read_text()
    out = run_script(project, "scripts/coverage_report.py", "--verify")
    assert out.returncode == 1 and "COVERAGE.md is stale" in out.stdout
    assert (project / "COVERAGE.md").read_text() == before


def test_verify_passes_after_a_regeneration(render, run_script):
    project = render()
    _seed(project)
    run_script(project, "scripts/coverage_report.py")
    out = run_script(project, "scripts/coverage_report.py", "--verify")
    assert out.returncode == 0 and "in sync" in out.stdout
