"""Baseline truthfulness: TestClient must use httpx2, not a hidden warning."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
WARNING = "Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead."
PROBE = """
import warnings
warnings.filterwarnings(
    "error",
    message="Using `httpx` with `starlette.testclient` is deprecated",
)
import fastapi.testclient
import starlette.testclient as testclient
print(testclient.httpx.__name__)
"""


def test_starlette_testclient_uses_httpx2_without_a_warning_filter() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "filterwarnings" not in pyproject
    assert "httpx2>=" in pyproject
    assert '  "httpx>=0.28,<1",' in pyproject
    environment = os.environ.copy()
    environment.pop("PYTEST_CURRENT_TEST", None)
    environment.pop("PYTEST_ADDOPTS", None)
    result = subprocess.run(
        ["uv", "run", "--frozen", "python", "-"],
        cwd=ROOT,
        input=PROBE,
        capture_output=True,
        text=True,
        timeout=120,
        env=environment,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert WARNING not in combined
    assert result.stdout.strip() == "httpx2"


def test_starlette_httpx_todo_stays_open_without_claiming_suppression() -> None:
    matches = [
        line for line in (ROOT / "TODO.md").read_text(encoding="utf-8").splitlines()
        if "Starlette TestClient HTTPX" in line
    ]
    assert matches == [
        "- [ ] Resolve the upstream Starlette TestClient HTTPX deprecation warning before upgrading test dependencies."
    ]
