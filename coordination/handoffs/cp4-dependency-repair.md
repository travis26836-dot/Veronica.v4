# Handoff: cp4-dependency-repair

**Status:** completed

**Agent:** codex / codex-desktop

**Started:** 2026-09-23T08:36:20Z

**Ended:** 2026-09-23T08:48:04Z

## Scope

Repair CP4 dependency validation to require transitive hashes and real CP2/CP3 artifact checks; preserve historical packets

## Files changed

- `docs/evals/T2-READINESS-PACKET.md`
- `runs/2026-09-23-cp4-dependency-repair`
- `scripts/build_t2_readiness_packet.py`
- `src/veronica_core/qualification_packet.py`
- `tests/test_qualification_packet.py`

## Tests

- uv run pytest tests/test_qualification_packet.py tests/test_qualification.py tests/test_schema_gate.py -q (16 passed)
- uv run python scripts/build_t2_readiness_packet.py validate --packet runs/2026-09-23-cp4-dependency-repair/t2-readiness-packet.json --report runs/2026-09-23-cp4-dependency-repair/cli-validation-report.json (valid=true, ready=true)
- uv run pytest tests -q -r a (one pre-existing runpod-core failure from unrelated dirty config/runpod-core.json)

## Evidence

- `runs/2026-09-23-cp4-dependency-repair/t2-readiness-report.json`
- `runs/2026-09-23-cp4-dependency-repair/negative-complete-only-report.json`
- `runs/2026-09-23-cp4-dependency-repair/historical-packet-rejection-report.json`

## Limitations

- Historical 2026-09-23 review packet is preserved and now rejected because its complete-only wrappers lack transitive evidence.
- Active diagnostic Pod and chat-template provenance remain mismatched to frozen T2; no model inference or T2 qualification is claimed.
- Full suite has one unrelated failure: tests/test_runpod_core.py::test_saved_start_defaults_are_bounded_and_supervised sees a dirty config/runpod-core.json fallback.

## Ruled out

- No Pod, launcher, TODO, CURRENT-STATE, or active runtime changes.

## Next safe action

Parent should record the CP4 repair, keep live T2 on hold, and resolve exact runtime plus chat-template provenance before any qualification run.
