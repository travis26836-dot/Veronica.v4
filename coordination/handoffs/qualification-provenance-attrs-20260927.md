# Handoff: qualification-provenance-attrs-20260927

**Status:** completed

**Agent:** codex / codex-desktop

**Started:** 2026-09-27T09:06:57Z

**Ended:** 2026-09-27T09:09:16Z

## Scope

Preserve frozen provenance bytes and regenerate the CP2 template pin from the immutable raw snapshot; retain a fail-closed live T2 gate.

## Files changed

- `.gitattributes`
- `tests/test_context_gate.py`

## Tests

- Fresh checkout: uv run pytest tests/test_context_gate.py tests/test_qualification.py -q (11 passed)
- Fresh checkout: uv run python scripts/verify_t2_qualification.py protocol (valid, four models, ten tracks)

## Evidence

- `commit:b4ffe0c`

## Limitations

- The historical 4,125-byte template artifact is rejected and cannot qualify a live runtime.
- Transitive CP4 validator integration and all live evidence remain pending.

## Ruled out

- No Pod, model server, model download, response collection, or foundation selection.

## Next safe action

Cherry-pick e8086a8 and b4ffe0c onto the clean integration branch before bringing in the CP4 validator; require serving runtime attestations to match raw provenance hashes.
