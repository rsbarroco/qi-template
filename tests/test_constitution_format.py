"""T2 — the constitution diet and the Agent Skills format: CLAUDE.md stays short, rules are
scoped by paths, every skill is a folder with SKILL.md and a third-person description, and
skills with side effects cannot be invoked by the model."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from qi.config import Config
from qi.generator import generate
from qi.skills import MAX_BODY_LINES, SKILLS

MAX_CLAUDE_MD_LINES = 200
FULL = dict(tracker="jira", tracker_project_key="FULL", doc_platform="confluence", test_repo="testrail",
            comm_platform="slack", comm_platform_channel="#qa", sql_dbs=["postgresql"], nosql_dbs=["mongodb"],
            ui_web=True, ui_mobile_ios=True, test_framework="playwright", cloud="gcp", queues=["sqs"],
            performance="k6", ci="github_actions")


def _frontmatter(text: str) -> dict | None:
    if not text.startswith("---\n"):
        return None
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end]) or {}


@pytest.mark.parametrize("overrides", [{}, FULL], ids=["minimal", "full"])
def test_claude_md_is_under_200_lines(render, overrides):
    project = render(**overrides)
    lines = (project / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) < MAX_CLAUDE_MD_LINES, len(lines)


def test_claude_md_points_at_rules_skills_autonomy_and_hooks(render):
    text = (render() / "CLAUDE.md").read_text(encoding="utf-8")
    for needle in [".claude/rules/", ".claude/skills/<name>/SKILL.md", "AUTONOMY.md", ".claude/hooks/", "docs/decisions/"]:
        assert needle in text, needle


@pytest.mark.parametrize("overrides", [{}, FULL], ids=["minimal", "full"])
def test_every_skill_is_a_folder_with_skill_md_and_frontmatter(render, overrides):
    project = render(**overrides)
    folders = list((project / ".claude/skills").iterdir())
    assert folders and all(f.is_dir() for f in folders)
    for folder in folders:
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        fm = _frontmatter(text)
        assert fm is not None, folder.name
        assert fm["name"] == folder.name
        assert len(text.splitlines()) < MAX_BODY_LINES, folder.name
        assert not re.search(r"(?<!\$){{|{%", text), folder.name


@pytest.mark.parametrize("meta", SKILLS.values(), ids=lambda m: m.name)
def test_descriptions_are_third_person_and_say_when_to_use(meta):
    d = meta.description
    assert re.match(r"[A-Z][a-z]+s ", d), d              # "Drives ...", "Runs ...": third person
    assert not re.match(r"(I |You |Use this|Invoke)", d)
    assert "Used " in d                                 # when to use it
    assert 40 < len(d) <= 1024


def test_side_effect_skills_are_not_model_invocable(render):
    project = render(**FULL)
    for name, meta in SKILLS.items():
        path = project / ".claude/skills" / name / "SKILL.md"
        if not path.exists():
            continue
        fm = _frontmatter(path.read_text(encoding="utf-8"))
        assert fm.get("disable-model-invocation", False) is meta.side_effect, name
    assert {m.name for m in SKILLS.values() if m.side_effect} == {"comm-broadcast", "report-bug"}


def test_claude_md_names_the_side_effect_skills(render):
    text = (render(**FULL) / "CLAUDE.md").read_text(encoding="utf-8")
    assert "`comm-broadcast`, `report-bug`" in text and "disable-model-invocation" in text


def test_every_skill_template_has_a_catalogue_entry():
    templates = {p.name[: -len(".md.j2")] for p in Path("qi/templates/skills").glob("*.md.j2")}
    assert templates == set(SKILLS)


@pytest.mark.parametrize("rule, scoped", [
    ("assertion-validity", True), ("evidence-based-qa", True), ("coverage-sync", True), ("feedback-loop", True),
    ("reusable-test-data", True), ("dependencies", True), ("test-execution-path", True), ("confluence-editing", True),
    ("environment-safety", False), ("connection-validation", False), ("pipeline", False),
])
def test_rules_carry_paths_frontmatter_when_scoped(render, rule, scoped):
    project = render(**FULL)
    text = (project / ".claude/rules" / f"{rule}.md").read_text(encoding="utf-8")
    fm = _frontmatter(text)
    if scoped:
        assert fm and isinstance(fm["paths"], list) and fm["paths"], rule
        assert all(isinstance(p, str) and p for p in fm["paths"])
    else:
        assert fm is None, rule      # always-on rules have no frontmatter
    assert "# Rule:" in text


def test_pipeline_rule_only_in_pipeline_mode(render):
    assert (render(tracker="jira", doc_platform="confluence") / ".claude/rules/pipeline.md").exists()
    assert not (render() / ".claude/rules/pipeline.md").exists()


# --- autonomy ---------------------------------------------------------------------------------

def test_autonomy_json_is_valid_and_agrees_with_autonomy_md(render):
    project = render(**FULL)
    cfg = json.loads((project / ".claude/autonomy.json").read_text(encoding="utf-8"))
    md = (project / "AUTONOMY.md").read_text(encoding="utf-8")
    assert cfg["tasks"]["merge-pr"] == 0 and cfg["tasks"]["case-approve"] == 0 and cfg["tasks"]["comm-post"] == 0
    assert all(0 <= v <= 3 for v in cfg["tasks"].values())
    for task, level in cfg["tasks"].items():
        assert re.search(rf"\| `{re.escape(task)}` \| {level} \|", md), task
    assert all({"pattern", "task", "needs"} <= set(g) and g["task"] in cfg["tasks"] for g in cfg["gates"])


def test_autonomy_tasks_follow_the_stack(render):
    minimal = json.loads((render() / ".claude/autonomy.json").read_text(encoding="utf-8"))["tasks"]
    assert "comm-post" not in minimal and "tracker-transition" not in minimal and "doc-publish" not in minimal
    full = json.loads((render(**FULL) / ".claude/autonomy.json").read_text(encoding="utf-8"))
    assert {"comm-post", "tracker-transition", "bug-report", "doc-publish"} <= set(full["tasks"])
    assert any(g["task"] == "execute-on-staging" for g in full["gates"])     # performance tool gated


# --- dependencies, ADRs -----------------------------------------------------------------------

def test_dependabot_only_with_github_actions_and_follows_the_stack(render):
    assert not (render(ci="gitlab_ci") / ".github/dependabot.yml").exists()
    pip_only = yaml.safe_load((render(ci="github_actions", test_framework="robot") / ".github/dependabot.yml").read_text(encoding="utf-8"))
    assert [u["package-ecosystem"] for u in pip_only["updates"]] == ["pip", "github-actions"]
    npm = yaml.safe_load((render(ci="github_actions", test_framework="playwright") / ".github/dependabot.yml").read_text(encoding="utf-8"))
    ecosystems = {u["package-ecosystem"]: u for u in npm["updates"]}
    assert set(ecosystems) == {"pip", "npm", "github-actions"}
    assert ecosystems["npm"]["ignore"][0]["dependency-name"] == "playwright"
    assert all(u["schedule"]["interval"] == "weekly" for u in npm["updates"])


def test_dependencies_rule_names_the_validation_and_the_task(render):
    text = (render() / ".claude/rules/dependencies.md").read_text(encoding="utf-8")
    assert "merge-dependency-pr" in text and "CI is green" in text and "changelog" in text.lower()


def test_adr_scaffold_with_a_confirmed_first_decision(render):
    project = render()
    adrs = sorted(p.name for p in (project / "docs/decisions").iterdir())
    assert adrs == ["0001-hooks-enforce-the-constitution.md", "README.md", "TEMPLATE.md"]
    first = (project / "docs/decisions/0001-hooks-enforce-the-constitution.md").read_text(encoding="utf-8")
    assert "**Status:** accepted" in first and "## Confirmation" in first and "--self-test" in first
