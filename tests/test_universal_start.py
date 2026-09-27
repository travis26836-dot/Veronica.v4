"""Offline tests for the universal cross-agent Veronica start command."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from veronica_core import universal_start as start


ROOT = Path(__file__).resolve().parents[1]


def completed(command, *, stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)


def runner(*, status="online", busy=False, labels=start.DEFAULT_RUNNER_LABELS):
    return {"name": "veronica-controller", "status": status, "busy": busy,
            "labels": [{"name": label} for label in labels]}


def test_plan_is_non_mutating_and_uses_the_saved_profile_defaults(capsys):
    assert start.execute(["--plan"]) == 0
    plan = json.loads(capsys.readouterr().out)
    profile = json.loads((ROOT / "config" / "runpod-core.json").read_text())
    assert plan["command"] == "Start Veronica"
    assert plan["duration_minutes"] == profile["safety"]["defaultDurationMinutes"]
    assert plan["maximum_hourly_usd"] == profile["safety"]["maximumHourlyUsd"]
    assert plan["resource_count"] == 1
    assert plan["resource_creation_attempted"] is False
    assert plan["current_authorization_required"] is True


def test_start_requires_a_current_explicit_authorization_before_any_dispatch():
    with patch.object(start, "dispatch_to_controller", side_effect=AssertionError("must not dispatch")):
        with pytest.raises(start.UniversalStartError, match="--authorize-start"):
            start.execute(["--dispatch"])


def test_local_start_fails_closed_off_the_windows_controller():
    with patch.object(start, "is_local_controller", return_value=False):
        with pytest.raises(start.UniversalStartError, match="not the configured Windows Veronica controller"):
            start.run_on_local_controller(
                duration_minutes=60, requested_by="test", authorization_context="current owner request"
            )


def test_only_an_online_idle_fully_labeled_runner_is_eligible():
    inventory = {"runners": [
        runner(status="offline"),
        runner(busy=True),
        runner(labels=("self-hosted", "windows", "x64")),
        runner(),
        runner(labels=("self-hosted", "Windows", "X64", "veronica-controller")),
    ]}

    def fake_run(command, **kwargs):
        assert command[:3] == ["gh", "api", "repos/example/repo/actions/runners?per_page=100"]
        return completed(command, stdout=json.dumps(inventory))

    eligible = start.eligible_controller_runners("example/repo", run=fake_run)
    assert [item["name"] for item in eligible] == ["veronica-controller", "veronica-controller"]


def test_dispatch_refuses_when_no_matching_controller_is_online():
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return completed(command, stdout=json.dumps({"runners": []}))

    with pytest.raises(start.UniversalStartError, match="No online idle Veronica controller"):
        start.dispatch_to_controller(
            repository="example/repo", duration_minutes=60, requested_by="codex",
            authorization_context="owner requested one hour", run=fake_run,
        )
    assert len(calls) == 1
    assert calls[0][:3] == ["gh", "api", "repos/example/repo/actions/runners?per_page=100"]


def test_dispatch_checks_runner_then_uses_workflow_inputs_without_credentials():
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["gh", "api", "repos/example/repo/actions/runners?per_page=100"]:
            return completed(command, stdout=json.dumps({"runners": [runner()]}))
        return completed(command)

    start.dispatch_to_controller(
        repository="example/repo", duration_minutes=60, requested_by="hermes",
        authorization_context="owner requested Start Veronica for one hour", run=fake_run,
    )
    assert len(calls) == 2
    command = calls[1]
    assert command[:5] == ["gh", "workflow", "run", "start-veronica.yml", "--repo"]
    assert "example/repo" in command
    assert "authorized_start=true" in command
    assert "duration_minutes=60" in command
    assert all("RUNPOD_API_KEY" not in argument for argument in command)


@pytest.mark.parametrize("duration", [0, -1, 1441])
def test_dispatch_rejects_out_of_policy_duration_before_runner_lookup(duration):
    with patch.object(start, "dispatch_to_controller", side_effect=AssertionError("must not dispatch")):
        with pytest.raises(start.UniversalStartError, match="Duration must be"):
            start.execute(["--dispatch", "--authorize-start", "--duration-minutes", str(duration)])


def test_cli_reports_a_policy_refusal_without_a_python_traceback(capsys):
    with patch.object(start, "is_local_controller", return_value=False):
        assert start.main(["--local", "--authorize-start"]) == 2
    assert "not the configured Windows Veronica controller" in capsys.readouterr().err


def test_unqualified_windows_host_dispatches_by_default_instead_of_running_locally():
    with patch.object(start.os, "name", "nt"), patch.object(start, "is_local_controller", return_value=False), \
            patch.object(start, "dispatch_to_controller") as dispatch:
        assert start.execute(["--authorize-start"]) == 0
    dispatch.assert_called_once()


def test_workflow_preserves_controller_labels_and_does_not_use_hosted_runner():
    workflow = (ROOT / ".github/workflows/start-veronica.yml").read_text()
    assert "runs-on: [self-hosted, windows, x64, veronica-controller]" in workflow
    assert "windows-latest" not in workflow
    assert "actions/checkout@v4" in workflow
    assert "authorized_start" in workflow
    assert "plan_only" in workflow
    assert "./scripts/start-veronica.ps1 -PlanOnly" in workflow
    assert "if: ${{ always() && inputs.plan_only == false }}" in workflow


def test_windows_controller_and_one_click_adapter_delegate_to_the_checked_launcher():
    controller = (ROOT / "scripts/start-veronica-universal.ps1").read_text()
    one_click = (ROOT / "scripts/start-veronica-one-click.ps1").read_text()
    assert "approval.json" in controller
    assert "authorization-context.md" in controller
    assert "start-veronica.ps1" in controller
    assert "start-veronica-universal.ps1" in one_click
    assert "runpodctl" not in controller
    assert "pod create" not in controller.lower()
