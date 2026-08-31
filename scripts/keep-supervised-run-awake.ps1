param([Parameter(Mandatory=$true)][string]$RunDir)
$ErrorActionPreference = 'Stop'

function Read-VeronicaRunJson([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
    catch { return $null } # An incomplete/unreadable record never proves shutdown.
}

function Test-VeronicaRunRelease($State, $Termination, $Cancellation, [bool]$StateExists, [string]$RunId) {
    if ($State -and $State.runId -and $State.runId -cne $RunId) { return $false }
    if ($State -and $State.podName -and
        $Termination.confirmedAbsent -is [bool] -and $Termination.confirmedAbsent -eq $true -and
        $Termination.podName -ceq $State.podName -and
        (-not $State.podId -or $Termination.podId -ceq $State.podId)) {
        return $true
    }
    # Cancellation is safe only before a creation request was ever attempted.
    if ($Cancellation.runId -ceq $RunId -and
        $Cancellation.creationAttempted -is [bool] -and $Cancellation.creationAttempted -eq $false -and
        (-not $StateExists -or ($State.creationAttempted -is [bool] -and $State.creationAttempted -eq $false))) {
        return $true
    }
    return $false
}

function Write-VeronicaAwakeStatus([string]$Path, [string]$Status, [string]$RunId) {
    $record = @{ status = $Status; pid = $PID; runId = $RunId; atUtc = [DateTime]::UtcNow.ToString('o') }
    $temporary = "$Path.$PID.tmp"
    [IO.File]::WriteAllText($temporary, ($record | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runs')) + [IO.Path]::DirectorySeparatorChar
$resolvedRun = [IO.Path]::GetFullPath($RunDir)
if (-not $resolvedRun.StartsWith($evidenceRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Run must be beneath project runs/' }
if (-not (Test-Path -LiteralPath $resolvedRun -PathType Container)) { throw 'Create the run evidence directory before enabling sleep prevention' }
$runId = Split-Path -Leaf $resolvedRun
$statePath = Join-Path $resolvedRun 'supervised-state.json'
$statusPath = Join-Path $resolvedRun 'keep-awake-state.json'
Add-Type @'
using System.Runtime.InteropServices;
public static class VeronicaRunAwake {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
try {
    # Start before creation so the controller can verify this acknowledgment.
    # The fixed Pod deadline belongs to the watchdog. Keep this PC awake through
    # longer sessions and failed/late deletions until exact absence is confirmed.
    while ($true) {
        $stateExists = Test-Path -LiteralPath $statePath
        $state = Read-VeronicaRunJson $statePath
        $termination = Read-VeronicaRunJson (Join-Path $resolvedRun 'termination.json')
        $cancellation = Read-VeronicaRunJson (Join-Path $resolvedRun 'startup-cancelled.json')
        if (Test-VeronicaRunRelease $state $termination $cancellation $stateExists $runId) { break }
        # Temporary per-thread idle-sleep prevention; does not change power settings.
        # This cannot prevent forced sleep, power failure, or loss of connectivity.
        if ([VeronicaRunAwake]::SetThreadExecutionState([uint32]2147483651) -eq 0) { throw 'Sleep prevention failed' }
        Write-VeronicaAwakeStatus $statusPath 'ready' $runId
        Start-Sleep -Seconds 30
    }
    Write-VeronicaAwakeStatus $statusPath 'released' $runId
} catch {
    Write-VeronicaAwakeStatus $statusPath 'failed' $runId
    throw
} finally {
    [void][VeronicaRunAwake]::SetThreadExecutionState([uint32]2147483648)
}
