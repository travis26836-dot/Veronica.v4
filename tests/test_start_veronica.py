"""Exercise the real PowerShell launcher without credentials or resource creation."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh")
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="PowerShell 7 is required for launcher checks")


@pytest.fixture
def launcher(tmp_path):
    # A separate project with spaces in its path verifies argument/path handling.
    # It has no WSL executable, environment, credentials, or controller code.
    root = tmp_path / "Veronica launcher fixture"
    (root / "scripts").mkdir(parents=True)
    (root / "config").mkdir()
    shutil.copyfile(ROOT / "scripts/start-veronica.ps1", root / "scripts/start-veronica.ps1")
    shutil.copyfile(ROOT / "config/runpod-core.json", root / "config/runpod-core.json")
    return root


def invoke(root, *args):
    environment = {**os.environ, "PATH": ""}
    before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(root / "scripts/start-veronica.ps1"), *map(str, args)],
        capture_output=True, text=True, timeout=20, env=environment,
    )
    after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
    assert after == before, "Dry-run or rejected input must not create local startup evidence"
    return result


def test_plan_only_works_without_wsl_or_approval_and_makes_no_changes(launcher):
    result = invoke(launcher, "-PlanOnly")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["durationMinutes"] == 60
    assert plan["maxHourlyUsd"] == 1.75
    assert plan["resourceCount"] == 1
    assert plan["gpuTypeId"] == "NVIDIA A100-SXM4-80GB"
    assert plan["resourceCreationAttempted"] is False
    assert plan["platformDeadlineEnforced"] is False
    assert plan["currentAuthorizationRequired"] is True
    assert "verify-real-windows-wrapper-responses" in plan["stages"]


def test_explicit_options_override_defaults_without_raising_saved_ceiling(launcher):
    result = invoke(launcher, "-PlanOnly", "-DurationMinutes", "120", "-MaxHourlyUsd", "1.60")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["durationMinutes"] == 120
    assert plan["maxHourlyUsd"] == 1.6
    assert plan["maximumHourlyUsd"] == 1.75


@pytest.mark.parametrize("args", [(), ("-RunDir", "RUN_PLACEHOLDER")])
def test_launch_refuses_missing_current_authorization_before_external_calls(launcher, args):
    args = tuple(str(launcher / "runs" / "new-run") if arg == "RUN_PLACEHOLDER" else arg for arg in args)
    result = invoke(launcher, *args)
    assert result.returncode != 0
    assert "Launch requires explicit RunDir and ApprovalFile" in result.stderr
    assert "WSL is required" not in result.stderr


@pytest.mark.parametrize("value", ["0", "-1", "1441", "1.5", "NaN"])
def test_invalid_duration_never_reaches_startup(launcher, value):
    result = invoke(launcher, "-PlanOnly", "-DurationMinutes", value)
    assert result.returncode != 0


@pytest.mark.parametrize("value", ["0", "-1", "1.76", "NaN", "Infinity"])
def test_invalid_or_over_budget_rate_never_reaches_startup(launcher, value):
    result = invoke(launcher, "-PlanOnly", "-MaxHourlyUsd", value)
    assert result.returncode != 0


@pytest.mark.parametrize("relative", ["outside", "runs", "runs/../outside", "runs/nested/run", "runs/name with spaces"])
def test_run_path_must_be_a_named_direct_child_of_runs(launcher, relative):
    result = invoke(launcher, "-PlanOnly", "-RunDir", launcher / relative)
    assert result.returncode != 0
    assert "RunDir must name a new direct child" in result.stderr


def test_plan_accepts_safe_run_path_without_creating_it(launcher):
    run = launcher / "runs" / "20260831-veronica-start"
    result = invoke(launcher, "-PlanOnly", "-RunDir", run)
    assert result.returncode == 0, result.stderr
    assert Path(json.loads(result.stdout)["runDir"]) == run
    assert not run.exists()


@pytest.mark.parametrize("key", ["relative/key", "/home/dubs/../private", "/tmp/key;command"])
def test_ssh_key_is_a_plain_absolute_wsl_path(launcher, key):
    result = invoke(launcher, "-PlanOnly", "-SshKey", key)
    assert result.returncode != 0
    assert "SshKey must be an absolute WSL path" in result.stderr


def test_config_cannot_silently_change_to_multiple_or_different_gpus(launcher):
    path = launcher / "config/runpod-core.json"
    profile = json.loads(path.read_text())
    profile["pod"]["gpuCount"] = 2
    path.write_text(json.dumps(profile))
    result = invoke(launcher, "-PlanOnly")
    assert result.returncode != 0
    assert "exactly one configured A100" in result.stderr


def test_wsl_timeout_reaps_linux_children_before_returning(tmp_path):
    """A harmless sleeper stands in for a slow CLI: killing wsl.exe alone fails this."""
    wsl = shutil.which("wsl.exe")
    if wsl is None:
        pytest.skip("WSL is unavailable")
    available = subprocess.run([wsl, "-e", "test", "-x", "/usr/bin/timeout"], capture_output=True, timeout=30)
    if available.returncode:
        pytest.skip("Configured WSL distribution does not provide GNU timeout")
    harness = tmp_path / "timeout-harness.ps1"
    harness.write_text(r'''
param([string]$LauncherPath, [string]$RunDirectory)
$ErrorActionPreference = 'Stop'
$resolvedRun = $RunDirectory
$script:startupExpires = [DateTimeOffset]::UtcNow.AddMinutes(1)
$ast = [Management.Automation.Language.Parser]::ParseFile($LauncherPath, [ref]$null, [ref]$null)
$definitions = $ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -in @('Assert-StartupWindow', 'Invoke-BoundedProcess')
}, $false)
foreach ($definition in $definitions) { Invoke-Expression $definition.Extent.Text }
$child = 'import os, subprocess, sys, time; p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"]); print(p.pid, flush=True); time.sleep(60)'
$result = Invoke-BoundedProcess 'wsl.exe' @('-e', 'python3', '-c', $child) 1
$result | ConvertTo-Json
''')
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(harness), "-LauncherPath", str(ROOT / "scripts/start-veronica.ps1"), "-RunDirectory", str(tmp_path / "unused-run")],
        capture_output=True, text=True, timeout=25,
    )
    assert result.returncode == 0, result.stderr
    execution = json.loads(result.stdout)
    assert execution["exitCode"] in (124, 137)
    child_pid = int(execution["output"].strip())
    check = subprocess.run(
        [wsl, "-e", "python3", "-c", "from pathlib import Path; import sys; p=Path('/proc')/sys.argv[1]/'stat'; assert not p.exists() or p.read_text().split()[2] == 'Z', 'Linux command child is still running'", str(child_pid)],
        capture_output=True, text=True, timeout=15,
    )
    assert check.returncode == 0, check.stderr
