$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

& (Join-Path $PSScriptRoot "validate-project.ps1")

uv sync --frozen --python 3.12
if ($LASTEXITCODE -ne 0) { throw "Dependency sync failed." }
uv run --frozen python scripts/validate_contracts.py
if ($LASTEXITCODE -ne 0) { throw "Contract schema validation failed." }
uv run --frozen python scripts/check_license_provenance.py
if ($LASTEXITCODE -ne 0) { throw "License/provenance checklist failed." }
uv run --frozen pytest
if ($LASTEXITCODE -ne 0) { throw "Local tests failed." }
uv run --frozen python -c "from veronica_core.app import create_app; app = create_app(); print(app.title, app.version)"
if ($LASTEXITCODE -ne 0) { throw "Application import failed." }
