"""Validate a remote START request and create its one-use authorization record.

This module deliberately does not create a Pod.  The GitHub Actions entry point
uses the existing supervised controller after these checks have passed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config" / "runpod-core.json"


def read_profile():
    return json.loads(PROFILE.read_text())


def validate_request(duration_minutes: int, authorization: str, profile: dict) -> None:
    safety = profile["safety"]
    allowed = set(safety["presetDurationMinutes"])
    if duration_minutes not in allowed and not 1 <= duration_minutes <= safety["maximumCustomDurationMinutes"]:
        raise ValueError("duration must be a configured preset or within the profile maximum")
    if authorization != "START_VERONICA":
        raise ValueError("fresh remote authorization must explicitly be START_VERONICA")


def write_approval(run_dir: Path, duration_minutes: int, authorization: str) -> Path:
    profile = read_profile()
    validate_request(duration_minutes, authorization, profile)
    if run_dir.exists() and any(run_dir.iterdir()):
        raise ValueError("run directory is not empty; remote STARTs cannot be retried")
    if not re.fullmatch(r"[0-9TZ-]+-start-veronica", run_dir.name):
        raise ValueError("run directory must be a UTC timestamped start-veronica directory")
    run_dir.mkdir(parents=True, exist_ok=False)
    approval = {
        "runId": run_dir.name,
        "authorizedAtUtc": datetime.now(timezone.utc).isoformat(),
        "maxHourlyUsd": profile["safety"]["maximumHourlyUsd"],
        "durationMinutes": duration_minutes,
        "resourceCount": 1,
        "gpuTypeId": profile["pod"]["gpuTypeId"],
        "networkVolumeId": profile["pod"]["networkVolumeId"],
        "modelRevision": profile["model"]["revision"],
        "shutdownMode": "supervised-with-local-backup",
        "authorizationSource": "github-actions-environment-approval",
    }
    path = run_dir / "approval.json"
    path.write_text(json.dumps(approval, indent=2) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate", "approve"])
    parser.add_argument("--duration-minutes", type=int, required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--run-dir")
    args = parser.parse_args()
    profile = read_profile()
    if args.command == "validate" and args.authorization == "PLAN_ONLY":
        safety = profile["safety"]
        if not (args.duration_minutes in set(safety["presetDurationMinutes"])
                or 1 <= args.duration_minutes <= safety["maximumCustomDurationMinutes"]):
            raise ValueError("duration must be a configured preset or within the profile maximum")
    else:
        validate_request(args.duration_minutes, args.authorization, profile)
    if args.command == "validate":
        print(json.dumps({"valid": True, "durationMinutes": args.duration_minutes,
                          "shutdownMode": "supervised-with-local-backup"}))
        return 0
    if not args.run_dir:
        parser.error("--run-dir is required for approve")
    print(write_approval(Path(args.run_dir), args.duration_minutes, args.authorization))
    return 0


if __name__ == "__main__":
    sys.exit(main())
