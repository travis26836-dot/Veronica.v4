"""Read public-safe startup evidence for the local Veronica boot dashboard.

The launcher writes records as it progresses.  This module deliberately reads
only a small, allow-listed subset of those records: credentials, SSH details,
private paths, and raw logs never cross the wrapper API boundary.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


STAGES: tuple[tuple[str, str, str], ...] = (
    ("authorization", "Authorization and local preflight", "startup-intent.json"),
    ("provenance", "Pinned model record prepared", "expected-model-manifest.json"),
    ("sleep_guard", "Local supervision armed", "keep-awake-state.json"),
    ("gpu", "GPU availability and selection", "preflight.json"),
    ("pod", "RunPod created", "supervised-state.json"),
    ("volume", "Persistent model volume inspected", "volume-inspection.txt"),
    ("tunnel", "Secure local tunnel established", "tunnel.json"),
    ("wrapper", "Veronica wrapper launched", "wrapper-process.json"),
    ("ui", "Chat interface available", "startup-ui-ready.json"),
    ("provider", "Model server and authenticated alias", "provider-ready.json"),
    ("inference", "First real inference and wrapper verification", "startup-ready.json"),
)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _run_from_environment() -> Path | None:
    raw = os.environ.get("VERONICA_RUN_DIR")
    if not raw:
        return None
    path = Path(raw).resolve()
    return path if path.is_dir() else None


def _single_live_run(evidence_root: Path) -> Path | None:
    """Use a run only when it can be unambiguously identified as still live."""
    candidates: list[Path] = []
    if not evidence_root.is_dir():
        return None
    for child in evidence_root.iterdir():
        state = _read_json(child / "supervised-state.json") if child.is_dir() else None
        if state and state.get("creationAttempted") is True and not (child / "termination.json").exists():
            candidates.append(child)
    return candidates[0] if len(candidates) == 1 else None


def _event(stage_id: str, title: str, state: str, detail: str, at_utc: str | None = None) -> dict[str, str]:
    event = {"id": stage_id, "title": title, "state": state, "detail": detail}
    if at_utc:
        event["atUtc"] = at_utc
    return event


def startup_status(evidence_root: Path) -> dict[str, Any]:
    """Return a display-only lifecycle report based on durable launcher evidence."""
    run = _run_from_environment() or _single_live_run(evidence_root)
    if run is None:
        return {
            "available": False,
            "phase": "idle",
            "detail": "No unambiguous active Veronica startup record is available.",
            "events": [_event(stage_id, title, "pending", "Waiting for a new Start Veronica run.") for stage_id, title, _ in STAGES],
        }

    records = {name: _read_json(run / name) for _, _, name in STAGES if name.endswith(".json")}
    state = records.get("supervised-state.json") or {}
    preflight = records.get("preflight.json") or {}
    provider = records.get("provider-ready.json") or {}
    provider_smoke = _read_json(run / "provider-smoke.json") or {}
    wrapper_smoke = _read_json(run / "wrapper-smoke.json") or {}
    startup_ready = records.get("startup-ready.json") or {}
    provider_smoke_passed = provider_smoke.get("basicSmokePassed") is True
    wrapper_smoke_passed = wrapper_smoke.get("basicSmokePassed") is True
    inference_verified = startup_ready.get("ready") is True or (provider_smoke_passed and wrapper_smoke_passed)
    events: list[dict[str, str]] = []

    for stage_id, title, filename in STAGES:
        record = records.get(filename)
        exists = (run / filename).exists()
        if stage_id == "gpu" and record:
            gpu = record.get("gpu") or record.get("gpuTypeId")
            cost = record.get("listedHourlyUsd")
            detail = f"Selected {gpu}" if gpu else "GPU selection recorded"
            if isinstance(cost, (int, float)):
                detail += f" at ${cost:.2f}/hour"
            status = "complete" if record.get("safeToCreate") else "blocked"
            events.append(_event(stage_id, title, status, detail, record.get("checkedAtUtc")))
        elif stage_id == "pod" and record:
            if record.get("creationAttempted") is True and record.get("podId"):
                events.append(_event(stage_id, title, "complete", "One authorized Pod was created and is under local supervision.", record.get("createdAttemptAtUtc")))
            elif record.get("creationAttempted") is False:
                events.append(_event(stage_id, title, "blocked", "No Pod was created; the launch did not pass pre-creation checks."))
            else:
                events.append(_event(stage_id, title, "running", "Creation request is in progress."))
        elif stage_id == "provider" and record:
            if record.get("ready") is True:
                events.append(_event(stage_id, title, "complete", "Model server answered through the authenticated local tunnel.", record.get("checkedAtUtc")))
            else:
                events.append(_event(stage_id, title, "running", str(record.get("waitingReason") or "Waiting for the model server to answer."), record.get("checkedAtUtc")))
        elif stage_id == "inference":
            if startup_ready.get("ready") is True:
                events.append(_event(stage_id, title, "complete", "Real provider and wrapper response checks were captured.", startup_ready.get("atUtc")))
            elif provider_smoke_passed and wrapper_smoke_passed:
                events.append(_event(stage_id, title, "complete", "Direct provider and Veronica-wrapper smoke responses were captured.", wrapper_smoke.get("checkedAtUtc") or provider_smoke.get("checkedAtUtc")))
            elif provider_smoke_passed:
                events.append(_event(stage_id, title, "running", "Direct provider inference passed; Veronica-wrapper smoke verification is still unrecorded."))
            elif wrapper_smoke_passed:
                events.append(_event(stage_id, title, "running", "Veronica-wrapper inference passed; direct provider smoke verification is still unrecorded."))
            else:
                events.append(_event(stage_id, title, "pending", "Waiting for real provider and wrapper response evidence."))
        elif stage_id == "ui" and record:
            events.append(_event(stage_id, title, "complete" if record.get("uiReady") else "running", "Chat UI is available; inference verification continues separately.", record.get("atUtc")))
        elif exists:
            at_utc = record.get("atUtc") if record else None
            events.append(_event(stage_id, title, "complete", "Recorded by the launcher.", at_utc))
        else:
            prior_running = any(item["state"] == "running" for item in events)
            events.append(_event(stage_id, title, "pending" if not prior_running else "pending", "Waiting for verified launcher evidence."))

    phase = "verified" if inference_verified else "starting"
    if (run / "termination.json").exists():
        phase = "stopped"
    return {
        "available": True,
        "phase": phase,
        "runId": run.name,
        "deadlineUtc": state.get("deadlineUtc"),
        "uiReady": bool((records.get("startup-ui-ready.json") or {}).get("uiReady")),
        "inferenceVerified": inference_verified,
        "events": events,
    }
