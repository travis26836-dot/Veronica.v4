# Veronica.v4 WORK IN PROGRESS

Veronica.v4 is a locally controlled AI product that wraps one installed open foundation with a stable public identity, **`Veronica.v.4.1-30B-A3B-BF16`**. The first deliverable is dependable text chat; reasoning, writing, coding, tools, memory, and later modules must extend the same core without silently replacing it.

This repository is the canonical source of product contracts, wrapper source, offline tests, foundation-provenance records, qualification evidence, and build history.

## Project contract

- **Objective:** deliver one capable, general-purpose AI product named **Veronica**.
- **Public API/model alias:** **`Veronica.v.4.1-30B-A3B-BF16`**. Clients call this alias, never an upstream repository name.
- **Operating mode:** local development and validation; short-lived, freshly authorized RunPod work only; eventual scale-to-zero deployment.
- **Source of truth:** [docs/SOURCE-OF-TRUTH.md](docs/SOURCE-OF-TRUTH.md)
- **Execution checklist:** [TODO.md](TODO.md)
- **Build pipeline:** [docs/BUILD-PIPELINE.md](docs/BUILD-PIPELINE.md)
- **Evaluation and qualification:** [docs/evals/README.md](docs/evals/README.md)
- **RunPod procedure:** [docs/STARTING-PROCEDURE.md](docs/STARTING-PROCEDURE.md)

The API preserves alias behavior: `/v1/models`, non-streaming completions, and streamed completion chunks expose only `Veronica.v.4.1-30B-A3B-BF16`; the wrapper forwards requests to its separately configurable upstream.

## Current verified state

- The wrapper and plain-text local chat UI are scaffolded and locally tested with a mock provider.
- A real historical RunPod smoke run demonstrated chat transport, UI readiness, and clean termination; it did **not** pass full foundation qualification.
- The installed foundation baseline is the only active foundation configuration.
- **Live baseline qualification is pending. No inference occurred during the 2026-09-25 identity migration.**
- No personality fine-tune, weight change, or production deployment exists.

## Internal provenance — not a public API contract

The installed foundation is recorded in internal configuration and the [2026-09-25 identity decision](runs/2026-09-25-installed-foundation-identity/decision.md):

| Field | Recorded value |
| --- | --- |
| Repository | `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` |
| Revision | `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` |
| Persistent storage path | `/workspace/veronica-core/models/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated/e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` |
| Declared license | Apache-2.0 |
| Architecture | Qwen3MoeForCausalLM |
| Weight format | BF16, no quantization |
| Qualification | Pending; storage presence and historical smoke evidence are not a full qualification pass |

## Non-negotiable principles

1. Capability evidence precedes tuning or capability claims.
2. The exact public alias remains stable while the upstream stays configurable internally.
3. Foundation weights remain unchanged during the wrapper/persona stage.
4. UI mode names are prompt presets until native behavior is qualified.
5. No milestone is complete without reproducible evidence in a dated run folder.
6. No paid GPU starts without a fresh, bounded owner authorization.
7. Source, active documents, and immutable run evidence remain separate.

## Quick start: wrapper-only development

```powershell
uv sync --python 3.12
Copy-Item .env.example .env
./scripts/start-wrapper.ps1
```

Open `http://127.0.0.1:8010`. The wrapper reports provider-unavailable state honestly until an OpenAI-compatible server is configured. Run `./scripts/verify-local.ps1` for local checks or `./scripts/build.ps1` to test and build; neither command rents GPUs or downloads weights.

## Folder guide

- `src/veronica_core/`: application source and static UI.
- `tests/`: offline/provider-mocked verification.
- `config/`: secret-free internal identity, runtime, schema, and qualification controls.
- `docs/`: active product and operating documentation.
- `runs/`: immutable execution and decision evidence.
- `scripts/`: repeatable local validation and start controls.
- `NON-SOURCE CODE/`: retained research and non-runtime material.
