# Handoff: rubric-routing-contract-20260923

**Status:** completed

**Agent:** codex / codex-desktop

**Started:** 2026-09-23T17:58:21Z

**Ended:** 2026-09-23T18:01:03Z

## Scope

Define evidence-backed rubric score routing for CORE improvement decisions

## Files changed

- `docs/evals/RUBRIC-ROUTING.md`

## Tests

- git diff --check -- docs/evals/RUBRIC-ROUTING.md
- .venv\\Scripts\\python.exe scripts/evaluate_veronica.py validate --tier extended

## Evidence

- `docs/evals/RUBRIC-ROUTING.md`
- `suite_sha256=ce1644f045953b66cd9b98883570d7404cac832cf06a6085453259af86aecf90`

## Limitations

- Routing contract is proposed; it does not implement automatic scoring or authorize training/paid compute

## Ruled out

- None recorded.

## Next safe action

Use the contract to adjudicate current live failures and implement evaluator fixes #6 and #7 once those paths are available
