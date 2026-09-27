"""Universal, fail-closed controller dispatch for Veronica's paid start workflow.

Every agent uses the same command.  The command either invokes the checked
Windows launcher on the designated controller host or dispatches a manual
GitHub Actions workflow to that controller.  It never uses a general Runpod
MCP mutation as a substitute for the supervised Veronica lifecycle.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPOSITORY = "travis26836-dot/Veronica.v4"
DEFAULT_BRANCH = "main"
DEFAULT_WORKFLOW = "start-veronica.yml"
DEFAULT_RUNNER_LABELS = ("self-hosted", "windows", "x64", "veronica-controller")
DEFAULT_CONTEXT = "Current owner request routed through the universal Veronica start command."


class UniversalStartError(RuntimeError):
    """A request cannot safely reach the checked controller launcher."""


@dataclass(frozen=True)
class StartPlan:
    command: str
    duration_minutes: int
    maximum_hourly_usd: float
    resource_count: int
    preferred_gpu: str
    network_volume_id: str
    shutdown_mode: str
    execution_mode: str
    controller_labels: tuple[str, ...]
    resource_creation_attempted: bool = False
    current_authorization_required: bool = True
    platform_deadline_enforced: bool = False


def _read_profile(profile_path: Path | None = None) -> dict:
    path = profile_path or ROOT / "config" / "runpod-core.json"
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UniversalStartError(f"Unable to read the Veronica Runpod profile: {error}") from error
    return profile


def _validate_request_text(value: str, field: str, *, limit: int) -> str:
    value = value.strip()
    if not value or len(value) > limit or "\x00" in value:
        raise UniversalStartError(f"{field} must be non-empty, contain no NUL byte, and be at most {limit} characters")
    return value


def _validate_request(duration_minutes: int, requested_by: str, authorization_context: str, profile: dict) -> None:
    safety = profile["safety"]
    if isinstance(duration_minutes, bool) or not isinstance(duration_minutes, int):
        raise UniversalStartError("Duration must be a whole number of minutes")
    maximum = safety["maximumCustomDurationMinutes"]
    if not 1 <= duration_minutes <= maximum:
        raise UniversalStartError(f"Duration must be between 1 and {maximum} minutes")
    _validate_request_text(requested_by, "Requested-by", limit=120)
    _validate_request_text(authorization_context, "Authorization context", limit=500)


def build_plan(duration_minutes: int, *, execution_mode: str, profile_path: Path | None = None) -> StartPlan:
    profile = _read_profile(profile_path)
    _validate_request(duration_minutes, "plan", "Non-mutating plan only.", profile)
    pod, safety = profile["pod"], profile["safety"]
    return StartPlan(
        command="Start Veronica",
        duration_minutes=duration_minutes,
        maximum_hourly_usd=float(safety["maximumHourlyUsd"]),
        resource_count=1,
        preferred_gpu=pod["gpuTypeId"],
        network_volume_id=pod["networkVolumeId"],
        shutdown_mode=safety["defaultShutdownMode"],
        execution_mode=execution_mode,
        controller_labels=DEFAULT_RUNNER_LABELS,
    )


def _repository_from_origin(root: Path = ROOT) -> str:
    fallback = DEFAULT_REPOSITORY
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"], cwd=root, check=False,
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return fallback
    origin = result.stdout.strip()
    patterns = (
        r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?$",
        r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, origin)
        if match:
            return match.group(1)
    return fallback


def eligible_controller_runners(repository: str, *, run=subprocess.run) -> list[dict]:
    """Return online, idle runners matching every required controller label."""
    command = ["gh", "api", f"repos/{repository}/actions/runners?per_page=100"]
    try:
        result = run(command, check=False, capture_output=True, text=True, timeout=20)
    except FileNotFoundError as error:
        raise UniversalStartError("GitHub CLI is required to dispatch from a non-controller host") from error
    except subprocess.TimeoutExpired as error:
        raise UniversalStartError("Timed out while checking the Veronica controller runner") from error
    if result.returncode:
        message = result.stderr.strip() or "GitHub CLI could not inspect repository runners"
        raise UniversalStartError(message)
    try:
        runners = json.loads(result.stdout).get("runners", [])
    except json.JSONDecodeError as error:
        raise UniversalStartError("GitHub returned an invalid self-hosted runner inventory") from error
    required = set(DEFAULT_RUNNER_LABELS)
    return [
        runner
        for runner in runners
        if runner.get("status") == "online"
        and runner.get("busy") is False
        and required.issubset({label.get("name") for label in runner.get("labels", [])})
    ]


def dispatch_to_controller(
    *, repository: str, duration_minutes: int, requested_by: str, authorization_context: str,
    workflow: str = DEFAULT_WORKFLOW, branch: str = DEFAULT_BRANCH, run=subprocess.run,
) -> None:
    """Dispatch only after a matching idle controller runner is known to be online."""
    runners = eligible_controller_runners(repository, run=run)
    if not runners:
        labels = ", ".join(DEFAULT_RUNNER_LABELS)
        raise UniversalStartError(
            f"No online idle Veronica controller runner is available (required labels: {labels}). "
            "No Runpod resource was created."
        )
    command = [
        "gh", "workflow", "run", workflow, "--repo", repository, "--ref", branch,
        "--raw-field", "authorized_start=true",
        "--raw-field", f"duration_minutes={duration_minutes}",
        "--raw-field", f"requested_by={requested_by}",
        "--raw-field", f"authorization_context={authorization_context}",
    ]
    try:
        result = run(command, check=False, capture_output=True, text=True, timeout=30)
    except FileNotFoundError as error:
        raise UniversalStartError("GitHub CLI is required to dispatch the Veronica controller workflow") from error
    except subprocess.TimeoutExpired as error:
        raise UniversalStartError("Timed out while dispatching the Veronica controller workflow") from error
    if result.returncode:
        message = result.stderr.strip() or "GitHub rejected the Veronica controller dispatch"
        raise UniversalStartError(message)


def is_local_controller(*, run=subprocess.run) -> bool:
    """Identify the Windows host that owns Veronica's required WSL control plane."""
    if os.name != "nt":
        return False
    command = [
        "wsl.exe", "-e", "bash", "-lc",
        "command -v runpodctl >/dev/null && "
        "test -f /home/dubs/.ssh/id_ed25519_runpod_noirworks && "
        "test -f /home/dubs/.ssh/id_ed25519_runpod_noirworks.pub",
    ]
    try:
        result = run(command, check=False, capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def run_on_local_controller(*, duration_minutes: int, requested_by: str, authorization_context: str, run=subprocess.run) -> None:
    """Invoke the checked PowerShell adapter only on a Windows controller host."""
    if not is_local_controller(run=run):
        raise UniversalStartError(
            "This host is not the configured Windows Veronica controller. Use the default dispatch mode instead; "
            "do not create a Pod directly through the general Runpod MCP."
        )
    pwsh = shutil.which("pwsh")
    if not pwsh:
        raise UniversalStartError("PowerShell 7 (pwsh) is required on the Veronica controller host")
    script = ROOT / "scripts" / "start-veronica-universal.ps1"
    command = [
        pwsh, "-NoProfile", "-NonInteractive", "-File", str(script),
        "-DurationMinutes", str(duration_minutes),
        "-RequestedBy", requested_by,
        "-AuthorizationContext", authorization_context,
    ]
    try:
        result = run(command, cwd=ROOT, check=False, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired as error:
        raise UniversalStartError("The checked Veronica launcher exceeded its bounded startup window") from error
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip() or "The checked Veronica launcher failed"
        raise UniversalStartError(message)
    if result.stdout.strip():
        print(result.stdout.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="veronica-start",
        description="Route a fresh Veronica start authorization to the approved supervised controller.",
    )
    parser.add_argument("--duration-minutes", type=int, default=None, help="Approved run window (default: profile default).")
    parser.add_argument("--authorize-start", action="store_true", help="Confirm this invocation represents a current owner start request.")
    parser.add_argument("--requested-by", default="trusted-agent", help="Agent or owner identity for the run evidence.")
    parser.add_argument("--authorization-context", default=DEFAULT_CONTEXT, help="Short non-secret explanation saved with the one-use approval.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--local", action="store_true", help="Run only on the Windows controller host.")
    mode.add_argument("--dispatch", action="store_true", help="Dispatch the approved GitHub controller workflow.")
    parser.add_argument("--plan", action="store_true", help="Print a no-cloud, no-dispatch start plan.")
    parser.add_argument("--repo", default=None, help="GitHub repository for the controller workflow.")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help="Controller workflow file name.")
    return parser


def execute(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profile = _read_profile()
    duration = args.duration_minutes if args.duration_minutes is not None else profile["safety"]["defaultDurationMinutes"]
    if args.local:
        execution_mode = "local"
    elif args.dispatch:
        execution_mode = "dispatch"
    elif args.plan:
        execution_mode = "local" if os.name == "nt" else "dispatch"
    else:
        execution_mode = "local" if is_local_controller() else "dispatch"
    _validate_request(duration, args.requested_by, args.authorization_context, profile)
    plan = build_plan(duration, execution_mode=execution_mode)
    if args.plan:
        print(json.dumps(asdict(plan), indent=2))
        return 0
    if not args.authorize_start:
        raise UniversalStartError(
            "Refusing to dispatch or launch: pass --authorize-start only for a current explicit owner request. "
            "Use --plan for a non-mutating preview."
        )
    if execution_mode == "local":
        run_on_local_controller(
            duration_minutes=duration, requested_by=args.requested_by,
            authorization_context=args.authorization_context,
        )
        return 0
    repository = args.repo or _repository_from_origin()
    dispatch_to_controller(
        repository=repository, duration_minutes=duration, requested_by=args.requested_by,
        authorization_context=args.authorization_context, workflow=args.workflow,
    )
    print(json.dumps({
        "status": "dispatched", "repository": repository, "workflow": args.workflow,
        "durationMinutes": duration, "resourceCreationAttempted": False,
        "note": "The GitHub controller job performs the checked preflight and is the only component allowed to create the Pod.",
    }, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Console entry point that reports ordinary policy refusals without a traceback."""
    try:
        return execute(argv)
    except UniversalStartError as error:
        print(f"veronica-start: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
