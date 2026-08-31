[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Parent,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    $resolvedParent = [System.IO.Path]::GetFullPath($Parent).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolvedPath.StartsWith($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label is outside its approved location: $resolvedPath"
    }
    return $resolvedPath
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$docsRoot = Join-Path $projectRoot 'docs'
$archiveRoot = Join-Path $docsRoot 'COMPLETED\copilot-handoff-2026-08-30'
$manifestPath = Join-Path $archiveRoot 'archive-manifest.json'

$sourceRelativePaths = @(
    'CODEX-CREDIT-CHECKPOINT.md',
    'COPILOT-HANDOFF.md',
    'COPILOT-RESTART-PROMPT.md'
)

$sources = foreach ($relativePath in $sourceRelativePaths) {
    Assert-ChildPath -Path (Join-Path $docsRoot $relativePath) -Parent $docsRoot -Label 'Handoff source'
}

if (Test-Path -LiteralPath $manifestPath) {
    Write-Output '{"continue":true,"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"The Codex-to-Copilot handoff was already archived. Read docs/COMPLETED/copilot-handoff-2026-08-30/."}}'
    exit 0
}

$missing = @($sources | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
if ($missing.Count -gt 0) {
    throw "Refusing to archive a partial handoff. Missing: $($missing -join ', ')"
}

if ($DryRun) {
    [ordered]@{
        dryRun = $true
        sources = @($sources)
    } | ConvertTo-Json -Compress
    exit 0
}

New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$moved = New-Object System.Collections.Generic.List[object]

try {
    foreach ($source in $sources) {
        $destination = Assert-ChildPath -Path (Join-Path $archiveRoot (Split-Path -Leaf $source)) -Parent $archiveRoot -Label 'Archive destination'
        if (Test-Path -LiteralPath $destination) {
            throw "Archive destination already exists: $destination"
        }
        Move-Item -LiteralPath $source -Destination $destination -ErrorAction Stop
        $moved.Add([pscustomobject]@{ Source = $source; Destination = $destination })
    }

    $manifest = [ordered]@{
        archivedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
        trigger = 'VS Code Copilot SessionStart hook'
        archivedFiles = @($moved | ForEach-Object {
            [ordered]@{
                originalPath = $_.Source.Substring($projectRoot.Length + 1).Replace('\\', '/')
                archivedPath = $_.Destination.Substring($projectRoot.Length + 1).Replace('\\', '/')
            }
        })
        retainedEvidence = 'runs/2026-08-30-copilot-handoff/ is retained because run evidence stays in runs/ by project contract.'
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
}
catch {
    for ($index = $moved.Count - 1; $index -ge 0; $index--) {
        $entry = $moved[$index]
        if ((Test-Path -LiteralPath $entry.Destination) -and -not (Test-Path -LiteralPath $entry.Source)) {
            Move-Item -LiteralPath $entry.Destination -Destination $entry.Source -ErrorAction SilentlyContinue
        }
    }
    throw
}

Write-Output '{"continue":true,"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Codex-to-Copilot handoff archived to docs/COMPLETED/copilot-handoff-2026-08-30/. Read it, then continue with Candidate A artifact integrity only."}}'
