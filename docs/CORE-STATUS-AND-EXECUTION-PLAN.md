# Veronica Core: verified status and execution plan

Date: 2026-09-22  
Owner: Travis  
Branch: `feature/complete-todo-milestones`

This is the working answer to two questions: what is actually finished, and
what must happen before Veronica Core can be called finished. `TODO.md` remains
the authoritative checklist; this document supplies the order, evidence, and
checkpoint rules.

## Current conclusion

The repository is past scaffolding and local safety work. It has a working
wrapper, UI, collaboration process, isolated code-evaluation path, and the
first schema qualification gate. The Core is **not finished** because no
foundation model has yet passed the complete independent qualification, and
persona, tools, memory, external integration, recovery, and controlled release
still require evidence.

The next action is **M1 CP2: actual-token context packet**. It is local work.
It does not require Docker to be restarted or a paid Pod to be created. A Pod
is considered only after CP4, during M2, with fresh bounded authorization.

## Verified accomplishments

These items have repository evidence and may be treated as completed
foundations:

| Area | Verified result | Evidence |
| --- | --- | --- |
| Product contract | Source-of-truth, TODO, current-state, and CREATED workflow are defined and linked. | `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, `docs/CURRENT-STATE.md`, `docs/CREATED-WORKING-SYSTEM.md` |
| Core wrapper | Configurable upstream model, stable `Veronica` alias, local API/UI, modes, health/capability reporting, non-stream and SSE paths exist. | `src/`, local test suite, earlier run records |
| First live smoke | Candidate A was started, model files were checked, wrapper/direct-provider smoke was recorded, and the resource was terminated. | `runs/2026-09-13T135326Z-start-veronica/decision.md` |
| Collaboration | Collaboration workflow was integrated locally into this milestone branch. | commit `e659d0c`, `runs/2026-09-17-collaboration-integration/decision.md` |
| Execution safety | Generated-code evaluation is fail-closed, host-scored, pinned, resource-limited, network/mount restricted, and Docker-tested. | commits `772c5f4`, `3f14e8a`; `runs/2026-09-17-container-sandbox/decision.md` |
| Docker recovery | The sandbox was rechecked after the reported Docker crash; targeted and full tests passed and no sandbox containers remained. | sandbox validation run and test output |
| CP1 schema gate | Strict JSON parsing, duplicate/nonfinite rejection, exact keys, native tool-call shape checks, no-tool checks, negative fixtures, and capability-report integration are implemented. | commit `479489f`; `runs/2026-09-22-cp1-schema-gate/decision.md`; `tests/test_schema_gate.py` |
| Local validation | Full `uv run pytest tests -q -r a` passed with only existing platform-specific skips; the T2 protocol verifier still correctly reports `foundation_qualified=false`. | CP1 run evidence |

## Completed foundations that are not product qualification

The following are useful but must not be counted as Core completion:

- A reachable service, `/v1/models`, a nonempty response, a mock provider, or
  a passing wrapper test does not prove model capability.
- The September 13 Candidate A run is a startup and smoke checkpoint, not T2
  qualification or a model-selection decision.
- CP1 proves that evaluator outputs can be checked. It does not prove that a
  foundation model emits valid schemas under real prompts.
- The collaboration PR is integrated locally. Remote PR status, pushing, and
  merging into `main` are separate repository actions and remain owner-led.
- Existing commits are progress checkpoints; they are not evidence that every
  older TODO checkbox is satisfied.

## Remaining work, in dependency order

### M1 — T2 qualification readiness (local, no Pod)

Only evaluation preparation is allowed until CP4. Do not change foundation
weights, add persona/tools/memory, or spend on a live resource in this phase.

**CP2 — Actual-token context packet**

1. Keep the nine synthetic context cases outside the frozen 60-case suite.
2. Add the exact tokenizer and runtime metadata used by the evaluator.
3. Generate 8K, 16K, and 32K probes with the needle at the beginning, middle,
   and end of the context.
4. Record token counts, truncation, latency, and retrieval accuracy from the
   actual runtime. Word counts are not an acceptable substitute.
5. Store configuration, hashes, machine-readable output, and a decision file.

Acceptance: the generator and metadata validator pass locally; no model
behavior or context capability is claimed. If the tokenizer/runtime is
unavailable, record `blocked` and the exact input needed to resume.

**CP3 — Evaluator integrity**

1. Re-run Docker boundary, resource-limit, cleanup, and fail-closed checks.
2. Verify expected answers and scores are host-side and model-produced flags
   are untrusted.
3. Verify raw-result retention, secret redaction, runtime provenance, and no
   leftover containers.
4. Run the complete local evaluation test set and preserve the report.

Acceptance: all integrity checks pass and the evidence can be reproduced from
the checked-out commit.

**CP4 — Frozen T2 readiness packet**

1. Freeze protocol revision, hashes, runtime pins, thresholds, cases, sampling,
   and required Candidate A/B/control artifacts.
2. Include the negative packet and prove the verifier rejects it.
3. Reconcile the historical Candidate A launcher with the matched T2 runtime;
   do not substitute the old smoke result.
4. Write the exact bounded live-run packet and cost estimate, without starting
   it.

Acceptance: the positive packet validates, the negative packet fails, all
required inputs are present, and `runs/<date>-t2-readiness/decision.md` records
the handoff to M2.

### M2 — Mind Proven (first paid/live qualification)

Begins only after CP4 and a fresh explicit authorization for one bounded A100
80 GB run with the $1.75/hour ceiling and supervised shutdown.

- **CP5 Diagnostic reviewed:** run the approved Candidate A diagnostic first;
  inspect truthfulness, reasoning, context, coding, schema, and tool failures.
- **CP6 Matrix complete:** run the matched Candidate A/B and official-control
  matrix with raw responses, runtime attestations, and independent scores.
- **CP7 Human adjudicated:** complete blinded human review and resolve
  disagreements without changing thresholds after seeing results.
- **CP8 Selection signed:** record selected, rejected, or held foundation and
  the reason. Only this checkpoint can close foundation qualification.

If runtime, network, cost, or evidence preflight fails, stop and preserve the
failed run. Do not create an automatic replacement Pod.

### M3 — Voice Recognized

After M2 only: approve persona examples, implement the prompt wrapper, run
blind baseline comparisons, and pass capability regression. Consider an
adapter only if prompting is insufficient and the change is separately scoped.

Checkpoints: CP9 examples approved, CP10 prompt persona pass, CP11 regression
pass. Complete the remaining A1/E2 TODO items that are required for these
checks, including persistence and safe rendering, without expanding the scope.

### M4 — Hands Online and Memory With Boundaries

Keep these as separate packets so a tool result cannot be confused with a
memory result.

- CP12 Tools Safe: registry, schemas, permissions, confirmation, timeouts,
  limits, and audit records.
- CP13 Tools Truthful: real result/error evidence, no invented success, and a
  clean tools-disabled path.
- CP14 Memory Isolated: session/user/project/application scopes, attribution,
  retrieval, and stale-data handling.
- CP15 Memory Disable-Proven: inspect/correct/export/delete/disable controls and
  a test proving disabled memory is not read or written.

### M5 — Facets and controlled release

- CP16 Alias Integration: one external application uses the stable `Veronica`
  alias without hardcoding a foundation model.
- CP17 Module Removal: Studio Director and Application Builder are removable,
  manifest-validated modules.
- CP18 Recovery Proven: clean-machine local and Pod recovery, inventories, and
  secret-free configuration are reproducible.
- CP19 Staging Verified: authenticated, quota-limited, cost-visible
  Serverless staging with cold-start, failure, concurrency, and scale-to-zero
  evidence.
- CP20 Owner Release Decision: required reviews complete, release risks are
  recorded, and Travis explicitly accepts or holds release.

## Checkpoint contract

Every checkpoint must leave four things: a dated decision file, machine-readable
reports or test output, the exact commit, and a short handoff naming the next
action and any blocker. A checkpoint is not earned by a plan, a port, a mock, or
a model claim. Failed attempts remain in `runs/` and are never overwritten.

## Immediate execution slice

1. Implement CP2 only.
2. Run its local validator and targeted tests.
3. Write the CP2 decision and handoff.
4. Stop for the checkpoint review before starting CP3.

This keeps the work moving while preserving the requested frequent review
points. The full plan is intentionally selective: every later milestone is
blocked until its predecessor has evidence.
