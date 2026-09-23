# 2026-09-22 CP2 actual-token context packet

**Decision:** CP2 Context Packet Ready is complete. M1 continues at CP3.

## Verified

- `config/t2-context.json` pins the frozen 60-case suite hash, matched T2
  runtime, and all four candidate/control tokenizer revisions.
- The packet used the exact Qwen tokenizer JSON artifacts at those immutable
  revisions. Their SHA-256 hashes are recorded in `metadata.json`; the local
  acquisition files were hash-checked against the durable Hugging Face URLs.
- `probes.jsonl` contains nine synthetic cases: 8K, 16K, and 32K actual tokens,
  each with the needle at the beginning, middle, and end.
- `report.json` and `validation.json` record actual token counts for all four
  tokenizers, per-tokenizer truncation, tokenizer-only latency, and synthetic
  literal retrieval integrity.
- All primary tokenizer probes hit their requested token counts exactly. The
  alternate Qwen3.8 tokenizer reports 8,191/16,383/32,767 for middle/end
  boundary variants; these are retained as measured rather than rounded.
- The synthetic probes remain outside the frozen suite. `model_retrieval_accuracy`
  is `null`, model latency is uncollected, `model_behavior_claim` is `false`,
  and no model server or Pod was started.

## Validation

- `uv run pytest tests/test_context_gate.py -q` passed (6 tests).
- `uv run --with tokenizers==0.22.2 python scripts/generate_context_packet.py`
  completed and wrote a valid nine-probe packet.
- Packet validator returned `valid: true`.

## Limits and next action

This checkpoint proves packet construction and tokenizer/runtime provenance. It
does not prove model context capacity, needle retrieval, model latency, or any
candidate capability. CP3 must verify evaluator integrity, host-side scoring,
redaction, runtime provenance, and clean Docker state before CP4 freezes T2.

No paid compute, Pod, model server, training, or external action was used.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
