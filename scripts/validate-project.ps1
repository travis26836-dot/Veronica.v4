$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$requiredFiles = @(
    "README.md", "TODO.md", "PRINTABLE-PLAN.md",
    "docs/SOURCE-OF-TRUTH.md", "docs/BUILD-PIPELINE.md", "docs/EVIDENCE.md",
    "config/workflow.json", "config/status-states.json", "config/model-registry.json",
    "agents/core-builder.md", "agents/capability-evaluator.md", "agents/release-keeper.md",
    "src/veronica_core/app.py", "src/veronica_core/persona.py", "uv.lock"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $file) -PathType Leaf)) {
        throw "Required project artifact missing: $file"
    }
}

$workflow = Get-Content -Raw "config/workflow.json" | ConvertFrom-Json
$registry = Get-Content -Raw "config/model-registry.json" | ConvertFrom-Json
$states = Get-Content -Raw "config/status-states.json" | ConvertFrom-Json

if ($workflow.projectName -ne "Veronica.v4") { throw "Project identity mismatch." }
if ($registry.publicAlias -ne "Veronica") { throw "Public model alias changed." }
if ($states.states -notcontains "hold") { throw "Workflow hold state is missing." }
if ($registry.candidates.Count -lt 1) { throw "No model candidates registered." }

Write-Host "Project contract validated: required artifacts, JSON, identity, alias, and hold state."
