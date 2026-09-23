# Veronica.v4 Current State

**Status date:** 2026-09-13

**Update rule:** change this file deliberately when a newer decision is accepted; never infer authority from filesystem modification time

## Current authority

- Canonical product definition: `docs/SOURCE-OF-TRUTH.md`
- Execution checklist: `TODO.md`
- Authoritative current decision: `runs/2026-09-13T135326Z-start-veronica/decision.md`
- Collaboration contract: `docs/AGENT-COLLABORATION.md`

## Verified checkpoint

The September 13 cold start verified early UI readiness, full model-file integrity, wrapper and direct-provider smoke results, and clean supervised Pod termination with the persistent volume retained. The Pod is recorded absent after termination.

## Important limitations

- Foundation selection remains `benchmark_required`; full T2 qualification is not complete.
- Candidate A is the single currently wired candidate; Candidate B and official controls are not integrated.
- Native tools, long-context stress, complete JSON-schema qualification, and final human review remain open.
- Saved run evidence is not proof that a model or Pod is currently running.
- Any new paid run requires a fresh explicit start request and bounded authorization.

## Collaboration workspace

- Collaboration development branch: `agents/multi-agent-collaboration`
- This branch establishes the shared Codex/Hermes/Copilot workflow before any merge to `main`.
- Existing uncommitted Veronica changes predate the collaboration bootstrap and must not be bundled into collaboration-only commits.

## Next legitimate action

Use the collaboration preflight and claim system for subsequent work. Merge this collaboration branch into `main` only after owner review. Continue core-first qualification after the collaboration workflow is accepted.
