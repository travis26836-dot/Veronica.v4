<#
Create a fresh bounded approval and invoke the checked Veronica launcher.

This script is intentionally manual-only: it is suitable for a Run-button task,
but it must never be configured with runOn=worktreeCreated.

CLEANUP AFTER REVISIONS: Added explicit stale port/process kill for 8010/18000/4173
and veronica python processes to prevent "already running" or port conflicts from
prior failed starts or revisions. This ensures clean launch every time.
#>
[CmdletBinding()]
param(
    [ValidateRange(1, 1440)]
    [int]$DurationMinutes = 120
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$profilePath = Join-Path $projectRoot 'config\\runpod-core.json'
$profile = Get-Content -Raw -LiteralPath $profilePath | ConvertFrom-Json

# Cleanup stale local wrappers/tunnels from previous revisions or failed starts (ports 8010 UI, 18000 tunnel, 4173 old)
Write-Host "Cleaning stale local ports and processes..."
$portsToClean = @(8010, 18000, 4173)
foreach ($port in $portsToClean) {
    Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        $pid = $_.OwningProcess
        if ($pid) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "Killed listener on port $port (PID $pid)"
        }
    }
}
# Kill any lingering python veronica processes (local or wrapper)
Get-Process -Name python* -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'veronica' -or $_.Path -match 'veronica' } | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Killed stale veronica python (PID $($_.Id))"
}

$runName = "{0}-start-veronica" -f [DateTimeOffset]::UtcNow.ToString('yyyy-MM-ddTHHmmssZ')
$runDir = Join-Path $projectRoot "runs\\$runName"

if (Test-Path -LiteralPath $runDir) {
    throw "The generated run directory already exists; wait one second and try again."
}

New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$approval = [ordered]@{
    runId = $runName
    authorizedAtUtc = [DateTimeOffset]::UtcNow.ToString('o')
    maxHourlyUsd = [double]$profile.safety.maximumHourlyUsd
    durationMinutes = $DurationMinutes
    resourceCount = 1
    gpuTypeId = $profile.pod.gpuTypeId
    networkVolumeId = $profile.pod.networkVolumeId
    modelRevision = $profile.model.revision
    shutdownMode = $profile.safety.defaultShutdownMode
}
$approvalPath = Join-Path $runDir 'approval.json'
$approval | ConvertTo-Json | Set-Content -LiteralPath $approvalPath -Encoding utf8

@"
# One-click authorization

The owner launched the manual `Start Veronica - 2 hours (PAID)` task.
This task creates one fresh approval for this run only. The checked launcher
still enforces the configured hourly ceiling, GPU/volume ownership, stock
availability, local safety checks, and bounded shutdown deadline.
"@ | Set-Content -LiteralPath (Join-Path $runDir 'authorization-context.md') -Encoding utf8

& (Join-Path $PSScriptRoot 'start-veronica.ps1') `
    -DurationMinutes $DurationMinutes `
    -RunDir $runDir `
    -ApprovalFile $approvalPath
if ($LASTEXITCODE -ne 0) {
    throw "The checked Veronica launcher failed with exit code $LASTEXITCODE."
}