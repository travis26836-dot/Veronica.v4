import argparse
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "collaboration.py"
SPEC = importlib.util.spec_from_file_location("collaboration_script", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CoordinationError = MODULE.CoordinationError
claim = MODULE.claim
claims_overlap = MODULE.claims_overlap
layout = MODULE.layout
update_task = MODULE.update_task
validate_repository = MODULE.validate_repository


def git(root: Path, *args: str) -> None:
    import subprocess

    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def project(tmp_path: Path) -> Path:
    for name in (
        "AGENTS.md",
        "docs/AGENT-COLLABORATION.md",
        "docs/CURRENT-STATE.md",
        "docs/SOURCE-OF-TRUTH.md",
        "TODO.md",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
    git(tmp_path, "init", "-b", "test-branch")
    git(tmp_path, "config", "user.email", "tests@example.invalid")
    git(tmp_path, "config", "user.name", "Tests")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    return tmp_path


def claim_args(task_id: str, paths: list[str]) -> argparse.Namespace:
    return argparse.Namespace(
        task_id=task_id,
        agent="codex",
        surface="test",
        model="test-model",
        session_id="test-session",
        summary=f"Task {task_id}",
        paths=paths,
        supersedes=[],
    )


def finish_args(task_id: str, evidence: str) -> argparse.Namespace:
    return argparse.Namespace(
        task_id=task_id,
        files=["docs/example.md"],
        tests=["pytest tests/test_collaboration.py"],
        evidence=[evidence],
        limitations=[],
        ruled_out=["A single shared mutable ledger because concurrent writers conflict."],
        next_action="Owner reviews the completed task.",
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("src/veronica_core", "src/veronica_core/app.py"),
        ("docs/*.md", "docs/CURRENT-STATE.md"),
        ("TODO.md", "TODO.md"),
    ],
)
def test_claims_overlap(left: str, right: str) -> None:
    assert claims_overlap(left, right)


def test_claim_rejects_overlapping_active_path(tmp_path: Path) -> None:
    root = project(tmp_path)
    claim(root, claim_args("first-task", ["src/veronica_core"]))
    with pytest.raises(CoordinationError, match="first-task"):
        claim(root, claim_args("second-task", ["src/veronica_core/app.py"]))


def test_claim_allows_separate_paths(tmp_path: Path) -> None:
    root = project(tmp_path)
    claim(root, claim_args("docs-task", ["docs/example.md"]))
    second = claim(root, claim_args("source-task", ["src/example.py"]))
    assert second.is_file()


def test_complete_moves_record_and_writes_handoff(tmp_path: Path) -> None:
    root = project(tmp_path)
    evidence = root / "docs" / "example.md"
    evidence.write_text("evidence", encoding="utf-8")
    claim(root, claim_args("complete-task", ["docs/example.md"]))
    completed = update_task(root, finish_args("complete-task", "docs/example.md"), True)
    record = json.loads(completed.read_text(encoding="utf-8"))
    assert record["status"] == "completed"
    assert not (layout(root)["active"] / "complete-task.json").exists()
    assert (layout(root)["handoffs"] / "complete-task.md").is_file()
    validate_repository(root)


def test_validate_rejects_missing_evidence(tmp_path: Path) -> None:
    root = project(tmp_path)
    claim(root, claim_args("missing-proof", ["docs/example.md"]))
    completed = update_task(root, finish_args("missing-proof", "docs/missing.md"), True)
    assert completed.exists()
    with pytest.raises(CoordinationError, match="missing evidence"):
        validate_repository(root)
