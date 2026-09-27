Set-Location (Split-Path -Parent $PSScriptRoot)
Set-Location (Split-Path -Parent (Get-Location))
& uv run pytest tests/test_start_veronica.py -q *> (Join-Path $PSScriptRoot 'combined.txt')
$code = $LASTEXITCODE
Set-Content -Path (Join-Path $PSScriptRoot 'exit.txt') -Value $code
exit $code
