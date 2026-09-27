# CORE baseline and evaluator integration

- ID / parent / owner: G0 / CORE-1 / Codex coordinator with three specialized agents.
- Outcome: preserve completed milestone work, establish a reproducible local baseline, and repair evaluator defects before foundation comparison.
- Status: G0.1 completed; G0.2/G0.3 remain open, 2026-09-26.
- Authority: current root docs/PROJECT-WORKFLOW.md, docs/GOALS.md, SOURCE-OF-TRUTH section 11 and September 24 decision. Older milestone planning does not supersede these.
- Existing implementation: main 7435489 is an ancestor of milestone 168e0a2 (23 additional commits). Milestone includes Docker isolation, independent schema grading, tokenized context packets, evaluator integrity and transitive qualification evidence validation.
- Paths / claims: core-baseline-20260925 owns this packet and runs/2026-09-25-core-baseline. Implementation is isolated in .worktrees/core-finish-20260925 on agents/core-finish-20260925, based on milestone 168e0a2; agents claim disjoint files there.
- Acceptance: complete test exits; preserve pacing and isolation while correcting extraction/redaction; independent review; retain exact limitations and next actions.
- Bound: local development only; no paid compute or external publication authorized.

## Assignments

1. Baseline/evidence specialist: completed branch comparison; now preserve request pacing and fix overbroad credential redaction in evaluation.py.
2. Evaluator specialist: completed defect audit; now fix Python extraction in capability_reports.py with focused regression tests.
3. Acceptance specialist: completed section-11 and spending-policy audit; now independently review grader trust boundaries and proposed repairs.
4. Coordinator: baseline test execution, integration review, evidence and handoff.

## Baseline evidence

Fresh read-only remote verification succeeded after sandbox network restrictions: origin main is 7435489c79368e9b5311c63b0377790ecfb79f94 and milestone is 6f041197c96025b188cf800c782f0a0a4bf4fd2c. Local milestone 168e0a2 includes additional unpushed work. No push or merge was performed.

Isolated checkout contract validator and license/provenance presence checker both exited 0. The latter found all four pinned model snapshots; this is a presence check, not a new legal or model qualification decision.

Root main retains its pre-existing dirty source, tests, configuration, workflow and run evidence. Apparent deleted historical test paths also produced access-denied messages; do not classify them as confirmed deletions or remove them.

The initial uv invocation exited 2 because its cache was inaccessible. Direct project Python exited 1 because pytest's default temporary directory was inaccessible. Retrying with a fresh workspace basetemp completed successfully, exit 0: runs/2026-09-25-core-baseline/pytest-workspace.txt and pytest-workspace-exit.txt. Two tests skipped; dependency and pytest-cache warnings remain. This is wrapper/test evidence, not live model qualification.

## Current gates and policy

Foundation selection is still benchmark_required. Complete matched candidate/control results, runtime/template provenance, independent scoring and owner adjudication are required. Native tools, optional scoped memory, persona regression, external integration, recovery and controlled serverless acceptance remain open.

Current owner instructions require one A100 80 GB and a $1.75/hour ceiling. September 23's $2.09 alternate authorization was bounded to 60 minutes; it does not establish permanent authorization. Preserve historical configuration changes pending deliberate reconciliation; no start is part of this packet.

Do not merge the entire historical branch into the dirty root checkout. Do not republish historical approval files or raw private run evidence. Review exact implementation paths and preserve the current workflow before any later integration.

## G0.1 completion record

The branch/evidence comparison is complete. The isolated branch now contains a
focused evaluator packet at `a6126ef` (`fix: harden offline evaluator
qualification gates`). It adds fail-closed source extraction with provenance,
credential redaction that preserves validated usage counters, host-side native
tool/context graders, Windows-stable CP2 text-snapshot checking, and the
non-sensitive historical rejection fixture required by CP4 regression tests.

Validation in the isolated checkout:

- targeted evaluator/context suite: 98 passed, exit 0;
- broad suite excluding the pre-existing startup command-window limitation:
  310 passed, 8 skipped, exit 0;
- `git diff --check`: exit 0 before commit.

`tests/test_start_veronica.py` exceeds the current 30-second terminal command
window after its initial checks. This packet did not change startup code, so it
is recorded as a separate baseline-verification limitation rather than being
treated as a passing full-suite result.

## Next action

Resolve G0.2's A100/$1.75 policy conflict and capture G0.3's startup-suite
result. Then review and integrate the focused `a6126ef` packet through a clean,
dedicated integration branch. CORE remains open throughout these offline steps.
