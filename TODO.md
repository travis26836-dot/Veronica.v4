# Veronica.v4 - Definitive TODO

This file is the execution source of truth. Check an item only when its stated proof exists. Each milestone ends with a named acknowledgment so progress is visible and memorable.

**Immediate route:** candidate integrity -> model server -> first text/chat. The full roadmap below is not a prerequisite for that first conversation. Full qualification is required before final model selection and fine-tuning.

## Status legend

- `[ ]` not verified
- `[x]` verified with evidence
- `HOLD` cannot proceed safely or legitimately
- `ACK` milestone acknowledgment earned only after its gate passes

## C - Capture: define the AI

- [x] Confirm owner, objective, canonical home, and operating mode in `README.md`.
- [x] Separate Veronica's stable identity from the replaceable foundation model.
- [x] Define capability-first and reversible-fine-tuning principles.
- [x] Define the seven target capability modules.
- [x] Limit the first deliverable to basic text/chat and mode selection.
- [x] Record current exclusions: public billing, accounts, autonomous publishing, and media execution.
- [x] Document completion criteria in `docs/SOURCE-OF-TRUTH.md`.
- [x] Preserve existing image/video work under `NON-SOURCE CODE/` as a later module input.

**Gate C:** project documents agree and contain no claim that an untested model is complete.

**ACK:** `North Star Locked` - verified 2026-08-30.

## R - Research: qualify the foundation

- [x] Register the already-bucketed 30B-A3B uncensored candidate.
- [x] Register the newer Qwen3.8-27B uncensored capability challenger.
- [x] Pin immutable Hugging Face revisions for every candidate and control. Proof: `runs/2026-08-30-candidate-provenance/decision.md`.
- [x] Save the full license and model-card snapshots in the run record. Proof: `runs/2026-09-01-t2-qualification/provenance-manifest.json`.
- [x] Verify commercial use, modification, redistribution, attribution, and derivative obligations. Proof: `runs/2026-09-01-t2-qualification/license-review.md`; repository declarations do not replace final legal review.
- [x] Record base-model lineage and the community ablation method. Proof: the same pinned snapshots and license/lineage review.
- [ ] Record complete file manifest, expected byte count, and storage URI.
- [ ] Validate transfers before promotion from `.uploading` storage.
- [ ] Select comparison quantizations appropriate to 48 GB and 80 GB GPUs.
- [x] Define the fixed development evaluation prompt pack and scoring rubric. Proof: `runs/2026-08-31-evaluation-foundation/decision.md` (60 cases, 69 turns, 0–4 rubrics). Independent qualification holdouts remain pending.
- [x] Include sarcasm, implication, humor, disagreement, and ambiguity tests. Proof: `docs/evals/QUESTION-BANK.md`, social-understanding and correction categories; authored coverage, not model results.
- [ ] Include chat, reasoning, creative writing, coding, long context, and factuality tests.
- [ ] Include JSON-schema and native tool-call tests.
- [ ] Include intended lawful adult prompt-following tests.
- [ ] Include ablation-regression comparisons against official controls.
- [ ] Record expected RunPod GPU, maximum hourly price, and termination deadline.

**Gate R:** no candidate advances without provenance, license, integrity, and an approved evaluation plan.

**ACK:** `Engine Accounted For` - pending.

## E - Establish: create durable contracts

- [x] Create the canonical source-of-truth document.
- [x] Create the stage-by-stage build pipeline.
- [x] Create a versioned model registry.
- [x] Create durable workflow statuses and advancement rules.
- [x] Create Core Builder, Capability Evaluator, and Release Keeper roles.
- [x] Define the public API model alias as `Veronica`.
- [x] Define the initial OpenAI-compatible wrapper endpoints.
- [x] Define run-folder evidence requirements.
- [x] Add a local project-contract validator for required artifacts, JSON, identity, alias, and hold state.
- [ ] Add JSON schemas for run records, model records, evaluation cases, and module manifests.
- [ ] Add a configuration fingerprint generator.
- [ ] Add an immutable run-folder initializer.
- [ ] Add a license/provenance validation checklist script.
- [ ] Commit the initial source-of-truth baseline.

**Gate E:** another session can identify the current state and next legitimate action without relying on chat history.

**ACK:** `Trail Marked` - pending initial commit and schema validation.

## A1 - Assemble: local wrapper and chat

- [x] Scaffold a Python 3.12 package using a `src/` layout.
- [x] Add environment-based provider configuration with no committed secrets.
- [x] Add stable Veronica alias mapping to a configurable upstream model.
- [x] Add concise, capability-preserving persona injection.
- [x] Add Chat, Deep Reasoning, Creative, and Coding modes.
- [x] Add wrapper health and capability endpoints.
- [x] Add basic non-streaming chat completions.
- [x] Add clear provider-unavailable behavior.
- [x] Add a local interactive chat page with a mode menu.
- [ ] Add streaming chat responses.
- [ ] Add conversation persistence for the browser session.
- [ ] Add message retry, stop-generation, copy, and regenerate controls.
- [ ] Add Markdown and code-block rendering with safe escaping.
- [ ] Add model context/token usage display.
- [ ] Add configurable reasoning-effort controls supported by the selected model.
- [ ] Add local-only access controls before exposing beyond loopback.

**Gate A1:** wrapper starts without a GPU and reports provider status honestly.

**ACK:** `Shell Awakened` - local HTTP/UI/alias verified 2026-08-30. A later real chat run succeeded; its paid Pod is now terminated.

## A2 - Assemble: model server

**Current checkpoint:** first real API/UI conversation achieved; Pod explicitly terminated and absent from inventory. Network volume retained. See `runs/2026-08-30-supervised-first-chat/decision.md`. The supervised run's approval is consumed; future/replacement Pods need fresh authorization. Capability qualification is not passed.

- [x] Create a reusable, secret-free RunPod profile, shared Codex/Copilot skill, preflight, scoped supervised controller and on-Pod preparation script; validate offline safety checks. Proof: `runs/2026-08-30-supervised-first-chat/decision.md` (27 tests).
- [x] Add the "Start Veronica" trigger, one duration question with a one-hour default, saved $1.75/hour/one-A100 limits, and a checked multi-step launcher. Offline proof: `runs/2026-08-30-start-command/decision.md`.
- [x] Verify the original START launcher through a fresh authorized paid cold restart and confirmed shutdown. Proof: `runs/2026-08-31T034034Z-start-veronica/decision.md` and `termination.json`. The later UI-first order has a separate pending live check below.
- [x] Open a live UI before startup response checks finish, per the owner's correction; preserve access while tests run. Live proof: `runs/2026-08-31T034034Z-start-veronica/decision.md` (same-Pod UI at port 8011 during the original launch).
- [ ] Verify the revised launcher opens its standard 8010 UI via `startup-ui-ready.json` before waiting for model readiness/tests on the next authorized cold start. Existing offline suite passed; see the same run's `ui-first-offline-tests.txt`.

- [x] Create a short-lived RunPod development run with an explicit termination deadline. Proof: `runs/2026-08-30-supervised-first-chat/supervised-state.json`; local backup is not a platform guarantee.
- [x] Attach or locate validated persistent model storage. Proof: `runs/2026-08-30-supervised-first-chat/validated-model-manifest.json`.
- [x] Pin the CUDA/runtime image and vLLM package versions. Proof: `runs/2026-08-30-supervised-first-chat/profile.json` and `runtime-packages.txt`.
- [x] Start Candidate A with a documented OpenAI-compatible command. Proof: `runs/2026-08-30-supervised-first-chat/server-command.json`.
- [x] Verify `/v1/models`, one completion, model identity, and clean shutdown. Proof: `runs/2026-08-30-supervised-first-chat/decision.md` and linked raw evidence.
- [x] Record load time, VRAM, first-content latency, observed throughput, and configured context limit. Proof: `runs/2026-08-30-supervised-first-chat/verification-summary.json`; full context stress testing remains open.
- [ ] Repeat for Candidate B and official controls where affordable.
- [ ] Confirm native reasoning controls and the correct tool-call parser.
- [x] Confirm the Pod is terminated after evidence is transferred. Proof: `runs/2026-08-30-supervised-first-chat/termination.json`.

**Gate A2:** a model server can be recreated from records and shut down without data loss.

**ACK:** `First Pulse` - first deployment/inference/shutdown verified 2026-08-30. Cold restart and full qualification remain open.

## T1 - Test: wrapper without paid GPU

- [x] Add a mock upstream provider for deterministic tests.
- [x] Test stable alias exposure.
- [x] Test persona injection without replacing user or system content.
- [x] Test mode prompt injection and removal of wrapper-only fields.
- [x] Test provider failure returns an honest 503 response.
- [x] Test malformed chat requests stop locally.
- [x] Test the capability endpoint distinguishes implemented from planned work.
- [x] Test browser UI behavior in Chrome and narrow/mobile widths. Proof: `runs/2026-08-30-ui-layout-port/decision.md`.
- [ ] Test interruption and restart with no false provider-ready state. Actual shutdown-to-offline transition verified in the supervised run; restart is still open.
- [ ] Test wrapper logs redact authorization values.
- [ ] Resolve the upstream Starlette TestClient HTTPX deprecation warning before upgrading test dependencies.

**Gate T1:** all local tests pass on a clean environment.

**ACK:** `Shell Proven` - 13 local tests passed; see `runs/2026-08-30-core-foundation/decision.md`.

## T2 - Test: untouched model baseline

- [x] Build an offline-validated evaluation runner, transcript intake/reporting, draft dataset linter, and reusable `veronica-evals` skill. Proof: `runs/2026-08-31-evaluation-foundation/decision.md`.
- [x] Freeze a matched four-model T2 protocol and add a strict offline evidence verifier. Proof: `config/t2-qualification.json` and `runs/2026-09-01-t2-qualification/decision.md`; no live comparison is claimed.
- [x] Preserve and import the retained first conversation for evaluation, with assistant findings labeled advisory and training consent absent. Proof: `runs/2026-08-31-recorded-conversation-eval/report.md`.
- [ ] Adjudicate the transcript's advisory findings and approve the next bounded evaluation selection.
- [ ] Extend short context probes into long-context stress tests and add complete schema/executable-code qualification environments; the current runner never executes tools or generated code.
- [ ] Run the frozen evaluation pack against each candidate and control.
- [ ] Save every raw response and machine-readable score.
- [ ] Manually review sarcasm, personality fit, prose, and conversational intuition.
- [ ] Measure coding correctness with executable tests.
- [ ] Measure structured JSON validity and schema adherence.
- [ ] Measure tool selection, argument accuracy, and invented-result rate.
- [ ] Measure multi-turn consistency and context retention.
- [ ] Measure refusal behavior for intended lawful requests.
- [ ] Compare quantized output quality to full or higher-precision controls.
- [ ] Reject candidates that require the wrapper to simulate missing native capability.
- [ ] Record a signed model-selection decision.

**Gate T2:** the selected model wins on capability and acceptable cost, not familiarity or download completion.

**ACK:** `Mind Proven` - pending.

## E1 - Execute: basic Veronica text/chat milestone

- [x] Configure the wrapper with an intact candidate and immutable revision; mark the choice provisional until the baseline passes. Proof: `runs/2026-08-30-supervised-first-chat/decision.md`.
- [x] Start the model server under a bounded supervised development run. Proof: the same run's `supervised-state.json` and `termination.json`; no platform timer guarantee.
- [x] Start the Veronica wrapper locally. Proof: the same run's `windows-ready-health.json`.
- [x] Verify wrapper health from the local machine. Proof: the same run's Windows health records.
- [x] Complete a multi-turn Chat-mode conversation. Proof: the same run's `ui-live-transcript.txt` and `ui-live-recall.png`.
- [ ] Complete one Deep Reasoning task without contradictory answers. The first task ended at the correct 3/10 but opened with 3/5; see the run's `manual-review.md`.
- [x] Complete one Creative writing smoke task. Proof: the run's `wrapper-smoke.json`; broader prose quality is not qualified.
- [x] Complete one Coding task with an executable result. Proof: the run's `generated-coding-check.py` and `verification-summary.json` (nine checks).
- [x] Confirm responses publicly identify the model as Veronica. Proof: the run's raw responses and UI transcript.
- [x] Save screenshots, API output, configuration fingerprint, and evaluation summary. Proof: `runs/2026-08-30-supervised-first-chat/`.
- [x] Shut down and terminate paid GPU resources. Proof: the run's `termination.json`.
- [ ] Commit the verified milestone state.

**Gate E1:** Veronica speaks through its own UI and API with untouched foundation weights. Capability qualification remains explicitly pending until T2 passes.

**ACK:** `Veronica Speaks` - first real two-turn UI/API chat verified 2026-08-30. Full capable-core acceptance is NOT earned: reasoning consistency, action truthfulness, persistence and broader qualification remain open.

## E2 - Execute: personality adaptation

- [x] Prepare a diagnosis-first dataset/adapter strategy with provenance, consent, family splits, regression exclusions and draft SFT/DPO examples. Proof: `docs/evals/DATASET-AND-FINETUNING-STRATEGY.md`; no training-ready dataset or training run is claimed.
- [ ] Write a personality specification with positive examples and explicit non-goals.
- [ ] Define sarcasm, humor, initiative, confidence, honesty, and disagreement behavior.
- [ ] Collect owner-written or owner-approved conversation examples.
- [ ] Remove factual teaching and application knowledge from the persona dataset.
- [ ] Split train, validation, blind preference, and regression sets.
- [ ] Version and document the dataset with provenance.
- [ ] Tune the wrapper persona before training weights.
- [ ] Run blind preference tests against the baseline persona.
- [ ] Train a reversible LoRA/QLoRA adapter only if prompting is insufficient.
- [ ] Run the complete capability regression suite.
- [ ] Reject the adapter if reasoning, coding, tools, or writing regress beyond threshold.
- [ ] Version the accepted adapter separately from the foundation weights.

**Gate E2:** Veronica sounds unique without becoming less capable.

**ACK:** `Voice Recognized` - pending.

## E3 - Execute: native tools

- [ ] Define the tool registry and JSON schemas.
- [ ] Implement model-generated tool calls without text-pattern guessing.
- [ ] Add per-tool permissions, timeouts, loop limits, and audit records.
- [ ] Require confirmation for publish, send, purchase, delete, and external commit.
- [ ] Return tool results to the model with untrusted-data boundaries.
- [ ] Verify correct tool selection and argument generation.
- [ ] Verify the model never claims an unexecuted tool succeeded.
- [ ] Verify ordinary chat continues when tools are disabled.

**Gate E3:** native tool behavior is reliable, permissioned, observable, and optional.

**ACK:** `Hands Online` - pending.

## E4 - Execute: scoped memory

- [ ] Define session, user, project, and application scopes.
- [ ] Implement retrieval with source attribution and confidence metadata.
- [ ] Prevent cross-application and cross-user leakage.
- [ ] Add inspect, correct, export, delete, and disable controls.
- [ ] Test retrieval relevance and stale-memory handling.
- [ ] Prove memory can be disabled without breaking chat.

**Gate E4:** memory makes Veronica more useful without silently controlling or leaking context.

**ACK:** `Memory With Boundaries` - pending.

## E5 - Execute: remaining modules

- [ ] Complete General Assistant acceptance tests.
- [ ] Complete Deep Reasoner acceptance tests.
- [ ] Complete Generative Writer acceptance tests.
- [ ] Complete Tool-Using Agent acceptance tests.
- [ ] Build the Studio Director as a tool-based application module.
- [ ] Build the Application Builder and module-manifest validator.
- [ ] Integrate each module through the stable Veronica API alias.
- [ ] Verify every module can be removed without damaging core chat.

**Gate E5:** all modules extend one core rather than becoming disconnected AI projects.

**ACK:** `Seven Facets Lit` - pending.

## D - Document, package, and release

- [ ] Pin application, runtime, model, adapter, and configuration versions.
- [ ] Build a reproducible container without secrets.
- [ ] Generate dependency and license inventories.
- [ ] Validate clean-machine startup and health checks.
- [ ] Document local, Pod, and Serverless recovery procedures.
- [ ] Add API authentication, usage metering, quotas, and rate limits.
- [ ] Add structured logs, latency/error metrics, and model-version telemetry.
- [ ] Add per-request cost accounting and budget alarms.
- [ ] Deploy a Serverless scale-to-zero staging endpoint.
- [ ] Verify cold start, successful request, failure behavior, concurrency, and scale-to-zero.
- [ ] Complete security, privacy, legal, and abuse-boundary review.
- [ ] Publish only after an explicit owner release approval.
- [ ] Preserve the final evaluation, deployment manifest, recovery proof, and release decision.

**Gate D:** the system is reproducible, supportable, accountable, and affordable to operate.

**ACK:** `Veronica Released` - pending.

