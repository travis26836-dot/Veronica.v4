<#
.SYNOPSIS
Create one fresh Veronica approval and invoke the checked supervised launcher.

.DESCRIPTION
This is the only paid-launch adapter used by the universal `veronica-start`
command and the GitHub controller workflow. It is intentionally Windows/WSL
specific because it owns the private SSH tunnel, local chat UI, keep-awake
helper, watchdog, and confirmed shutdown receipt. It must never be replaced
by a raw Runpod MCP create-pod call.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 1440)]
    [int]$DurationMinutes,
    [Parameter(Mandatory = $true)]
    [ValidateLength(1, 120)]
    [string]$RequestedBy,
    [Parameter(Mandatory = $true)]
    [ValidateLength(1, 500)]
    [string]$AuthorizationContext
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw 'Start the universal Veronica controller with PowerShell 7 (pwsh).'
}
if ($RequestedBy.IndexOf([char]0) -ge 0 -or $AuthorizationContext.IndexOf([char]0) -ge 0) {
    throw 'Authorization fields cannot contain NUL characters.'
}

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$profilePath = Join-Path $projectRoot 'config\runpod-core.json'
$profile = Get-Content -Raw -LiteralPath $profilePath | ConvertFrom-Json
if ($DurationMinutes -gt $profile.safety.maximumCustomDurationMinutes) {
    throw 'Requested duration exceeds the configured Veronica maximum.'
}
$hourly = [double]$profile.safety.maximumHourlyUsd
if ($profile.safety.PSObject.Properties.Name -contains 'defaultHourlyUsd' -and $null -ne $profile.safety.defaultHourlyUsd) {
    $hourly = [double]$profile.safety.defaultHourlyUsd
}
if ($profile.pod.gpuCount -ne 1) {
    throw 'The universal controller requires exactly one configured GPU.'
}

$runName = "{0}-start-veronica" -f [DateTimeOffset]::UtcNow.ToString('yyyy-MM-ddTHHmmssZ')
$runDir = Join-Path $projectRoot "runs\$runName"
if (Test-Path -LiteralPath $runDir) {
    throw 'Generated run directory already exists; wait one second and retry.'
}
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$approval = [ordered]@{
    runId = $runName
    authorizedAtUtc = [DateTimeOffset]::UtcNow.ToString('o')
    maxHourlyUsd = $hourly
    durationMinutes = $DurationMinutes
    resourceCount = 1
    gpuTypeId = $profile.pod.gpuTypeId
    networkVolumeId = $profile.pod.networkVolumeId
    modelRevision = $profile.model.revision
    shutdownMode = $profile.safety.defaultShutdownMode
}
$approvalPath = Join-Path $runDir 'approval.json'
$approval | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $approvalPath -Encoding utf8

$authorizationRecord = @"
# Universal Veronica Start Authorization

- Requested by: $RequestedBy
- Authorized at (UTC): $($approval.authorizedAtUtc)
- Duration: $DurationMinutes minutes
- Resource count: 1
- Maximum hourly price: `$$($approval.maxHourlyUsd)
- Preferred GPU: $($approval.gpuTypeId)
- Persistent volume: $($approval.networkVolumeId)
- Shutdown: $($approval.shutdownMode)

## Current owner authorization context

$AuthorizationContext

This record authorizes only this named run. The checked launcher still performs
live stock, price, volume, duplicate-Pod, SSH, watchdog, and exact-termination
checks before and after Pod creation.
"@
$authorizationRecord | Set-Content -LiteralPath (Join-Path $runDir 'authorization-context.md') -Encoding utf8

& (Join-Path $PSScriptRoot 'start-veronica.ps1') `
    -DurationMinutes $DurationMinutes `
    -MaxHourlyUsd $hourly `
    -RunDir $runDir `
    -ApprovalFile $approvalPath
if ($LASTEXITCODE -ne 0) {
    throw "The checked Veronica launcher failed with exit code $LASTEXITCODE."
}
