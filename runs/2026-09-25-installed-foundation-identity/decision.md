# 2026-09-25 installed-foundation identity

**Decision:** Accept the installed RunPod foundation as the sole active foundation, and expose it only through the public alias **`Veronica.v.4.1-30B-A3B-BF16`**. Qualification remains **pending**. This record supersedes active Candidate A/B planning terminology; it does not rewrite historical run folders.

**Status date:** 2026-09-25  
**Owner:** Travis  
**Stage:** establish  
**Paid GPU started:** no  
**Model inference performed:** no  
**Weights modified:** no

## Why this supersedes Candidate A/B

Active project materials previously described two candidate foundations and official controls. The owner directed that the model already installed on persistent storage is the only active foundation, that Candidate A/B labels must leave active planning documents, and that clients should call a Veronica-named alias that still records parameter class and BF16/no-quantization.

Historical completed run records remain immutable. Those folders may still say Candidate A; this decision is the new authority for *active* documents, configs, and tests.

## Accepted public identity

| Field | Value |
| --- | --- |
| Product | Veronica |
| Public API/model alias | `Veronica.v.4.1-30B-A3B-BF16` |
| Role of alias | Client-facing name only; never the upstream repository |

Applications must call the exact alias. They must not hard-code the Hugging Face repository or storage path.

## Internal provenance — not a public API contract

| Field | Value |
| --- | --- |
| Registry id | `foundation-baseline` |
| Repository | `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` |
| Immutable revision | `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` |
| Persistent storage path | `/workspace/veronica-core/models/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated/e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` |
| Declared license | Apache-2.0 |
| Architecture | `Qwen3MoeForCausalLM` (30.5B total / 3.3B active parameters) |
| Weight format | BF16 |
| Quantization | none |
| Weights | unchanged |
| Active registry | `config/model-registry.json` |
| Baseline protocol | `config/foundation-baseline-qualification.json` |
| Baseline RunPod profile | `config/runpod-foundation-baseline.json` |
| Card/license snapshots | `runs/2026-09-25-installed-foundation-identity/provenance/foundation-baseline/` |

Pinned snapshots and registry fields establish declared identity. They do not prove model quality, legal finality, or live capability.

## Qualification status

The installed foundation remains **`pending` / `benchmark_required`**.

Not accepted as qualification evidence:

- Persistent-storage presence
- Historical smoke/chat transport success
- HTTP 200, a model listing, or nonempty text
- Prompt-preset modes in the wrapper UI

Required later evidence, under a fresh bounded owner authorization, includes artifact/runtime attestation, the frozen baseline tracks, executable-code isolation, native tool-call checks, long-context stress, JSON/schema checks, and signed human review. Missing or inconclusive evidence stays `hold`.

## Training implication recorded for later work

The installed foundation is a Transformers-compatible Qwen3 MoE causal LM and is therefore adaptable. Future personality work should keep this BF16 copy immutable and use a reversible LoRA adapter first. QLoRA is a VRAM fallback for a training load, not a reason to overwrite the canonical weights. No training, quantization, or adapter run is authorized by this decision.

## Limits of this run

- No Pod was created.
- No weights were downloaded or modified.
- No inference occurred.
- Secrets were not written into this folder.

## Next safe action

1. Keep this identity branch reviewed and durable.
2. Run remaining offline wrapper/protocol tests without compute.
3. Do **not** start RunPod until the owner issues a fresh, one-use, bounded START request. That live baseline is the next core milestone (`TODO.md` current gate).
