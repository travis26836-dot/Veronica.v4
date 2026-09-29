# Handoff: launch-policy-20260926

**Status:** completed

**Agent:** codex / codex-desktop

**Started:** 2026-09-26T09:32:30Z

**Ended:** 2026-09-26T09:35:23Z

## Scope

Reconcile RunPod profiles and documented start ceiling with current A100 1.75 USD policy

## Files changed

- `config/runpod-core.json`
- `config/runpod-t2-alternative.json`
- `docs/STARTING-PROCEDURE.md`

## Tests

- uv run python profile safety validation for both RunPod profiles
- powershell -ExecutionPolicy Bypass -File scripts/start-veronica.ps1 -PlanOnly
- powershell -ExecutionPolicy Bypass -File scripts/start-veronica.ps1 -PlanOnly -ProfilePath config/runpod-t2-alternative.json
- git -c core.whitespace=cr-at-eol diff --check -- config/runpod-core.json config/runpod-t2-alternative.json docs/STARTING-PROCEDURE.md

## Evidence

- `config/runpod-core.json`
- `config/runpod-t2-alternative.json`
- `docs/STARTING-PROCEDURE.md`

## Limitations

- Live stock and price were deliberately not queried; no paid Pod was started.
- RunPod test expectations are owned by startup-policy-test-update-20260926.

## Ruled out

- Retaining the prior 2.09 USD/hour policy because it conflicts with the current 1.75 USD/hour project instruction.

## Next safe action

Startup-policy-test-update-20260926 should update and capture the RunPod/startup suite; then integrate the reviewed packet on a clean branch.
