"""Shared fixtures. Rendering is fast, so every test gets a fresh project."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qi.config import Config
from qi.generator import generate


def make_config(**overrides) -> Config:
    base = dict(
        project_name="Acme Shop QA",
        project_slug="acme-shop-qa",
        tracker="none",
        doc_platform="none",
        test_framework="playwright",
        ui_web=True,
    )
    base.update(overrides)
    return Config(**base)


@pytest.fixture
def render(tmp_path):
    """render(**config_overrides) -> Path of a freshly generated project."""
    counter = {"n": 0}

    def _render(**overrides) -> Path:
        counter["n"] += 1
        target = tmp_path / f"project-{counter['n']}"
        generate(make_config(**overrides), target)
        return target

    return _render


@pytest.fixture
def run_script():
    """run_script(project, 'scripts/x.py', *args, env=...) -> CompletedProcess (never raises)."""

    def _run(project: Path, script: str, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        import os
        full_env = {**os.environ, **(env or {})}
        return subprocess.run(
            [sys.executable, str(project / script), *args],
            cwd=project, capture_output=True, text=True, env=full_env,
            encoding="utf-8", errors="replace",
        )

    return _run
