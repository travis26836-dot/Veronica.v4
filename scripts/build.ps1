$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)
& (Join-Path $PSScriptRoot "verify-local.ps1")
uv build
if ($LASTEXITCODE -ne 0) { throw "Package build failed." }
Write-Host "Verified Veronica Core package built in dist/. This packages the wrapper, not model weights."
