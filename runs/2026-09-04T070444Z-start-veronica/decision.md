# Recovery start — Candidate A answered; deadline shutdown confirmed

**Decision: recovery chat succeeded on the proven vLLM 0.11.0 stack. T2 matched-runtime hold is unchanged.**

## Authorization and spend

The owner asked to fix the non-responding model after `runs/2026-09-04T065235Z-start-veronica` failed to install vLLM 0.17.0 + Transformers 5.8.0. Duration remained 60 minutes from the earlier "One hour is fine." Profile: default `config/runpod-core.json` (Candidate A, vLLM 0.11.0 / Transformers 4.57.1). This is not a four-model T2 comparison.

Created Pod `pbym3oq2acr3uj` / `veronica-core-20260904-070546-55012b79` at **$1.59/hour**. Deadline `2026-09-04T08:05:46.345348Z`. Local watchdog requested termination; exact absence confirmed at **2026-09-04T08:05:58.979826Z**. Network volume retained. Keep-awake helper released. Do not reuse this approval.

## Verified

- UI opened at `http://127.0.0.1:8010` before inference (`startup-ui-ready.json`).
- Model files verified on the existing volume (`validated-model-manifest.json`).
- Direct and wrapper smokes produced real text and passed recall (`provider-smoke.json`, `wrapper-smoke.json`, `startup-ready.json` at 07:16:32 UTC).
- Smoke is not T2 qualification.

## Not verified

- Frozen T2 runtime (vLLM 0.17.0 + Transformers 5.8.0) remains unsatisfiable.
- Candidate B and both controls were not served.
- No signed model-selection decision.

## Next legitimate action

A new bounded start request is required for another Pod. A T2 comparison still needs one installable matched runtime frozen for all four models, then a separate compatibility run.
