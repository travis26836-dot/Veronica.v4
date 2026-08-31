"""Offline authorization and authenticated startup-readiness checks."""
import importlib.util
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load("runpod_core")
with patch.dict(sys.modules, {"runpod_core": core}):
    controller = load("supervised_runpod")


def approval(profile, run):
    return {"runId": run.name, "resourceCount": 1, "maxHourlyUsd": 1.75,
            "durationMinutes": 60, "shutdownMode": "supervised-with-local-backup",
            "authorizedAtUtc": datetime.now(timezone.utc).isoformat(),
            "gpuTypeId": profile["pod"]["gpuTypeId"],
            "networkVolumeId": profile["pod"]["networkVolumeId"],
            "modelRevision": profile["model"]["revision"]}


@pytest.mark.parametrize("field,value", [
    ("maxHourlyUsd", 1.76), ("maxHourlyUsd", True),
    ("resourceCount", True), ("authorizedAtUtc", "2026-08-30T15:00:00"),
    ("authorizedAtUtc", None), ("durationMinutes", True),
])
def test_invalid_approval_cannot_reach_cloud(field, value, tmp_path):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    grant = {**approval(profile, tmp_path), field: value}
    with patch.object(core, "cli", side_effect=AssertionError("Cloud must not be called")):
        with pytest.raises(ValueError):
            controller.validate_approval(grant, profile, tmp_path)


def setup_ready(run):
    instant = datetime.now(timezone.utc)
    controller.write(run / "supervised-state.json", {
        "podId": "test-owned", "deadlineUtc": (instant + timedelta(minutes=30)).isoformat()})
    controller.write(run / "watchdog-heartbeat.json", {"atUtc": instant.isoformat()})
    controller.write(run / "profile.json", core.profile_at(core.DEFAULT_PROFILE))
    controller.write(run / "test-private.json", {"apiKey": "test-only-private-key"})
    controller.write(run / "bootstrap-start.json", {"privateKeyFile": str(run / "test-private.json")})


def test_ready_uses_private_auth_but_does_not_claim_inference(tmp_path, capsys):
    setup_ready(tmp_path)
    def server(request, timeout):
        assert request.get_header("Authorization") == "Bearer test-only-private-key"
        assert request.full_url == "http://127.0.0.1:18000/v1/models"
        assert timeout == 5
        return io.BytesIO(b'{"data":[{"id":"Veronica"}]}')
    with patch.object(controller, "urlopen", side_effect=server):
        assert controller.ready(tmp_path)
    result = core.read_json(tmp_path / "provider-ready.json")
    assert result["ready"] and not result["inferenceVerified"]
    assert "test-only-private-key" not in capsys.readouterr().out
    assert "test-only-private-key" not in json.dumps(result)


@pytest.mark.parametrize("error", [URLError("refused"), TimeoutError(), HTTPError("local", 503, "loading", {}, None)])
def test_loading_is_waiting_not_ready(tmp_path, error):
    setup_ready(tmp_path)
    with patch.object(controller, "urlopen", side_effect=error):
        assert not controller.ready(tmp_path)
    assert not core.read_json(tmp_path / "provider-ready.json")["ready"]


@pytest.mark.parametrize("reason", ["expired", "stale-watchdog", "terminated"])
def test_unsafe_run_is_rejected_before_endpoint_probe(tmp_path, reason):
    setup_ready(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    if reason == "expired":
        controller.write(tmp_path / "supervised-state.json", {"podId": "test-owned", "deadlineUtc": past})
    elif reason == "stale-watchdog":
        controller.write(tmp_path / "watchdog-heartbeat.json", {"atUtc": past})
    else:
        controller.write(tmp_path / "termination.json", {"confirmedAbsent": True})
    with patch.object(controller, "urlopen", side_effect=AssertionError("Must not probe")):
        with pytest.raises(RuntimeError):
            controller.ready(tmp_path)


def test_wrong_alias_or_auth_failure_is_fatal_not_retryable(tmp_path):
    setup_ready(tmp_path)
    with patch.object(controller, "urlopen", return_value=io.BytesIO(b'{"data":[{"id":"other"}]}')):
        with pytest.raises(RuntimeError, match="Veronica alias"):
            controller.ready(tmp_path)
    with patch.object(controller, "urlopen", side_effect=HTTPError("local", 401, "unauthorized", {}, None)):
        with pytest.raises(RuntimeError, match="HTTP 401"):
            controller.ready(tmp_path)


def test_empty_inventory_after_uncertain_creation_cannot_release_watchdog(tmp_path):
    controller.write(tmp_path / "supervised-state.json", {
        "podName": "veronica-core-uncertain", "podId": None, "creationAttempted": True})
    with patch.object(core, "cli", return_value="[]"):
        with pytest.raises(RuntimeError, match="unresolved"):
            controller.terminate(tmp_path)
    assert not (tmp_path / "termination.json").exists()


def test_late_appearing_owned_pod_is_reconciled_and_removed(tmp_path):
    state = {"podName": "veronica-core-uncertain", "podId": None, "creationAttempted": True}
    controller.write(tmp_path / "supervised-state.json", state)
    replies = [json.dumps([{"id": "late123", "name": state["podName"]}]), "", "[]"]
    with patch.object(core, "cli", side_effect=replies) as cli:
        controller.terminate(tmp_path)
    assert [call.args for call in cli.call_args_list] == [
        ("pod", "list", "--all"), ("pod", "delete", "late123"), ("pod", "list", "--all")]
    assert core.read_json(tmp_path / "supervised-state.json")["podId"] == "late123"
    assert core.read_json(tmp_path / "termination.json")["confirmedAbsent"]


def test_precreation_cancellation_releases_watchdog_without_cloud_call(tmp_path):
    controller.write(tmp_path / "supervised-state.json", {
        "creationAttempted": False, "backupShutdownAtUtc": datetime.now(timezone.utc).isoformat()})
    controller.write(tmp_path / "startup-cancelled.json", {"runId": tmp_path.name, "creationAttempted": False})
    with patch.object(core, "cli", side_effect=AssertionError("No cloud request for cancelled creation")):
        controller.watchdog(tmp_path)


def test_unresolved_previous_run_blocks_new_start_even_if_inventory_would_be_empty(tmp_path):
    old_run = tmp_path / "runs" / "older"
    new_run = tmp_path / "runs" / "newer"
    state = {"podName": "veronica-core-old", "podId": None, "creationAttempted": True}
    controller.write(old_run / "supervised-state.json", state)
    with patch.object(core, "ROOT", tmp_path):
        with pytest.raises(RuntimeError, match="confirmed closeout"):
            controller.require_closed_previous_runs(new_run)
        # A receipt for an unknown or different resource does not clear it.
        controller.write(old_run / "termination.json", {"podName": state["podName"], "podId": None, "confirmedAbsent": True})
        with pytest.raises(RuntimeError, match="confirmed closeout"):
            controller.require_closed_previous_runs(new_run)
        controller.write(old_run / "supervised-state.json", {**state, "podId": "known123"})
        controller.write(old_run / "termination.json", {"podName": state["podName"], "podId": "known123", "confirmedAbsent": True})
        controller.require_closed_previous_runs(new_run)


def test_start_lock_serializes_attempts_and_releases_after_failure(tmp_path):
    pytest.importorskip("fcntl", reason="Linux/WSL locking tested separately on the serving-control OS")
    lock = tmp_path / "start.lock"
    with pytest.raises(ValueError, match="simulated startup failure"):
        with controller.start_lock(lock):
            with pytest.raises(RuntimeError, match="Another Veronica START"):
                with controller.start_lock(lock):
                    pytest.fail("Concurrent START acquired an already-held lock")
            raise ValueError("simulated startup failure")
    with controller.start_lock(lock):
        pass
