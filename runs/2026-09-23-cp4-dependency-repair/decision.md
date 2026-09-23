# 2026-09-23 CP4 transitive dependency validation repair

**Decision:** The CP4 readiness packet machinery is repaired and passes its
transitive evidence gate. This checkpoint does not qualify a model or claim
T2 inference readiness.

## Verified

- `t2-readiness-packet.json` is `valid: true`, `ready: true`, with CP2 and CP3
  complete only after following the wrapper, decision, and typed artifact
  references and verifying every SHA-256.
- CP2 content was checked from the actual context configuration, metadata,
  nine-probe JSONL, report, and validation records. It remains packet-only:
  `model_behavior_claim: false`, no model server, and no Pod.
- CP3 content was checked from the actual Docker attestation, offline and
  Docker test results, and empty evaluator-container inventory. It remains an
  evaluator-integrity result, with `foundation_qualified: false`.
- `negative-complete-only-report.json` proves that a `status: complete` wrapper
  without decision and artifact references is rejected.
- `historical-packet-rejection-report.json` revalidates the preserved
  `runs/2026-09-23-t2-readiness-review/t2-readiness-packet.json` and rejects
  both of its complete-only wrappers. The historical packet was not rewritten.

## Limits and next action

This repair establishes an auditable CP4 packet boundary only. It does not
establish live model behavior, context capacity, tool use, coding capability,
human review, or foundation qualification. The active diagnostic Pod uses a
separate profile (RTX PRO 6000 Blackwell, vLLM 0.11.0, Transformers 4.57.1,
max length 8192) and is not the frozen T2 runtime (A100-SXM4-80GB, vLLM 0.28.0,
Transformers 5.8.0, max length 32768). The diagnostic manifest also records a
4125-byte/Git-blob chat-template artifact, while CP2 canonical provenance pins
the 4040-byte standalone template SHA; that discrepancy remains unresolved
and cannot be used as matched T2 evidence.

Next safe action: parent review should record this CP4 repair, keep the
historical packet on hold, and resolve the exact live runtime and chat-template
provenance before any T2 qualification run. No Pod or launcher was changed by
this checkpoint.

## Evidence

- `manifest.json`
- `t2-readiness-packet.json`
- `t2-readiness-report.json`
- `negative-complete-only-packet.json`
- `negative-complete-only-report.json`
- `historical-packet-rejection-report.json`

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
