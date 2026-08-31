$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (Test-Path -LiteralPath ".env") {
    uv run --frozen uvicorn veronica_core.app:create_app --factory --env-file .env --host 127.0.0.1 --port 8010
} else {
    Write-Host "No .env file found. Copy .env.example to .env and review the provider settings."
    uv run --frozen uvicorn veronica_core.app:create_app --factory --host 127.0.0.1 --port 8010
}
exit $LASTEXITCODE
