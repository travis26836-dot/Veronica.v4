# Veronica.v4 Current State

**Status date:** 2026-09-27 (single-model live priority; no new model qualification)

**Update rule:** change this file deliberately when a newer decision is accepted; never infer authority from filesystem modification time

## Current authority

- Canonical product definition: `docs/SOURCE-OF-TRUTH.md`
- Execution checklist: `TODO.md`
- Authoritative current decision: `runs/2026-09-27-single-model-priority/decision.md`
- Last designated runtime checkpoint: `runs/2026-09-13T135326Z-start-veronica/decision.md`
- Ongoing workflow and priority: `docs/PROJECT-WORKFLOW.md`, `docs/GOALS.md`
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

- Observed checkout: `main` at `7435489`, containing the PR #5 merge.
- Existing dirty source, tests and evidence remain preserved; this is not a clean release baseline.
- Earlier milestone work exists on `feature/complete-todo-milestones`; compare it before reimplementation or integration.

## Next legitimate action

Review the clean offline integration branch, then run one bounded live Candidate
A session to verify real Veronica chat behavior. The four-model comparison is
deferred research; it is not a prerequisite for this live session. Do not infer
live runtime or global agent inactivity from the local collaboration ledger.
