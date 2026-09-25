# Handoff: installed-foundation-identity-20260925

**Status:** completed

**Agent:** other / manus

**Started:** 2026-09-25T21:42:01Z

**Ended:** 2026-09-25T22:01:32Z

## Scope

Replace legacy Candidate A/B terminology with the exact installed RunPod foundation identity; convert active qualification configuration to a one-model baseline; update repository documents and tests.

## Files changed

- `.env.example`
- `AGENTS.md`
- `README.md`
- `TODO.md`
- `config/foundation-baseline-inputs.template.json`
- `config/foundation-baseline-qualification.json`
- `config/model-registry.json`
- `config/runpod-core.json`
- `config/runpod-foundation-baseline.json`
- `config/schemas/model-record.schema.json`
- `runs/2026-09-25-installed-foundation-identity/decision.md`
- `src/veronica_core/config.py`
- `src/veronica_core/contracts.py`
- `src/veronica_core/qualification.py`
- `tests/test_qualification.py`
- `tests/test_supervised_start.py`

## Tests

- uv run python scripts/verify_t2_qualification.py protocol
- uv run python -m pytest -q

## Evidence

- `runs/2026-09-25-installed-foundation-identity/outputs/offline-validation.md`

## Limitations

- No live inference or paid GPU start occurred; foundation remains unqualified.
- 31 PowerShell launcher tests were skipped because pwsh is unavailable in this Linux sandbox.

## Ruled out

- Starting RunPod from the Manus sandbox: no RunPod CLI, credentials, or SSH key are present.

## Next safe action

Pull docs/installed-foundation-identity on the Windows/WSL machine and START Veronica for 60 minutes at $1.75/hour using the checked launcher; collect the frozen one-model baseline. Do not treat smoke chat as qualification.
