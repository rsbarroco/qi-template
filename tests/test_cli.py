"""The `qi` entry point: wiring between prompts and generator, dry-run, target dir."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from qi import cli
from qi.config import Config

runner = CliRunner()


def _cfg(**over) -> Config:
    base = dict(project_name="Acme Shop QA", project_slug="acme-shop-qa", test_framework="playwright")
    base.update(over)
    return Config(**base)


def test_dry_run_lists_files_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: _cfg(ui_web=True))
    target = tmp_path / "out"
    result = runner.invoke(cli.app, [str(target), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output
    assert "CLAUDE.md" in result.output and ".claude/skills/web-ui/SKILL.md" in result.output
    assert not target.exists()


def test_generates_into_explicit_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: _cfg())
    target = tmp_path / "custom-dir"
    result = runner.invoke(cli.app, [str(target)])
    assert result.exit_code == 0, result.output
    assert (target / "CLAUDE.md").exists()
    assert "Done!" in result.output and "custom-dir" in result.output


def test_default_output_dir_is_the_project_slug(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: _cfg())
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, [])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "acme-shop-qa" / "CLAUDE.md").exists()


def test_banner_names_the_product(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: _cfg())
    result = runner.invoke(cli.app, [str(tmp_path / "p"), "--dry-run"])
    assert "Quality Intelligence" in result.output


def test_next_steps_point_at_claude_md(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: _cfg())
    result = runner.invoke(cli.app, [str(tmp_path / "p")])
    assert "read CLAUDE.md" in result.output
