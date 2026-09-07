# Veronica Core Build Pipeline

This pipeline is sequential. A stage advances only when its artifact, validation result, and acknowledgment are saved in a dated run folder.

## Pipeline map

```text
Contract -> Candidate integrity -> Model server -> First wrapper chat
         -> Baseline -> Persona -> Tools -> Memory -> Modules -> Package -> Serverless
```

## Stage 0 - Contract lock

**Input:** owner vision and canonical project folder.

**Output:** `README.md`, `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, model registry.

**Validation:** documents agree on objective, current truth, exclusions, candidates, and definition of done.

**Recovery:** return to the last committed versions and reconcile evidence before editing.

**Acknowledgment:** `North Star Locked`

## Stage 1 - Candidate integrity

**Input:** candidate repository URL and exact revision.

**Output:** license record, file manifest, sizes, hashes where practical, and storage location.

**Validation:** repository is downloadable, commercially usable for the intended packaging, explicitly uncensored, and traceable to its base.

**Failure state:** `hold` for unclear license, incomplete weights, mutable revision, or corrupted transfer.

**Acknowledgment:** `Engine Accounted For`

## Stage 2 - OpenAI-compatible model server

**Input:** provenance-checked, intact candidate and pinned serving image.

**Output:** reachable `/v1/models` and `/v1/chat/completions` endpoints.

**Validation:** deterministic startup, model identity check, healthy completion, bounded timeout, clean shutdown, and restart proof.

**Recovery:** recreate from the pinned image and persistent model storage; never rely on undocumented Pod state.

**Acknowledgment:** `First Pulse`

## Stage 3 - Veronica wrapper and basic chat

**Input:** healthy model server.

**Output:** Veronica API alias, persona injection, mode selection, and local chat UI.

**Validation:** multi-turn conversation, provider failure handling, model aliasing, no secret leakage, and no capability-changing prompt pollution.

**Recovery:** wrapper starts independently and clearly reports provider unavailable.

**Acknowledgment:** `Veronica Speaks`

This is the immediate product milestone. Future modules and complete benchmarks do not block this first conversation.

## Stage 4 - Untouched capability baseline

**Input:** intact candidate, functioning server, and a fixed evaluation pack.

**Output:** raw responses, scores, latency, VRAM, and failure categories.

**Validation:** minimum thresholds for chat, reasoning, writing, coding, sarcasm/implied meaning, JSON, tool calls, long context, and intended prompt following.

**Failure state:** reject or compare another quantization/candidate; do not compensate with persona fine-tuning.

**Acknowledgment:** `Mind Proven`

## Stage 5 - Persona shaping

**Input:** approved personality specification and conversation examples.

**Output:** versioned persona prompt, then an optional LoRA adapter and dataset card.

**Validation:** blind style preference tests plus complete baseline regression.

**Failure state:** remove or roll back the adapter; base weights remain unchanged.

**Acknowledgment:** `Voice Recognized`

## Stage 6 - Native tool calling

**Input:** qualified model-server tool parser and safe tool schemas.

**Output:** tool registry, permission boundary, execution loop, and audit trail.

**Validation:** correct tool selection and arguments, refusal to invent tool results, approval stops, timeout handling, and loop limits.

**Recovery:** disable tool execution while preserving ordinary chat.

**Acknowledgment:** `Hands Online`

## Stage 7 - Scoped memory

**Input:** memory policy and retrieval stores.

**Output:** session, user, project, and application memory scopes.

**Validation:** retrieval relevance, deletion/export behavior, cross-scope isolation, and memory-off mode.

**Recovery:** disable retrieval without deleting the source records.

**Acknowledgment:** `Memory With Boundaries`

## Stage 8 - Application modules

**Input:** stable wrapper contracts and one approved application specification.

**Output:** module manifest, tools, knowledge scope, optional adapter, and tests.

**Validation:** the application integrates through Veronica's public API without binding itself to foundation weights.

**Recovery:** unload the application module without changing core chat.

**Acknowledgment:** `New Door Opened`

## Stage 9 - Reproducible package

**Input:** qualified wrapper, model configuration, adapters, and tests.

**Output:** pinned container image, startup contract, health check, dependency record, and deployment manifest.

**Validation:** clean-environment build and start; no secrets or unlicensed weights embedded.

**Recovery:** deploy the last qualified image by immutable version.

**Acknowledgment:** `Core Sealed`

## Stage 10 - Production Serverless

**Input:** packaged worker, network model storage, API gateway, and cost policy.

**Output:** authenticated scale-to-zero endpoint with request accounting.

**Validation:** cold start, successful request, concurrency, timeout, quota, failed-request accounting, shutdown to zero, and budget alarm.

**Recovery:** disable ingress and return to the last qualified worker image.

**Acknowledgment:** `Veronica Released`

## Required run record

Each execution uses `runs/YYYY-MM-DD-purpose/` and contains:

```text
run.json
inputs/
outputs/
logs/
evaluations/
decision.md
```

`run.json` records stage, status, owner, timestamps, model revision, runtime version, GPU, configuration fingerprint, and last durable handoff. Secrets are never written into the run folder.

Create new folders with `scripts/init_run_folder.py`; it refuses to overwrite an existing run directory.

## Contract schemas

Machine-readable JSON Schema files live in `config/schemas/` for run records, model records, evaluation cases, and module manifests. `scripts/validate-project.ps1` requires those schema files. After dependency sync, `scripts/verify-local.ps1` runs `scripts/validate_contracts.py` against the canonical registry and evaluation suite, then `scripts/check_license_provenance.py` against pinned local snapshots. Neither command downloads weights or starts compute.

Non-secret profile, runtime, and identity settings are hashed by `scripts/configuration_fingerprint.py`.
