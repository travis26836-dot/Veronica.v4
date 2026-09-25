# Veronica Core Build Pipeline

A stage advances only when its artifact, validation result, and decision are saved in a dated run folder. The active public identity is **`Veronica.v.4.1-30B-A3B-BF16`**.

```text
Installed-foundation provenance -> model server -> wrapper chat
                               -> live baseline -> persona -> tools -> memory -> modules -> package -> serverless
```

## Stage 0 — Contract lock

**Output:** `README.md`, `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, and the one-foundation registry.
**Validation:** documents agree on the exact alias, one installed baseline, pending qualification, and protected actions.
**Acknowledgment:** `North Star Locked`.

## Stage 1 — Installed-foundation provenance

**Input:** the installed foundation's pinned internal repository/revision and persistent-storage path.
**Output:** declared license, pinned card/license snapshots, artifact manifest, hashes, architecture, BF16/no-quantization record, and storage location.
**Validation:** immutable identity and integrity evidence are present. Storage presence alone is not quality evidence.
**Failure state:** `hold` for unclear license, mutable revision, incomplete weights, or corrupted transfer.
**Acknowledgment:** `Engine Accounted For`.

## Stage 2 — OpenAI-compatible model server

**Input:** the intact installed foundation and pinned serving image.
**Output:** reachable private `/v1/models` and `/v1/chat/completions` endpoints advertising `Veronica.v.4.1-30B-A3B-BF16`.
**Validation:** deterministic start, identity check, bounded authorization, healthy completion, clean shutdown, and recovery proof.
**Acknowledgment:** `First Pulse`.

## Stage 3 — Wrapper and basic chat

**Output:** exact public alias, persona injection, prompt-preset modes, local UI, honest health, and provider failure handling.
**Validation:** mock-provider API/UI coverage and, separately, recorded live evidence.
**Acknowledgment:** `Veronica Speaks`.

## Stage 4 — Live installed-foundation baseline

**Input:** `config/foundation-baseline-qualification.json`, an already authorized running server, and the fixed suite.
**Output:** raw outputs, automated checks, latency, token/cost data, runtime attestation, supplemental technical reports, and human review.
**Validation:** direct persona-free baseline tracks plus executable code, native tools, long context, JSON/schema, and human-review gates. Missing or inconclusive evidence yields **hold**. The auditor never qualifies a foundation automatically.
**Acknowledgment:** `Mind Proven` only after a signed decision.

## Stages 5–10 — Extension and release

Persona adaptation, native tools, scoped memory, modules, packaging, and serverless deployment each require their own reversible design, regression proof, security/cost controls, and dated run decision. The foundation weights remain unchanged until a separately authorized change is evidenced.

## Required run record

Each execution uses `runs/YYYY-MM-DD-purpose/` with `run.json`, `inputs/`, `outputs/`, `logs/`, `evaluations/`, and `decision.md`. Record the model revision, runtime, GPU, configuration fingerprint, results, limitations, and next safe action; never write secrets. Use `scripts/init_run_folder.py`, which refuses overwrite.
