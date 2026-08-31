param(
    [Parameter(Mandatory=$true)][string]$RunDir,
    [ValidateRange(1024,65535)][int]$Port = 8010
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runs')) + [IO.Path]::DirectorySeparatorChar
$resolvedRun = [IO.Path]::GetFullPath($RunDir)
if (-not $resolvedRun.StartsWith($evidenceRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Run must be beneath project runs/' }
if (Test-Path -LiteralPath (Join-Path $resolvedRun 'termination.json')) { throw 'The Pod has been terminated; a new authorized run is required' }
$bootstrapRecord = Get-Content -Raw -LiteralPath (Join-Path $resolvedRun 'bootstrap-start.json') | ConvertFrom-Json
$runProfile = Get-Content -Raw -LiteralPath (Join-Path $resolvedRun 'profile.json') | ConvertFrom-Json
# Capture private WSL state directly; never print it, put it in arguments, or write it into source.
$privateText = & wsl.exe -e cat -- $bootstrapRecord.privateKeyFile
if ($LASTEXITCODE -ne 0) { throw 'Cannot read this run upstream credential' }
$env:VERONICA_UPSTREAM_API_KEY = ($privateText | ConvertFrom-Json).apiKey
$privateText = $null
$env:VERONICA_UPSTREAM_BASE_URL = 'http://127.0.0.1:' + $runProfile.runtime.localTunnelPort + '/v1'
$env:VERONICA_UPSTREAM_MODEL = $runProfile.publicAlias
$env:VERONICA_PUBLIC_MODEL = $runProfile.publicAlias
$env:VERONICA_PROVIDER_TIMEOUT_SECONDS = '180'
Set-Location -LiteralPath $projectRoot
try {
    & (Join-Path $projectRoot '.venv\Scripts\python.exe') -m uvicorn veronica_core.app:create_app --factory --host 127.0.0.1 --port $Port
} finally {
    Remove-Item Env:VERONICA_UPSTREAM_API_KEY -ErrorAction SilentlyContinue
}
