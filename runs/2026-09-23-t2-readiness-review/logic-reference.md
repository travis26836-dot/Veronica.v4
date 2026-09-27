# Why Veronica Core uses these checkpoints

This reference explains the decision order in plain language. It is a guide to
the evidence; `TODO.md` and `docs/SOURCE-OF-TRUTH.md` remain authoritative.

## The problem being solved

A wrapper can answer, a port can be open, and a mock can pass while the chosen
foundation model still fails at reasoning, context, coding, schemas, tools, or
truthfulness. A paid Pod is expensive, so we first make the tests trustworthy,
then use the Pod to collect real model behavior.

## What each gate proves

**CP1 — Schema Proven** checks the shape and meaning of structured outputs. It
rejects malformed JSON, duplicate keys, non-finite numbers, wrong roots,
unexpected keys, fabricated tool prose, and multiple native calls. It proves
that the evaluator can reject bad output; it does not prove a model will pass.

**CP2 — Context Packet Ready** constructs 8K, 16K, and 32K probes using the
actual pinned tokenizer for every candidate/control. The needle appears at the
beginning, middle, and end. Token counts, truncation, tokenizer latency,
artifact hashes, and runtime metadata are saved. Model retrieval is deliberately
`null` until live inference. This prevents word counts from being mistaken for
context capability.

**CP3 — Evaluator Trusted** checks that executable evaluation is isolated,
resource-limited, cleaned up, redacted, provenance-tracked, and scored on the
host. Expected answers stay outside the untrusted worker. This prevents a model
or worker from declaring its own pass.

**CP4 — T2 Ready** freezes the protocol, suite hash, runtime pins, thresholds,
case IDs, sampling, model/control matrix, and required evidence. It requires
completed CP2 and CP3 records and proves that a tampered packet is rejected.
It still does not qualify a foundation.

## Why the Pod comes after CP4

The Pod supplies the missing evidence: real completions, raw responses, runtime
attestations, latency, coding results, schema/tool behavior, and context
retrieval. The live sequence is diagnostic first, then the matched candidate /
control matrix, then human review and a signed selection. A live result cannot
repair an untrusted evaluator, so creating the Pod earlier would spend money
before the measurement system is ready.

## What a successful live run can and cannot decide

It can establish whether a pinned candidate meets the frozen capability and
cost gates. It cannot silently change thresholds, substitute a different
runtime, or turn a single smoke response into qualification. `Mind Proven` is
earned only after CP5 through CP8: diagnostic review, complete matrix, human
adjudication, and signed selection.

## Current boundary

CP1, CP2, and CP3 are complete. This review is rebuilding CP4 with their
evidence. No model is selected yet, no foundation is qualified yet, and no
Pod should be created until the combined packet reports `ready: true`.
