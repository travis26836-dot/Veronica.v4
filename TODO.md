# Veronica.v4 — Definitive TODO

This checklist is the execution source of truth. Check an item only when its stated proof exists. Historical evidence remains in its original dated run folders; the active identity decision is `runs/2026-09-25-installed-foundation-identity/decision.md`.

## Active identity and guardrails

- [x] Define the sole public API/model alias as `Veronica.v.4.1-30B-A3B-BF16`.
- [x] Register one installed-foundation baseline with pinned internal provenance, BF16/no-quantization declaration, and immutable revision.
- [x] Replace active paired-model planning with `config/foundation-baseline-qualification.json`.
- [x] Preserve legacy decision records and completed handoffs without rewriting their terminology.
- [ ] Obtain complete live baseline evidence under fresh bounded authorization. **No inference occurred during the identity migration.**

## Research and provenance

- [x] Record the installed foundation's repository, revision, persistent-storage path, declared Apache-2.0 license, architecture, and BF16/no-quantization state. Proof: `config/model-registry.json` and `runs/2026-09-25-installed-foundation-identity/`.
- [x] Preserve pinned README/license snapshots for the active internal provenance record. Proof: `runs/2026-09-25-installed-foundation-identity/provenance/foundation-baseline/`.
- [x] Preserve prior storage-manifest/hash evidence without treating it as qualification. Proof: `runs/2026-09-13T135326Z-start-veronica/`.
- [ ] Collect current artifact, runtime, tokenizer, server-command, GPU, and raw-response evidence in one authorized baseline run.
- [ ] Complete executable-code, native-tool, long-context, JSON/schema, and human-review evidence.

## Wrapper and API

- [x] Expose only `Veronica.v.4.1-30B-A3B-BF16` at `/v1/models`, non-streaming chat responses, streaming chunks, defaults, and the static UI.
- [x] Keep the upstream repository configurable internally and hidden from public API/UI contracts.
- [x] Keep Chat, Deep Reasoning, Creative, and Coding as prompt presets pending native behavior qualification.
- [ ] Add browser persistence, message controls, safe Markdown/code rendering, and context display after core qualification work is stable.

## Baseline qualification

- [x] Freeze one-model direct, persona-free baseline tracks and an offline evidence auditor.
- [ ] Start a Pod only after a fresh explicit owner request, duration, budget, and one-use approval.
- [ ] Run each frozen baseline track against the installed foundation.
- [ ] Save every raw response, automatic check, runtime attestation, supplemental report, and human review.
- [ ] Record a signed hold, qualification, or rejection decision. Missing or inconclusive evidence remains `hold`.

## Later work

- [ ] Tune persona only after an intact baseline is recorded and regression gates are ready.
- [ ] Implement permissioned native tools, then scoped memory and application modules.
- [ ] Build reproducible packaging, authentication, observability, cost controls, and scale-to-zero deployment.

**Current gate:** the installed foundation is available in persistent storage but **not fully qualified**. The next legitimate action is offline validation or a freshly authorized, bounded baseline run.
