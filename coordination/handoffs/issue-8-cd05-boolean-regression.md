# Handoff: issue-8-cd05-boolean-regression

**Status:** blocked

**Agent:** copilot / copilot-cloud

## Scope

Preserve CD-05's generated boolean-parser regression, lock its independent
fixture expectations, and record an intervention plan without claiming a live
model result or T2 qualification.

## Files changed

- `tests/test_capability_reports.py`
- `runs/2026-10-07-cd05-boolean-regression/decision.md`
- `coordination/tasks/active/issue-8-cd05-boolean-regression.json`

## Tests and evidence

- Focused test suite: 17 passed.
- Pinned Docker execution: reported `isinstance` parser 7/8; exact-type repair
  8/8 on all unchanged CD-05 vectors.
- Baseline report: `runs/2026-09-23-live-coding/executable-code-report.json`
  (original boolean vector failure retained).
- Intervention status, hashes, and result limits:
  `runs/2026-10-07-cd05-boolean-regression/decision.md`.

## Limitations

- The prompt-only live intervention remains unevaluated; no matching active
  endpoint was supplied or verified, and no fresh bounded-run authorization
  was included.
- The raw baseline `results.jsonl` is absent from this checkout, limiting direct
  re-scoring of the original explanation claim.
- T2 coding qualification remains open.

## Ruled out

- No application parser was added; the regression concerns model-generated code.
- No expected fixture answer or baseline evidence was changed.
- The manual corrected-code Docker run is not presented as a model intervention.

## Next safe action

Recover the baseline response/runtime record and obtain a fresh authorized live
evaluation window before running the paired prompt comparison. Keep code
correctness and explanation/action truthfulness as separate outcomes.
