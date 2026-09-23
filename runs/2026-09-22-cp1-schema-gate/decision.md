# 2026-09-22-cp1-schema-gate

**Decision:** CP1 Schema Proven is complete; M1 continues at CP2.

Implemented an independent strict schema gate in `src/veronica_core/schema_gate.py`
and integrated its report into the existing capability report as the authoritative
structural sub-report. It validates the actual assistant response rather than
trusting `automatic_checks`. The gate covers exact JSON, required/allowed keys,
duplicate keys, malformed/nonfinite numbers, wrong roots, native function-call
shape, strict arguments, no-tool-call behavior, and rejects prose that merely
claims a tool ran.

Added `data/evals/schema-gate-negative.json` and tests for every failure family.
The frozen 60-case suite hash and model/runtime configuration were unchanged.

Validation:

- `uv run pytest tests/test_schema_gate.py tests/test_capability_reports.py -q` passed.
- `uv run pytest tests -q -r a` exited 0; only existing platform-specific tests
  were skipped.
- `uv run python scripts/verify_t2_qualification.py protocol` passed with four
  models, two pairs, ten required tracks, and `foundation_qualified=false`.
- `git diff --check` and collaboration validation passed.

No model inference, Pod, paid compute, or external action was used. This earns
CP1 only; semantic human review, actual-token context, live qualification, and
the remaining T2 gates are still open. A Pod is not required for CP1 or M1.

Next: implement CP2 actual-token context packet and record its checkpoint before
any M2 authorization request.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
