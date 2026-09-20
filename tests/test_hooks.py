"""The generated hooks (.claude/hooks) are run as Claude Code runs them: a process, JSON on
stdin, exit 2 with the reason on stderr to block. Every rule has a blocking case and an
allowing case, so a hook that always blocks or never blocks fails here."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = ["protect_paths.py", "guard_bash.py", "stop_gate.py"]


def hook(project: Path, name: str, payload: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = {k: v for k, v in os.environ.items() if k not in {"QI_PHASE", "QI_AUTONOMY_OVERRIDE"}}
    full_env.update({"CLAUDE_PROJECT_DIR": str(project), **(env or {})})
    return subprocess.run([sys.executable, str(project / ".claude/hooks" / name)],
                          input=json.dumps(payload), capture_output=True, text=True, cwd=project, env=full_env,
                          encoding="utf-8", errors="replace")


def edit(path: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": path}}


def bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


@pytest.fixture
def project(render) -> Path:
    return render(ci="github_actions")


# --- wiring -------------------------------------------------------------------------------

def test_settings_json_wires_the_three_hooks(project):
    settings = json.loads((project / ".claude/settings.json").read_text(encoding="utf-8"))
    commands = [h["command"] for group in settings["hooks"].values() for entry in group for h in entry["hooks"]]
    assert len(commands) == 3
    for name in HOOKS:
        assert any(name in c and "$CLAUDE_PROJECT_DIR" in c for c in commands), name
    matchers = {entry.get("matcher") for entry in settings["hooks"]["PreToolUse"]}
    assert matchers == {"Edit|Write|MultiEdit", "Bash"}


@pytest.mark.parametrize("name", HOOKS)
def test_each_hook_passes_its_own_self_test(project, name):
    out = subprocess.run([sys.executable, str(project / ".claude/hooks" / name), "--self-test"],
                         capture_output=True, text=True, cwd=project,
                         encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    assert "self-test ok" in out.stdout


@pytest.mark.parametrize("name", HOOKS)
def test_garbage_input_never_blocks(project, name):
    out = subprocess.run([sys.executable, str(project / ".claude/hooks" / name)], input="not json",
                         capture_output=True, text=True, cwd=project,
                         env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)},
                         encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr


# --- protect_paths --------------------------------------------------------------------------

@pytest.mark.parametrize("path, blocked", [
    (".env", True), (".env.local", True), ("config/.env.staging", True), (".env.example", True),
    ("COVERAGE.md", True), (".claude/autonomy.json", True), ("qa/dossiers/SHOP-1/approved", True),
    ("specs/checkout.md", False), ("tests/test_checkout.py", False), ("README.md", False),
    ("qa/dossiers/SHOP-1.md", False), (".claude/rules/new-rule.md", False),
])
def test_protect_paths_rules(project, path, blocked):
    out = hook(project, "protect_paths.py", edit(path))
    assert (out.returncode == 2) is blocked, out.stderr
    if blocked:
        assert "[qi hook]" in out.stderr and path in out.stderr


def test_protect_paths_resolves_absolute_paths_inside_the_project(project):
    out = hook(project, "protect_paths.py", edit(str(project / "COVERAGE.md")))
    assert out.returncode == 2


@pytest.mark.parametrize("phase, path, blocked", [
    ("red", "src/checkout.py", True), ("red", "tests/test_checkout.py", False), ("red", "tests/checkout.spec.ts", False),
    ("red", "features/checkout.feature", False), ("red", "docs/notes.md", False),
    ("implement", "tests/test_checkout.py", True), ("implement", "src/checkout_test.go", True), ("implement", "src/checkout.py", False),
    ("", "tests/test_checkout.py", False), ("", "src/checkout.py", False),
])
def test_tdd_phase_guard(project, phase, path, blocked):
    out = hook(project, "protect_paths.py", edit(path), env={"QI_PHASE": phase})
    assert (out.returncode == 2) is blocked, out.stderr
    if blocked:
        assert f"QI_PHASE={phase}" in out.stderr


# --- guard_bash -----------------------------------------------------------------------------

@pytest.mark.parametrize("command, blocked", [
    ("git push --force origin feat/x", True), ("git push -f origin feat/x", True),
    ("git push --force-with-lease", True), ("git push origin main", True), ("git push main", True),
    ("git push -u origin feat/x", False), ("git push origin feat/main-menu", False),
    ("git -c x=y push -f origin feat/x", True), ("git -c user.name=a push origin main", True),   # options between git and push
    ("git push origin +feat/x", True), ("git push origin +HEAD:feat/x", True),                    # force via refspec
    ("git push origin HEAD:main", True), ("git push origin feat/x:master", True),                 # main as refspec destination
    ("git push origin HEAD:refs/heads/feat/x", False), ("git push origin feat/x:feat/x", False),
    ("git commit --no-verify -m 'x'", True), ("git -c core.hooksPath=/dev/null commit -m x", True),
    ("HUSKY=0 git commit -m x", True), ("git commit -m 'fix'", False),
    ("cat .env", True), ("grep TOKEN .env.local", True), ("cat .env.example", False), ("cat requirements.txt", False),
    ("git commit -m 'docs: never git push --force'", False),      # quoted string is data
    ("cat <<'EOF' > note.md\ngit push --force\nEOF", False),      # heredoc body is data
    ("", False),
])
def test_guard_bash_forbidden_commands(project, command, blocked):
    out = hook(project, "guard_bash.py", bash(command))
    assert (out.returncode == 2) is blocked, out.stderr


def test_merge_is_refused_at_the_generated_level_and_allowed_with_a_session_override(project):
    assert json.loads((project / ".claude/autonomy.json").read_text(encoding="utf-8"))["tasks"]["merge-pr"] == 0
    out = hook(project, "guard_bash.py", bash("gh pr merge 12 --squash"))
    assert out.returncode == 2 and '"merge-pr" is 0' in out.stderr and "needs 3" in out.stderr
    out = hook(project, "guard_bash.py", bash("gh pr merge 12 --squash"), env={"QI_AUTONOMY_OVERRIDE": "merge-pr=3"})
    assert out.returncode == 0, out.stderr


def test_gates_are_read_from_autonomy_json(project):
    cfg = json.loads((project / ".claude/autonomy.json").read_text(encoding="utf-8"))
    cfg["gates"].append({"pattern": r"\bdeploy\s+staging\b", "task": "execute-on-staging", "needs": 2})
    (project / ".claude/autonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    out = hook(project, "guard_bash.py", bash("make deploy staging"))
    assert out.returncode == 2 and '"execute-on-staging" is 1' in out.stderr
    cfg["tasks"]["execute-on-staging"] = 2
    (project / ".claude/autonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    assert hook(project, "guard_bash.py", bash("make deploy staging")).returncode == 0


def test_missing_autonomy_file_means_level_zero(project):
    (project / ".claude/autonomy.json").unlink()
    out = hook(project, "guard_bash.py", bash("gh pr merge 12"))
    assert out.returncode == 2 and '"merge-pr" is 0' in out.stderr


# --- stop_gate ------------------------------------------------------------------------------

SPEC = "| Feature | Status | Test | Notes |\n|---|---|---|---|\n| Place order | ✅ | tests/a.py | |\n| Coupon | ❌ | — | |\n"


def _git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


@pytest.fixture
def repo(project) -> Path:
    _git(project, "init", "-q")
    _git(project, "add", "-A")
    _git(project, "commit", "-q", "-m", "scaffold")
    return project


def test_stop_gate_blocks_when_a_spec_changed_and_coverage_is_stale(repo):
    (repo / "specs/checkout.md").write_text(SPEC, encoding="utf-8")
    out = hook(repo, "stop_gate.py", {"stop_hook_active": False})
    assert out.returncode == 2
    assert "COVERAGE.md is stale" in out.stderr and "coverage_report.py" in out.stderr


def test_stop_gate_allows_once_coverage_is_regenerated(repo):
    (repo / "specs/checkout.md").write_text(SPEC, encoding="utf-8")
    subprocess.run([sys.executable, "scripts/coverage_report.py"], cwd=repo, check=True, capture_output=True)
    assert hook(repo, "stop_gate.py", {}).returncode == 0


def test_stop_gate_ignores_changes_outside_specs(repo):
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    assert hook(repo, "stop_gate.py", {}).returncode == 0


def test_stop_gate_never_blocks_twice(repo):
    (repo / "specs/checkout.md").write_text(SPEC, encoding="utf-8")
    assert hook(repo, "stop_gate.py", {"stop_hook_active": True}).returncode == 0


def test_stop_gate_allows_outside_a_git_repo(project):
    (project / "specs/checkout.md").write_text(SPEC, encoding="utf-8")
    assert hook(project, "stop_gate.py", {}).returncode == 0
