"""Offline enforcement of saved startup limits and local sleep-prevention release."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("runpod_core_limits", ROOT / "scripts/runpod_core.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def fake_inventory(profile, price=1.75):
    replies = {
        ("network-volume", "get", profile["pod"]["networkVolumeId"]): {
            "id": profile["pod"]["networkVolumeId"], "dataCenterId": profile["pod"]["dataCenterId"], "size": 300,
        },
        ("gpu", "list", "--include-unavailable"): [{
            "gpuId": profile["pod"]["gpuTypeId"], "securePricePerHr": price,
            "dataCenterAvailability": [{"dataCenterId": profile["pod"]["dataCenterId"], "stockStatus": "Low"}],
        }],
        ("pod", "list", "--all"): [],
        ("ssh", "list-keys"): {"keys": [{"name": "offline-test"}]},
    }

    def cli(*args):
        if args in replies:
            return json.dumps(replies[args])
        if args == ("pod", "create", "--help"):
            return "offline create help; no platform timer"
        if args == ("version",):
            return "offline-test"
        raise AssertionError(f"Unexpected or mutating command: {args}")

    return cli


def test_saved_start_defaults_are_bounded_and_supervised():
    profile = core.profile_at(core.DEFAULT_PROFILE)
    assert profile["safety"]["maximumHourlyUsd"] == 1.75
    assert profile["safety"]["defaultDurationMinutes"] == 60
    assert profile["safety"]["defaultShutdownMode"] == "supervised-with-local-backup"
    assert profile["safety"]["durationSelectionRequired"] is True
    assert profile["safety"]["terminationGuard"] == "unavailable"


@pytest.mark.parametrize("hourly", [1.75001, 2, 100])
def test_oversized_approval_fails_before_inventory(hourly):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    with patch.object(core, "cli", side_effect=AssertionError("No inventory expected")):
        with pytest.raises(ValueError, match="saved.*ceiling"):
            core.preflight(profile, hourly, 60, supervised=True)


def test_lower_saved_limit_takes_precedence_over_larger_approval():
    profile = core.profile_at(core.DEFAULT_PROFILE)
    profile["safety"]["maximumHourlyUsd"] = 1.5
    with patch.object(core, "cli", side_effect=AssertionError("No inventory expected")):
        with pytest.raises(ValueError, match="saved.*ceiling"):
            core.preflight(profile, 1.75, 60, supervised=True)


@pytest.mark.parametrize("count", [0, 2, True, 1.0, "1", None])
def test_mutated_gpu_count_fails_before_inventory(count):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    profile["pod"]["gpuCount"] = count
    with patch.object(core, "cli", side_effect=AssertionError("No inventory expected")):
        with pytest.raises(ValueError, match="exactly one GPU"):
            core.preflight(profile, 1.75, 60, supervised=True)


def test_different_gpu_cannot_substitute_for_saved_a100():
    profile = core.profile_at(core.DEFAULT_PROFILE)
    profile["pod"]["gpuTypeId"] = "NVIDIA H100 80GB HBM3"
    with pytest.raises(ValueError, match="A100-SXM4-80GB"):
        core.validate_profile_safety(profile)


@pytest.mark.parametrize("ceiling", [None, "1.75", True, 0, -1, float("nan"), float("inf")])
def test_invalid_saved_ceiling_is_rejected(ceiling):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    profile["safety"]["maximumHourlyUsd"] = ceiling
    with pytest.raises(ValueError, match="saved hourly spending ceiling"):
        core.validate_profile_safety(profile)


@pytest.mark.parametrize("field,value", [("requirePerRunApproval", False), ("allowAutomaticReplacementPod", True)])
def test_profile_cannot_drop_new_pod_approval_guards(field, value):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    profile["safety"][field] = value
    with pytest.raises(ValueError, match="fresh approval"):
        core.validate_profile_safety(profile)


@pytest.mark.parametrize("price", [None, True, False, 0, -1, "invalid", "", "NaN", "Infinity", float("nan"), float("inf"), 1.75001])
def test_unverifiable_or_over_budget_price_blocks_creation(price):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    with patch.object(core, "cli", fake_inventory(profile, price)):
        result = core.preflight(profile, 1.75, 60, supervised=True)
    assert not result["safeToCreate"]
    assert any("price" in blocker for blocker in result["blockers"])


@pytest.mark.parametrize("price", [1.59, 1.75, "1.75"])
def test_available_exact_gpu_at_or_below_saved_limit_passes_offline_preflight(price):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    with patch.object(core, "cli", fake_inventory(profile, price)):
        result = core.preflight(profile, 1.75, 180, supervised=True)
    assert result["safeToCreate"]
    assert result["savedMaximumHourlyUsd"] == 1.75
    assert result["gpuCount"] == 1
    assert not result["platformDeadlineEnforced"]


def test_windows_awake_release_requires_exact_confirmed_termination_or_safe_cancellation(tmp_path):
    """Exercise the actual PowerShell policy without touching OS power or RunPod."""
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("PowerShell required for Windows keep-awake release policy")
    state = {"runId": "test-run", "podName": "veronica-core-owned", "podId": "owned123", "creationAttempted": True,
             # Three-hour run whose deadline has passed: this does not prove deletion.
             "createdAttemptAtUtc": "2000-01-01T00:00:00Z", "deadlineUtc": "2000-01-01T03:00:00Z"}
    receipt = {"podName": state["podName"], "podId": state["podId"], "confirmedAbsent": True}
    cancel = {"runId": state["runId"], "creationAttempted": False}
    cases = [
        (state, None, None, True, False),
        (state, {}, None, True, False),
        (state, {**receipt, "confirmedAbsent": False}, None, True, False),
        (state, {**receipt, "confirmedAbsent": "true"}, None, True, False),
        (state, {**receipt, "podId": "unrelated"}, None, True, False),
        (state, {**receipt, "podName": "veronica-core-other"}, None, True, False),
        (state, receipt, None, True, True),
        (state, None, cancel, True, False),
        ({**state, "creationAttempted": False, "podId": None}, None, cancel, True, True),
        (None, None, cancel, False, True),
        (None, None, cancel, True, False),
        (None, None, {**cancel, "runId": "other-run"}, False, False),
        ({**state, "runId": "other-run"}, receipt, None, True, False),
    ]
    input_path = tmp_path / "release-cases.json"
    input_path.write_text(json.dumps([{"state": s, "receipt": r, "cancel": c, "stateExists": exists}
                                    for s, r, c, exists, _ in cases]))
    harness = tmp_path / "release-policy.ps1"
    harness.write_text("""param([string]$Source, [string]$Cases)
$ErrorActionPreference = 'Stop'
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Source, [ref]$null, [ref]$null)
$definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-VeronicaRunRelease' }, $true)
Invoke-Expression $definition.Extent.Text
$results = @(Get-Content -LiteralPath $Cases -Raw | ConvertFrom-Json | ForEach-Object {
    Test-VeronicaRunRelease $_.state $_.receipt $_.cancel $_.stateExists 'test-run'
})
ConvertTo-Json -InputObject $results -Compress
""")
    result = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File", str(harness),
                             str(ROOT / "scripts/keep-supervised-run-awake.ps1"), str(input_path)],
                            capture_output=True, text=True, timeout=30, check=True)
    assert json.loads(result.stdout) == [expected for *_, expected in cases]
