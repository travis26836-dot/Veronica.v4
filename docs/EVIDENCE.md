# Technical evidence and limits

## Active foundation evidence

The active foundation is an internal installed-baseline record, not a public API name. Its provenance is recorded in `config/model-registry.json` and [the 2026-09-25 identity decision](../runs/2026-09-25-installed-foundation-identity/decision.md): pinned repository/revision, persistent storage path, Apache-2.0 declaration, Qwen3MoeForCausalLM architecture, BF16 format, and no quantization. Pinned card/license snapshots are local evidence only; they do not replace legal review.

## What is verified

- The Python environment resolves through `uv.lock`.
- The wrapper has offline mock-provider tests.
- Historical records preserve prior storage integrity, smoke transport/UI, and clean termination evidence.
- The public API/UI identity is `Veronica.v.4.1-30B-A3B-BF16` and forwards to an internal configurable upstream.

## What remains unverified

- Full live baseline capability: reasoning, writing, coding, factuality, social understanding, and action truthfulness.
- Native tool reliability, executable-code isolation, long-context behavior, JSON/schema performance, latency, throughput, and cost.
- Full legal/license obligations beyond the declared snapshot record.
- Fine-tuning quality, capability retention, production security, and Serverless behavior.

> A successful model list, HTTP response, storage manifest, model-card claim, mock test, or smoke conversation is **not** full foundation qualification.

No inference, paid GPU start, model download, or weight modification occurred during the 2026-09-25 installed-foundation identity migration.
