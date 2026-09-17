"""Repository-local coordination for Codex, Hermes, and GitHub Copilot."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable


REQUIRED_FILES = (
    "AGENTS.md",
    "docs/AGENT-COLLABORATION.md",
    "docs/CURRENT-STATE.md",
    "docs/SOURCE-OF-TRUTH.md",
    "TODO.md",
)
TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
AGENTS = ("codex", "hermes", "copilot", "human", "other")


class CoordinationError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise CoordinationError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise CoordinationError("Run this command inside a Git worktree.")
    return Path(result.stdout.strip()).resolve()


def normalize_claim(path: str) -> str:
    value = path.strip().replace("\\", "/").strip("/")
    if not value or value.startswith("../") or "/../" in value:
        raise CoordinationError(f"Invalid claimed path: {path!r}")
    return value


def claims_overlap(left: str, right: str) -> bool:
    left = normalize_claim(left)
    right = normalize_claim(right)
    if left == right:
        return True
    left_prefix = left.rstrip("/*")
    right_prefix = right.rstrip("/*")
    if left_prefix and (right == left_prefix or right.startswith(left_prefix + "/")):
        return True
    if right_prefix and (left == right_prefix or left.startswith(right_prefix + "/")):
        return True
    return PurePosixPath(left).match(right) or PurePosixPath(right).match(left)


def paths_overlap(left: Iterable[str], right: Iterable[str]) -> bool:
    return any(claims_overlap(a, b) for a in left for b in right)


def layout(root: Path) -> dict[str, Path]:
    base = root / "coordination"
    return {
        "base": base,
        "active": base / "tasks" / "active",
        "completed": base / "tasks" / "completed",
        "handoffs": base / "handoffs",
        "sessions": base / "sessions",
        "lock": base / ".claim-lock",
    }


def ensure_layout(root: Path) -> dict[str, Path]:
    paths = layout(root)
    for key in ("active", "completed", "handoffs", "sessions"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


@contextmanager
def claim_lock(root: Path):
    paths = ensure_layout(root)
    try:
        paths["lock"].mkdir()
    except FileExistsError as exc:
        raise CoordinationError(
            "Another claim operation is active, or coordination/.claim-lock is stale. "
            "Inspect it before retrying; do not delete it while another agent is working."
        ) from exc
    try:
        (paths["lock"] / "owner.json").write_text(
            json.dumps({"pid": os.getpid(), "created_at": utc_now()}, indent=2) + "\n",
            encoding="utf-8",
        )
        yield paths
    finally:
        owner = paths["lock"] / "owner.json"
        if owner.exists():
            owner.unlink()
        paths["lock"].rmdir()


def load_records(directory: Path) -> list[dict]:
    records = []
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CoordinationError(f"Invalid task record {path}: {exc}") from exc
        records.append(record)
    return records


def write_json_exclusive(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise CoordinationError(f"Record already exists: {path}") from exc


def write_json_replace(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def validate_record(record: dict, require_completion: bool = False) -> list[str]:
    required = {
        "schema_version", "task_id", "agent", "surface", "summary", "status",
        "worktree", "branch", "repo_commit_before", "paths", "started_at",
        "files_changed", "tests", "evidence", "limitations", "ruled_out",
        "next_action",
    }
    errors = [f"missing field {name}" for name in sorted(required - record.keys())]
    if record.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not TASK_ID_RE.fullmatch(str(record.get("task_id", ""))):
        errors.append("invalid task_id")
    if record.get("agent") not in AGENTS:
        errors.append("invalid agent")
    if not isinstance(record.get("paths"), list) or not record.get("paths"):
        errors.append("paths must be a non-empty array")
    if require_completion:
        if record.get("status") != "completed":
            errors.append("completed record must have status completed")
        if not record.get("ended_at"):
            errors.append("completed record requires ended_at")
        if not record.get("evidence"):
            errors.append("completed record requires evidence")
        if not record.get("next_action"):
            errors.append("completed record requires next_action")
    return errors


def preflight(root: Path, intended_paths: list[str] | None = None) -> list[str]:
    messages = []
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        raise CoordinationError("Missing authority files: " + ", ".join(missing))
    branch = run_git(root, "branch", "--show-current")
    if not branch:
        raise CoordinationError("Detached HEAD: create or switch to a named branch before editing.")
    commit = run_git(root, "rev-parse", "--short", "HEAD")
    dirty = run_git(root, "status", "--short")
    active = load_records(layout(root)["active"])
    if intended_paths:
        normalized = [normalize_claim(item) for item in intended_paths]
        conflicts = [r["task_id"] for r in active if paths_overlap(normalized, r.get("paths", []))]
        if conflicts:
            raise CoordinationError("Claimed paths overlap active tasks: " + ", ".join(conflicts))
    messages.append(f"PASS repository={root}")
    messages.append(f"PASS branch={branch} commit={commit}")
    messages.append(f"INFO active_tasks={len(active)}")
    messages.append(f"INFO dirty={'yes' if dirty else 'no'}")
    if dirty:
        messages.append("NOTICE preserve existing changes; stage exact reviewed paths, never git add .")
    return messages


def claim(root: Path, args: argparse.Namespace) -> Path:
    if not TASK_ID_RE.fullmatch(args.task_id):
        raise CoordinationError("task-id must use 3-80 lowercase letters, digits, dots, dashes, or underscores")
    claimed_paths = sorted({normalize_claim(item) for item in args.paths})
    with claim_lock(root) as paths:
        existing = load_records(paths["active"])
        conflicts = [r["task_id"] for r in existing if paths_overlap(claimed_paths, r.get("paths", []))]
        if conflicts:
            raise CoordinationError("Path ownership conflict with: " + ", ".join(conflicts))
        record = {
            "schema_version": 1,
            "task_id": args.task_id,
            "agent": args.agent,
            "model": args.model,
            "surface": args.surface,
            "session_id": args.session_id,
            "summary": args.summary,
            "status": "active",
            "worktree": str(root),
            "branch": run_git(root, "branch", "--show-current"),
            "repo_commit_before": run_git(root, "rev-parse", "HEAD"),
            "repo_commit_after": None,
            "paths": claimed_paths,
            "started_at": utc_now(),
            "ended_at": None,
            "files_changed": [],
            "tests": [],
            "evidence": [],
            "limitations": [],
            "ruled_out": [],
            "next_action": None,
            "supersedes": sorted(set(args.supersedes or [])),
        }
        destination = paths["active"] / f"{args.task_id}.json"
        write_json_exclusive(destination, record)
        return destination


def find_active(root: Path, task_id: str) -> tuple[Path, dict]:
    path = layout(root)["active"] / f"{task_id}.json"
    if not path.is_file():
        raise CoordinationError(f"No active task named {task_id}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def update_task(root: Path, args: argparse.Namespace, complete: bool) -> Path:
    active_path, record = find_active(root, args.task_id)
    record["status"] = "completed" if complete else args.status
    record["files_changed"] = sorted(set(args.files or []))
    record["tests"] = args.tests or []
    record["evidence"] = args.evidence or []
    record["limitations"] = args.limitations or []
    record["ruled_out"] = args.ruled_out or []
    record["next_action"] = args.next_action
    record["repo_commit_after"] = run_git(root, "rev-parse", "HEAD")
    if complete:
        record["ended_at"] = utc_now()
        errors = validate_record(record, require_completion=True)
        if errors:
            raise CoordinationError("; ".join(errors))
        paths = ensure_layout(root)
        completed = paths["completed"] / active_path.name
        if completed.exists():
            raise CoordinationError(f"Completed record already exists: {completed}")
        write_json_exclusive(completed, record)
        handoff = paths["handoffs"] / f"{args.task_id}.md"
        lines = [
            f"# Handoff: {args.task_id}", "", "**Status:** completed", "",
            f"**Agent:** {record['agent']} / {record['surface']}", "",
            f"**Started:** {record['started_at']}", "", f"**Ended:** {record['ended_at']}", "",
            "## Scope", "", record["summary"], "", "## Files changed", "",
            *[f"- `{item}`" for item in record["files_changed"]], "", "## Tests", "",
            *[f"- {item}" for item in record["tests"]], "", "## Evidence", "",
            *[f"- `{item}`" for item in record["evidence"]], "", "## Limitations", "",
            *([f"- {item}" for item in record["limitations"]] or ["- None recorded."]), "",
            "## Ruled out", "",
            *([f"- {item}" for item in record["ruled_out"]] or ["- None recorded."]), "",
            "## Next safe action", "", record["next_action"], "",
        ]
        handoff.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        active_path.unlink()
        return completed
    write_json_replace(active_path, record)
    return active_path


def validate_repository(root: Path) -> list[str]:
    messages = preflight(root)
    paths = layout(root)
    errors = []
    active = load_records(paths["active"])
    completed = load_records(paths["completed"])
    for record in active:
        errors.extend(f"{record.get('task_id')}: {e}" for e in validate_record(record))
    for record in completed:
        errors.extend(f"{record.get('task_id')}: {e}" for e in validate_record(record, True))
        handoff = paths["handoffs"] / f"{record.get('task_id')}.md"
        if not handoff.is_file():
            errors.append(f"{record.get('task_id')}: missing handoff")
        for evidence in record.get("evidence", []):
            if evidence.startswith("commit:") or evidence.startswith("command:"):
                continue
            if not (root / evidence).exists():
                errors.append(f"{record.get('task_id')}: missing evidence {evidence}")
    for index, left in enumerate(active):
        for right in active[index + 1 :]:
            if paths_overlap(left.get("paths", []), right.get("paths", [])):
                errors.append(f"active overlap: {left.get('task_id')} and {right.get('task_id')}")
    if errors:
        raise CoordinationError("\n".join(errors))
    messages.append(f"PASS records active={len(active)} completed={len(completed)}")
    return messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Repository root (defaults to current Git root)")
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", help="Check authority files, branch, status, and optional paths")
    pre.add_argument("--path", dest="paths", action="append", default=[])

    claim_parser = sub.add_parser("claim", help="Atomically claim paths for a task")
    claim_parser.add_argument("--task-id", required=True)
    claim_parser.add_argument("--agent", required=True, choices=AGENTS)
    claim_parser.add_argument("--surface", required=True)
    claim_parser.add_argument("--model")
    claim_parser.add_argument("--session-id")
    claim_parser.add_argument("--summary", required=True)
    claim_parser.add_argument("--path", dest="paths", action="append", required=True)
    claim_parser.add_argument("--supersedes", action="append", default=[])

    sub.add_parser("status", help="List active task claims")
    sub.add_parser("validate", help="Validate all coordination records")

    for name, complete in (("handoff", False), ("complete", True)):
        command = sub.add_parser(name, help=f"{'Complete' if complete else 'Update'} a task record")
        command.add_argument("--task-id", required=True)
        if not complete:
            command.add_argument("--status", choices=("handoff", "blocked"), default="handoff")
        command.add_argument("--file", dest="files", action="append", default=[])
        command.add_argument("--test", dest="tests", action="append", default=[])
        command.add_argument("--evidence", action="append", default=[])
        command.add_argument("--limitation", dest="limitations", action="append", default=[])
        command.add_argument("--ruled-out", action="append", default=[])
        command.add_argument("--next-action", required=True)
        command.set_defaults(complete=complete)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = (args.root.resolve() if args.root else repo_root())
        if args.command == "preflight":
            output = preflight(root, args.paths)
        elif args.command == "claim":
            output = [f"CREATED {claim(root, args).relative_to(root)}"]
        elif args.command == "status":
            records = load_records(layout(root)["active"])
            output = [json.dumps(record, sort_keys=True) for record in records] or ["No active tasks."]
        elif args.command == "validate":
            output = validate_repository(root)
        else:
            output = [f"UPDATED {update_task(root, args, args.complete).relative_to(root)}"]
        print("\n".join(output))
        return 0
    except CoordinationError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
