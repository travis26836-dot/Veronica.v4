<#
Create a fresh bounded approval through the universal Veronica controller.

This script is intentionally manual-only for the VS Code Run button. It keeps
its two-hour default but delegates all approval creation and checked launching
to start-veronica-universal.ps1 so every entry point shares the same contract.
#>
[CmdletBinding()]
param(
    [ValidateRange(1, 1440)]
    [int]$DurationMinutes = 120
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

& (Join-Path $PSScriptRoot 'start-veronica-universal.ps1') `
    -DurationMinutes $DurationMinutes `
    -RequestedBy 'VS Code Agents Run button' `
    -AuthorizationContext "The owner launched the manual Start Veronica paid task for $DurationMinutes minutes."
if ($LASTEXITCODE -ne 0) {
    throw "The universal Veronica controller failed with exit code $LASTEXITCODE."
}
