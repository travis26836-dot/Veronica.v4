# Veronica Core completion plan

Date: 2026-09-17. Owner: Travis. Execution branch: `feature/complete-todo-milestones`.
Status: proposed execution sequence; repository audit complete.

## C - Capture

Finish Veronica Core using the existing TODO gates and SOURCE-OF-TRUTH section 11.
TODO.md remains the checklist; this plan orders its remaining work. First chat is
already demonstrated. Core completion still requires qualification, persona,
tools, scoped memory, application integration, reproducible deployment, and
controlled Serverless staging. Do not silently redefine completion as chat alone.

Pause CREATED scheduling development, unrelated integrations, new model shopping,
and cosmetic work. Retain existing work. Studio Director and Application Builder
remain E5 deliverables, sequenced after the core capabilities they depend on.
Public release remains separately approved. No calendar completion promise is
credible until the foundation qualification result and runtime costs are known.

## R - Research

Verified starting point:

- September 13 decision proves Candidate A cold start, early UI, model integrity,
  smoke responses, and termination. It does not prove T2 qualification.
- Current protocol verifier passes: four registered models, two pairs, ten
  required model-track runs; `foundation_qualified=false`.
- The working launcher uses the historical Candidate A runtime. The frozen T2
  protocol uses a different matched runtime. Reconcile and verify compatibility
  before paying; do not silently substitute old smoke results for T2 results.
- The E1 commit checkbox is stale: commit `7a3f25a` contains the named decision.
  Audit the exact acceptance evidence before closing the checkbox; a coding
  claim made by the model is not an independently executed test.
- PR #5 is OPEN, MERGEABLE, CLEAN at head `59c00db`; remote verify passed.
  Fresh local suite and collaboration validation pass, with one platform skip
  and the known Starlette warning. Fetch found main at `5c47cf2`.

## E - Establish

One ordered queue, one accountable writer. Codex owns implementation and evidence;
Travis owns subjective acceptance, model selection, spending, and release.
After collaboration integration, claim each bounded item before editing, then
record tests, limitations, and next action in its handoff. No agents are spawned
by this plan. Coordination claims currently live per checkout: do not describe
them as global locks or allow concurrent writers based on that assumption.

| Order | Existing TODO scope | Required output and exit gate |
| --- | --- | --- |
| 0 | Establish / collaboration | Merge reviewed PR #5 into main after owner confirmation; merge main into the existing milestone branch, preserve both sets of AGENTS rules and the current branch objective, validate and commit conflict resolutions. No branch replacement. |
| 1 | R, A2, T1, E1, T2 preparation | Evidence-to-checkbox audit; interruption/restart and log-redaction checks; executable-code isolation, JSON schema, native tool-call scoring, long-context tests and independent holdout; frozen thresholds and a runnable evaluation packet. Resolve or explicitly record dependency-warning remediation. |
| 2 | R, A2, T2: Mind Proven | First run the already approved CC-01/CC-02/MB-01/MB-02 diagnostic selection on Candidate A under fresh paid authorization. Review known reasoning/truthfulness failures. Then execute matched candidate/control qualification, raw responses, executable scores, human review, precision comparisons and signed selection. |
| 3 | A1, E2: Voice Recognized | Finish session persistence, safe rendering, message controls, token/context display and access controls; expose reasoning controls only if supported. Tune prompt persona, approve examples, compare blind preferences, pass capability regressions. LoRA only if prompting is insufficient. |
| 4 | E3: Hands Online | Native tool registry and schemas, execution loop, permissions, confirmation, timeouts/limits and audit records. Prove real results, error handling, no invented execution success, and normal chat with tools disabled. |
| 5 | E4: Memory With Boundaries | Session/user/project/application scopes, attributed retrieval, inspect/correct/export/delete/disable controls. Prove isolation, stale-memory handling, relevance, and chat with memory disabled. |
| 6 | E5: Seven Facets Lit | Accept assistant/reasoner/writer/agent behavior; integrate one external application through Veronica alias; implement Studio Director and Application Builder as removable modules with manifest validation. Scope each module before implementation. |
| 7 | D: Veronica Released | Pinned secret-free container and inventories; clean-machine local/Pod recovery; authentication, quotas, metrics, costs, alarms; authorized Serverless staging with cold-start/request/failure/concurrency/scale-to-zero evidence; required reviews and owner release decision. |

## A - Assemble

First product work packet after collaboration integration: **qualification
readiness**, not another UI smoke run. Allowed paths: evaluation code and tests,
`config/t2-qualification.json`, evaluation data/docs, TODO, CURRENT-STATE, and a
new dated run folder; refine the exact claim after inspection. Preserve frozen
inputs by versioning any amended protocol and explaining the change.

Inputs: current protocol, evaluation runner, owner adjudication packet, pinned
model/runtime records, and September 13 evidence. Outputs: a gap report, runnable
missing checks, fixed acceptance thresholds, runtime compatibility evidence and
an exact bounded paid-run command/estimate. Validation: local tests plus strict
protocol/evidence verifier; negative fixtures must fail rather than qualify.
Failure state: blocked readiness with exact missing input and recovery action.

Use the existing four-model protocol. Candidate A diagnostic triage comes first
to limit waste; it does not waive matched comparison. Do not expand to new model
families without a recorded failure and a deliberate selection-plan revision.
48 GB quantization comparison remains evaluation scope, not authorization to
change the standing one-A100 launch policy.

## T - Test

Each gate requires its own acceptance proof. Local mocks prove wrapper behavior;
real raw responses and independently checked scores prove model behavior.
Freeze thresholds before collecting qualification outputs; use protocol-defined
thresholds where present, and obtain owner acceptance for new subjective gates.
Keep published regression material distinct from an independent holdout.
Review existing evidence before repeating paid tests. Never adjust criteria to
make a failed model pass. Human reviews and selection remain explicit records.

## E - Execute

Execute one bounded packet to a checked commit and handoff before taking another.
Merge PR #5 is the immediate recommendation, not completed by this planning task.
Its reviewable changes are at https://github.com/travis26836-dot/Veronica.v4/pull/5.
Integration must reconcile the PR's older CURRENT-STATE with this branch's newer
continuity records. Re-run validation on the resulting milestone branch.

No paid resource is authorized by this plan. For each live packet, first prepare
the exact model, tests, estimated duration, cost ceiling and failure stop point;
then obtain a fresh bounded start authorization. One A100 80 GB, maximum
$1.75/hour, supervised shutdown, no automatic replacement Pod. If runtime or
network preflight fails, resolve the failure before creating a resource.

If prompting meets E2, record why adapter-only TODO items are not applicable
instead of training just to tick boxes. Any other scope waiver requires an
explicit decision and synchronized TODO/source-of-truth update.

## D - Document

At every increment report: earned gate, evidence, commit, remaining blocker, next
action. A commit, push, merge, live verification and milestone are distinct.
Preserve failed attempts and ruled-out approaches. Scheduling remains deferred
until a useful end-to-end product work cycle succeeds and cadence is authorized.

Immediate next action: accept this sequence and integrate PR #5; then complete
the qualification-readiness packet. The final goal stays open until all core
completion criteria have evidence and the owner's required decisions exist.
