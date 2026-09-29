# Stage 1 text session — 2026-09-29

**Status:** live-verified smoke, not foundation qualification.

Pod `dupf56vpvwn7rm` (`veronica-core-20260929-115308-235f83ec`) ran one A100 80GB Secure in EUR-IS-1 at $1.59/hour under a $1.75 ceiling. The supervised deadline fired. `termination.json` records confirmed absence at 2026-09-29T12:53:14Z. Live inventory is empty. Volume `v53gj9flzs` remains.

## What the live model did

- Official provider and wrapper smokes passed the automated nonempty/recall checks. Evidence: `provider-smoke.json`, `wrapper-smoke.json`.
- Coding reply `is_even` was executed locally; three asserts passed.
- Adult multi-turn recalled `red silk`, Mara, and Jon. Evidence: `stage1-required-tests.json`.
- Reasoning failed review. The model claimed 3/5 for two red draws without replacement. The correct value is 3/10.
- Strict JSON image request matched the required fields. A revision changed the seed to 42. Evidence: `live-gap-tests.json`.
- The model emitted `render_image`. After the wrapper restart, the wrapper executed it and returned `not rendered` plus the exact prompt. No image was generated. Evidence: `live-tool-execution.json`.

## Limitations

- UI readiness was earlier than inference. `startup-ready.json` is the launcher's automated smoke, not capability qualification.
- The SSH tunnel dropped during the wrapper restart and was restored before the tool-execution check.
- Platform termination was not armed. Shutdown was the local watchdog.
- Source changes for the handoff stub are local and uncommitted.

## Next safe action

Review the reasoning failure before treating this model as qualified. The image handoff is a stub only. Do not start another pod for paperwork.
