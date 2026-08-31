<#
Prepare and start one explicitly authorized supervised RunPod session.
Use -PlanOnly to inspect saved defaults without WSL, network access, or writes.
The calling agent must remain engaged until exact Pod termination is confirmed.
#>
[CmdletBinding()]
param(
    [switch]$PlanOnly,
    [string]$DurationMinutes,
    [Nullable[double]]$MaxHourlyUsd,
    [string]$RunDir,
    [string]$ApprovalFile,
    [string]$SshKey = '/home/dubs/.ssh/id_ed25519_runpod_noirworks'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$profilePath = Join-Path $projectRoot 'config/runpod-core.json'
$profile = Get-Content -Raw -LiteralPath $profilePath | ConvertFrom-Json
$minutes = [int]$profile.safety.defaultDurationMinutes
if ($DurationMinutes) {
    if ($DurationMinutes -notmatch '^[0-9]+$' -or -not [int]::TryParse($DurationMinutes, [ref]$minutes)) {
        throw 'DurationMinutes must be a positive whole number within the configured duration limit.'
    }
}
$hourly = if ($null -eq $MaxHourlyUsd) { [double]$profile.safety.maximumHourlyUsd } else { [double]$MaxHourlyUsd }
if ($minutes -lt 1 -or $minutes -gt $profile.safety.maximumCustomDurationMinutes) {
    throw 'DurationMinutes must be a positive whole number within the configured duration limit.'
}
if ([double]::IsNaN($hourly) -or [double]::IsInfinity($hourly) -or $hourly -le 0 -or $hourly -gt $profile.safety.maximumHourlyUsd) {
    throw 'MaxHourlyUsd must be positive and cannot exceed the configured hourly ceiling.'
}
if ($profile.pod.gpuCount -ne 1 -or $profile.pod.gpuTypeId -ne 'NVIDIA A100-SXM4-80GB') {
    throw 'START requires exactly one configured A100 80 GB GPU.'
}
if ($SshKey -notmatch '^/[A-Za-z0-9_./-]+$' -or $SshKey.Split('/') -contains '..') {
    throw 'SshKey must be an absolute WSL path without parent traversal.'
}

# A single new child beneath runs/ is also the remote evidence directory name.
# Refuse junctions/symlinks in existing ancestry rather than relying on lexical paths.
function Resolve-RunDirectory([string]$Value) {
    $path = [IO.Path]::GetFullPath($Value)
    $runs = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runs'))
    if ([IO.Path]::GetDirectoryName($path) -ne $runs -or [IO.Path]::GetFileName($path) -notmatch '^[A-Za-z0-9_-]+$') {
        throw 'RunDir must name a new direct child directory beneath this project runs/.'
    }
    $ancestor = $path
    while ($ancestor) {
        if (Test-Path -LiteralPath $ancestor) {
            $item = Get-Item -Force -LiteralPath $ancestor
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or -not $item.PSIsContainer) {
                throw 'RunDir ancestry must contain only ordinary directories, without symlinks or junctions.'
            }
        }
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
    return $path
}
$resolvedRun = if ($RunDir) { Resolve-RunDirectory $RunDir } else { $null }
if ($ApprovalFile -and -not (Test-Path -LiteralPath $ApprovalFile -PathType Leaf)) { throw 'ApprovalFile does not exist.' }
$stages = @('validate-current-authorization-and-local-prerequisites', 'prepare-pinned-model-provenance',
    'confirm-windows-sleep-prevention', 'check-price-stock-volume-and-create-one-pod', 'wait-for-ssh',
    'validate-persistent-model-and-start-server', 'open-loopback-ssh-tunnel', 'start-windows-chat-wrapper',
    'report-ui-ready-with-model-checks-pending', 'wait-for-authenticated-model-alias',
    'verify-real-provider-responses', 'capture-model-and-runtime-evidence',
    'verify-real-windows-wrapper-responses', 'report-chat-url-and-fixed-shutdown-deadline')
if ($PlanOnly) {
    [ordered]@{
        command = 'Start Veronica'; planOnly = $true; resourceCreationAttempted = $false
        durationMinutes = $minutes; maxHourlyUsd = $hourly; maximumHourlyUsd = $profile.safety.maximumHourlyUsd
        resourceCount = 1; gpuTypeId = $profile.pod.gpuTypeId; networkVolumeId = $profile.pod.networkVolumeId
        dataCenterId = $profile.pod.dataCenterId; modelRevision = $profile.model.revision
        shutdownMode = $profile.safety.defaultShutdownMode; platformDeadlineEnforced = $false
        currentAuthorizationRequired = $true; runDir = $resolvedRun; stages = $stages
        durationSelectionRequired = $profile.safety.durationSelectionRequired
    } | ConvertTo-Json -Depth 5
    return
}
if (-not $resolvedRun -or -not $ApprovalFile) {
    throw 'Launch requires explicit RunDir and ApprovalFile recording current user authorization; use -PlanOnly to inspect defaults.'
}
$resolvedApproval = (Resolve-Path -LiteralPath $ApprovalFile).Path
foreach ($artifact in @('supervised-state.json', 'expected-model-manifest.json', 'bootstrap-start.json', 'keep-awake-state.json', 'startup-ui-ready.json', 'startup-ready.json', 'startup-cancelled.json', 'termination.json')) {
    if (Test-Path -LiteralPath (Join-Path $resolvedRun $artifact)) { throw 'This run already contains startup evidence; use a new run and authorization. Creation is never retried.' }
}
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'The local wrapper environment is missing; run scripts/build.ps1 before START.' }
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { throw 'WSL is required for RunPod credentials, SSH, and the local watchdog.' }
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Run START with PowerShell 7 (pwsh); argument-safe process orchestration requires it.' }
$shell = (Get-Process -Id $PID).Path
$script:startupExpires = [DateTimeOffset]::UtcNow.AddMinutes([Math]::Min(30, $minutes))

function Assert-StartupWindow {
    if ([DateTimeOffset]::UtcNow -ge $script:startupExpires) { throw 'Startup exceeded its bounded window.' }
    $statePath = Join-Path $resolvedRun 'supervised-state.json'
    if (Test-Path -LiteralPath $statePath) {
        $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
        if ([DateTimeOffset]::UtcNow -ge [DateTimeOffset]::Parse($state.deadlineUtc)) { throw 'The approved shutdown deadline was reached during startup.' }
    }
    if (Test-Path -LiteralPath (Join-Path $resolvedRun 'termination.json')) { throw 'This run has a termination receipt; startup cannot continue.' }
}

# Pass every argument separately; never interpolate paths or credentials into a shell command.
function Invoke-BoundedProcess([string]$Executable, [string[]]$Arguments, [int]$TimeoutSeconds = 120, [switch]$Cleanup) {
    $isWsl = $Executable -eq 'wsl.exe'
    if (-not $Cleanup) { Assert-StartupWindow }
    if ($isWsl) {
        if ($Arguments[0] -ne '-e') { throw 'WSL calls must use direct executable argument arrays.' }
        $linuxTimeout = $TimeoutSeconds
        if (-not $Cleanup) {
            $linuxTimeout = [Math]::Min($linuxTimeout, [Math]::Floor(($script:startupExpires - [DateTimeOffset]::UtcNow).TotalSeconds))
            $currentStateFile = Join-Path $resolvedRun 'supervised-state.json'
            if (Test-Path -LiteralPath $currentStateFile) {
                $currentState = Get-Content -Raw -LiteralPath $currentStateFile | ConvertFrom-Json
                $linuxTimeout = [Math]::Min($linuxTimeout, [Math]::Floor(([DateTimeOffset]::Parse($currentState.deadlineUtc) - [DateTimeOffset]::UtcNow).TotalSeconds))
            }
        }
        if ($linuxTimeout -lt 1) { throw 'No approved startup time remains.' }
        # timeout owns the Linux process group, including in-flight CLI children.
        # Detached watchdogs deliberately survive. Wait for timeout to reap the
        # command before cleanup; merely killing wsl.exe can leave Linux running.
        $Arguments = @('-e', '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', "${linuxTimeout}s") + $Arguments[1..($Arguments.Count - 1)]
        $TimeoutSeconds = [int]$linuxTimeout + 10
    }
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    [void]$process.Start()
    $output = $process.StandardOutput.ReadToEndAsync()
    $errors = $process.StandardError.ReadToEndAsync()
    $expires = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    try {
        while (-not $process.WaitForExit(500)) {
            if (-not $Cleanup -and -not $isWsl) { Assert-StartupWindow }
            if ([DateTimeOffset]::UtcNow -ge $expires) { throw 'A startup operation timed out.' }
        }
        return @{ exitCode = $process.ExitCode; output = $output.GetAwaiter().GetResult(); error = $errors.GetAwaiter().GetResult() }
    } finally {
        if (-not $process.HasExited) { $process.Kill() }
        $process.Dispose()
    }
}
function Invoke-Required([string]$Executable, [string[]]$Arguments, [int]$TimeoutSeconds = 120) {
    $result = Invoke-BoundedProcess $Executable $Arguments $TimeoutSeconds
    if ($result.exitCode -ne 0) { throw "Startup command failed (exit $($result.exitCode)); inspect the run evidence. $($result.error.Trim())" }
    return $result.output.Trim()
}
function Invoke-Controller([string]$Command, [int]$TimeoutSeconds = 120) {
    Invoke-Required 'wsl.exe' @('-e', 'python3', '-B', $script:wslController, $Command, '--run-dir', $script:wslRun) $TimeoutSeconds
}
function Test-OwnedWrapperListener {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8010 -ErrorAction SilentlyContinue)
    if (-not $listeners) { return $false }
    foreach ($listener in $listeners) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
        $ancestor = $owner
        $belongsToWrapper = $false
        # Windows venv python.exe is a redirector; the listener may belong to
        # its base-Python child. Require an actual chain to our live wrapper.
        for ($depth = 0; $null -ne $ancestor -and $depth -lt 4; $depth++) {
            if ($ancestor.ParentProcessId -eq $wrapper.Id) { $belongsToWrapper = $true; break }
            $ancestor = Get-CimInstance Win32_Process -Filter "ProcessId = $($ancestor.ParentProcessId)"
        }
        if (-not $owner -or -not $belongsToWrapper -or $wrapper.HasExited -or $owner.CommandLine -notmatch 'veronica_core\.app:create_app') {
            throw 'Port 8010 is not owned by the wrapper launched for this run; refusing to verify an unrelated service.'
        }
    }
    return $true
}
function Write-Record([string]$Name, $Value) {
    $destination = Join-Path $resolvedRun $Name
    $temporary = $destination + '.tmp'
    $Value | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 -LiteralPath $temporary
    Move-Item -Force -LiteralPath $temporary -Destination $destination
}

# Reuse the controller's authorization contract, without invoking its network APIs.
$validator = @'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import runpod_core as core
import supervised_runpod as controller
profile = core.profile_at(sys.argv[2])
run = core.evidence_directory(sys.argv[3])
approval = core.read_json(sys.argv[4])
controller.validate_approval(approval, profile, run)
if approval['durationMinutes'] != int(sys.argv[5]) or approval['maxHourlyUsd'] != float(sys.argv[6]):
    raise ValueError('Selected duration and hourly limit must exactly match the current approval')
'@
$hourlyText = $hourly.ToString('R', [Globalization.CultureInfo]::InvariantCulture)
[void](Invoke-Required $python @('-B', '-c', $validator, $PSScriptRoot, $profilePath, $resolvedRun, $resolvedApproval, "$minutes", $hourlyText))
if (Get-NetTCPConnection -State Listen -LocalPort 8010 -ErrorAction SilentlyContinue) {
    throw 'Local port 8010 is already occupied. Identify and stop that wrapper explicitly before START; no Pod has been created.'
}
# Check the Windows runtime now, before any paid creation or local helper launch.
[void](Invoke-Required $python @('-B', '-c', 'import uvicorn; import veronica_core.app'))
$portProbe = 'import socket, sys; s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1) if hasattr(socket, "SO_EXCLUSIVEADDRUSE") else None; s.bind(("127.0.0.1", int(sys.argv[1]))); s.close()'
[void](Invoke-Required $python @('-B', '-c', $portProbe, "$($profile.runtime.localTunnelPort)"))
$script:wslRun = Invoke-Required 'wsl.exe' @('-e', 'wslpath', '-a', '-u', $resolvedRun)
$wslProfile = Invoke-Required 'wsl.exe' @('-e', 'wslpath', '-a', '-u', $profilePath)
$wslApproval = Invoke-Required 'wsl.exe' @('-e', 'wslpath', '-a', '-u', $resolvedApproval)
$wslCore = Invoke-Required 'wsl.exe' @('-e', 'wslpath', '-a', '-u', (Join-Path $PSScriptRoot 'runpod_core.py'))
$script:wslController = Invoke-Required 'wsl.exe' @('-e', 'wslpath', '-a', '-u', (Join-Path $PSScriptRoot 'supervised_runpod.py'))
[void](Invoke-Required 'wsl.exe' @('-e', 'test', '-f', $SshKey))
[void](Invoke-Required 'wsl.exe' @('-e', 'test', '-f', ($SshKey + '.pub')))
# Match core.cli's installed CLI fallback instead of depending on a login shell PATH.
[void](Invoke-Required 'wsl.exe' @('-e', 'python3', '-B', '-c', 'import os, shutil; from pathlib import Path; assert shutil.which("ssh"), "WSL SSH is missing"; cli = shutil.which("runpodctl") or str(Path.home()/".local/bin/runpodctl"); assert Path(cli).is_file() and os.access(cli, os.X_OK), "WSL runpodctl is missing"'))
[void](Invoke-Required 'wsl.exe' @('-e', 'python3', '-B', '-c', $portProbe, "$($profile.runtime.localTunnelPort)"))

$awake = $null
$wrapper = $null
try {
    Write-Host 'Preparing the pinned model record; no Pod has been created yet.'
    [void](Invoke-Required 'wsl.exe' @('-e', 'python3', '-B', $wslCore, 'prepare', '--profile', $wslProfile, '--run-dir', $script:wslRun) 600)
    # Start-Process safely handles fixed PowerShell arguments; quoted paths contain no quotes.
    $helperArguments = @('-NoProfile', '-File', ('"' + (Join-Path $PSScriptRoot 'keep-supervised-run-awake.ps1') + '"'), '-RunDir', ('"' + $resolvedRun + '"'))
    $awake = Start-Process -FilePath $shell -ArgumentList $helperArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $resolvedRun 'keep-awake.stdout.log') -RedirectStandardError (Join-Path $resolvedRun 'keep-awake.stderr.log')
    $awakeLimit = [DateTimeOffset]::UtcNow.AddSeconds(20)
    do {
        Assert-StartupWindow
        if ($awake.HasExited -or [DateTimeOffset]::UtcNow -ge $awakeLimit) { throw 'Windows sleep prevention did not acknowledge readiness; no Pod was created.' }
        Start-Sleep -Milliseconds 250
        $awakeRecord = Join-Path $resolvedRun 'keep-awake-state.json'
        $ready = if (Test-Path -LiteralPath $awakeRecord) { Get-Content -Raw -LiteralPath $awakeRecord | ConvertFrom-Json } else { $null }
    } until ($null -ne $ready -and $ready.status -eq 'ready' -and $ready.pid -eq $awake.Id)
    Write-Host 'Checking current price and availability, then creating the single authorized Pod.'
    [void](Invoke-Required 'wsl.exe' @('-e', 'python3', '-B', $wslCore, 'start', '--profile', $wslProfile, '--run-dir', $script:wslRun, '--approval-file', $wslApproval, '--ssh-key', $SshKey, '--supervised') 600)
    Write-Host 'Waiting for SSH, then validating the persistent model and starting its server.'
    $sshLimit = [DateTimeOffset]::UtcNow.AddMinutes(5)
    do {
        Assert-StartupWindow
        $inspection = Invoke-BoundedProcess 'wsl.exe' @('-e', 'python3', '-B', $script:wslController, 'inspect', '--run-dir', $script:wslRun) 90
        if ($inspection.exitCode -eq 0) { break }
        if ([DateTimeOffset]::UtcNow -ge $sshLimit) { throw 'The owned Pod did not become SSH-ready within five minutes.' }
        Start-Sleep -Seconds 5
    } while ($true)
    [void](Invoke-Controller 'bootstrap')
    [void](Invoke-Controller 'tunnel')
    # Show the actual chat UI while model validation/loading and response tests
    # continue. Listener readiness is deliberately not inference verification.
    Assert-StartupWindow
    if (Get-NetTCPConnection -State Listen -LocalPort 8010 -ErrorAction SilentlyContinue) { throw 'Port 8010 became occupied during startup; refusing to replace an unknown process.' }
    $wrapperArguments = @('-NoProfile', '-File', ('"' + (Join-Path $PSScriptRoot 'start-supervised-wrapper.ps1') + '"'), '-RunDir', ('"' + $resolvedRun + '"'))
    $wrapper = Start-Process -FilePath $shell -ArgumentList $wrapperArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $resolvedRun 'wrapper.stdout.log') -RedirectStandardError (Join-Path $resolvedRun 'wrapper.stderr.log')
    Write-Record 'wrapper-process.json' @{ pid = $wrapper.Id; startedAtUtc = $wrapper.StartTime.ToUniversalTime().ToString('o'); script = (Join-Path $PSScriptRoot 'start-supervised-wrapper.ps1'); runId = [IO.Path]::GetFileName($resolvedRun) }
    $wrapperLimit = [DateTimeOffset]::UtcNow.AddSeconds(30)
    do {
        Assert-StartupWindow
        if ($wrapper.HasExited -or [DateTimeOffset]::UtcNow -ge $wrapperLimit) { throw 'The Windows chat wrapper did not become ready.' }
        Start-Sleep -Milliseconds 500
    } until (Test-OwnedWrapperListener)
    Write-Record 'startup-ui-ready.json' @{ uiReady = $true; inferenceVerified = $false; checksPending = $true; atUtc = [DateTimeOffset]::UtcNow.ToString('o'); chatUrl = 'http://127.0.0.1:8010'; runId = [IO.Path]::GetFileName($resolvedRun) }
    Write-Host 'Chat UI is available at http://127.0.0.1:8010. Open it now; model loading and verification continue in the background.'
    Write-Host 'Waiting for the authenticated model endpoint; the UI remains available.'
    do {
        Assert-StartupWindow
        if (-not (Test-OwnedWrapperListener)) { throw 'The Windows chat wrapper exited during model startup.' }
        $provider = Invoke-BoundedProcess 'wsl.exe' @('-e', 'python3', '-B', $script:wslController, 'ready', '--run-dir', $script:wslRun) 20
        if ($provider.exitCode -eq 0) { break }
        if ($provider.exitCode -ne 2) { throw 'Provider readiness failed; inspect provider-ready.json and controller evidence.' }
        Start-Sleep -Seconds 5
    } while ($true)
    Write-Host 'Verifying real provider responses and capturing model evidence; chat remains available.'
    [void](Invoke-Controller 'verify' 950)
    [void](Invoke-Controller 'evidence' 180)
    Write-Host 'Verifying real responses through the Windows chat wrapper.'
    [void](Invoke-Required $python @('-B', (Join-Path $PSScriptRoot 'runpod_core.py'), 'verify', '--profile', $profilePath, '--run-dir', $resolvedRun, '--wrapper', '--base-url', 'http://127.0.0.1:8010/v1') 950)
    Assert-StartupWindow
    if (-not (Test-OwnedWrapperListener)) { throw 'The owned Windows wrapper exited during response verification.' }
    $finalState = Get-Content -Raw -LiteralPath (Join-Path $resolvedRun 'supervised-state.json') | ConvertFrom-Json
    $result = [ordered]@{ ready = $true; atUtc = [DateTimeOffset]::UtcNow.ToString('o'); chatUrl = 'http://127.0.0.1:8010'; podId = $finalState.podId; deadlineUtc = $finalState.deadlineUtc; actualHourlyUsd = $finalState.actualHourlyUsd; shutdownMode = 'supervised-with-local-backup'; platformDeadlineEnforced = $false; runDir = $resolvedRun; evidenceFile = (Join-Path $resolvedRun 'startup-ready.json') }
    Write-Record 'startup-ready.json' $result
    $result | ConvertTo-Json -Depth 5
} catch {
    $failure = $_
    $stateFile = Join-Path $resolvedRun 'supervised-state.json'
    $state = if (Test-Path -LiteralPath $stateFile) { Get-Content -Raw -LiteralPath $stateFile | ConvertFrom-Json } else { $null }
    if ($null -eq $state -or ($state.creationAttempted -is [bool] -and $state.creationAttempted -eq $false)) {
        if (Test-Path -LiteralPath $resolvedRun -PathType Container) {
            Write-Record 'startup-cancelled.json' @{ runId = [IO.Path]::GetFileName($resolvedRun); creationAttempted = $false; atUtc = [DateTimeOffset]::UtcNow.ToString('o') }
        }
    } else {
        Write-Warning 'Startup failed after creation was attempted. Terminating only this run owned Pod; preserving persistent storage.'
        try {
            $cleanup = Invoke-BoundedProcess 'wsl.exe' @('-e', 'python3', '-B', $script:wslController, 'terminate', '--run-dir', $script:wslRun) 180 -Cleanup
        } catch {
            $cleanup = @{ exitCode = -1 }
        }
        $receiptFile = Join-Path $resolvedRun 'termination.json'
        $receipt = if (Test-Path -LiteralPath $receiptFile) { Get-Content -Raw -LiteralPath $receiptFile | ConvertFrom-Json } else { $null }
        if ($cleanup.exitCode -ne 0 -or $null -eq $receipt -or $receipt.confirmedAbsent -ne $true -or $receipt.podName -ne $state.podName -or ($state.podId -and $receipt.podId -ne $state.podId)) {
            throw "START failed and exact Pod termination is NOT confirmed. Keep this computer awake and connected, inspect $resolvedRun, and terminate the owned Pod. Original failure: $($failure.Exception.Message)"
        }
    }
    # Only a process object created by this invocation can be stopped here.
    if ($null -ne $wrapper -and -not $wrapper.HasExited) { $wrapper.Kill($true) }
    throw $failure
}
