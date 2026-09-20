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


def _write_config(tmp_path, **over):
    import json
    data = {"project_name": "Acme Shop QA", "tracker": "jira", "tracker_project_key": "SHOP",
            "ui_web": True, "test_framework": "playwright", "ci": "github_actions"}
    data.update(over)
    path = tmp_path / "qi.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_config_file_generates_without_asking(tmp_path, monkeypatch):
    def never(): raise AssertionError("ask() must not be called with --config")
    monkeypatch.setattr(cli, "ask", never)
    target = tmp_path / "out"
    result = runner.invoke(cli.app, [str(target), "--config", str(_write_config(tmp_path))])
    assert result.exit_code == 0, result.output
    assert (target / "CLAUDE.md").exists() and "Jira" in (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert (target / ".github/workflows/tests.yml").exists()


def test_config_file_default_output_dir_is_the_derived_slug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["--config", str(_write_config(tmp_path))])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "acme-shop-qa" / "CLAUDE.md").exists()


def test_invalid_config_file_fails_with_the_reasons(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ask", lambda: (_ for _ in ()).throw(AssertionError("no prompt")))
    result = runner.invoke(cli.app, [str(tmp_path / "out"), "--config", str(_write_config(tmp_path, tracker="trello", extra=1))])
    assert result.exit_code == 2
    assert "tracker: 'trello'" in result.output and "unknown key 'extra'" in result.output
    assert not (tmp_path / "out").exists()


def test_missing_config_file_fails_cleanly(tmp_path):
    result = runner.invoke(cli.app, [str(tmp_path / "out"), "--config", str(tmp_path / "nope.json")])
    assert result.exit_code == 2 and "Cannot use" in result.output
