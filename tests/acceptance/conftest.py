"""Steps shared by every acceptance feature: scaffolding and looking at the result."""
from __future__ import annotations

from pathlib import Path

from pytest_bdd import parsers, then, when

from qi.generator import generate


@when("I scaffold the project", target_fixture="project")
def scaffold(config, tmp_path) -> Path:
    target = tmp_path / config.project_slug
    generate(config, target)
    return target


@then(parsers.re(r'the skills include "(?P<a>[^"]+)" and "(?P<b>[^"]+)"$'))
def skills_include_two(project, a, b):
    for name in (a, b):
        assert (project / ".claude/skills" / f"{name}.md").exists(), name


@then(parsers.re(r'the skills include "(?P<a>[^"]+)"$'))
def skills_include_one(project, a):
    assert (project / ".claude/skills" / f"{a}.md").exists(), a


@then(parsers.re(r'the skills do not include "(?P<name>[^"]+)"$'))
def skills_exclude(project, name):
    assert not (project / ".claude/skills" / f"{name}.md").exists()
