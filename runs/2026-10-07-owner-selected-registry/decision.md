# 2026-10-07-owner-selected-registry

**Decision:** Align the frozen offline comparison with owner-selected Candidate
A and its active official control. Candidate B and its control are retired and
excluded. This is protocol readiness only; Candidate A remains unqualified and
no paid compute or inference was started.

## Evidence

- `config/model-registry.json` records `owner_selected`, Candidate A as
  `selected_foundation`, and Candidate B/control as `retired_not_selected`.
- `config/t2-qualification.json` freezes the active pair and two chat tracks.
- `PYTHONPATH=src python scripts/verify_t2_qualification.py protocol` reports
  `protocol_ready: true`, two models, one pair, four model-track runs, and
  `foundation_qualified: false`.
- `PYTHONPATH=src python -m pytest tests/test_qualification.py tests/test_contracts.py -q`
  passed 18 tests; `scripts/validate_contracts.py` reports `ok: true`.

## Limits

- Owner selection does not prove T2 qualification; signed adjudication remains
  pending.
- This checkout does not contain the CP2 context configuration or its packet
  builder (`config/t2-context.json`, `src/veronica_core/context_gate.py`, or
  `scripts/generate_context_packet.py`), so CP2's tokenizer matrix could not be
  updated or revalidated here.
- No model downloads, inference, paid compute, or foundation-weight changes.

## Next safe action

Apply the same active-model exclusion to the CP2 config/builder in the checkout
that contains those files, then rebuild and validate the complete CP2/CP4
packet before any separately authorized live run.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
