# Veronica restarted; UI opened early; Pod terminated

## Current run

The owner requested "Okay, let's START VERONICA", then "An hour is fine- start the UI as well". The current one-use approval covers one A100 80 GB, 60 minutes including startup, and at most $1.75/hour. This run created exactly one Pod, `wosedisslfwffs`, at the verified rate of $1.59/hour. The fixed deadline is 2026-08-31T04:41:05.562649Z (12:41 AM Eastern). The watchdog and Windows keep-awake helper were checked live. The owner subsequently requested STOP. Exact Pod absence was confirmed at 2026-08-31T04:40:57.489579Z; persistent storage was retained. The Windows keep-awake helper released at 04:41:02 UTC. Do not reuse this approval or extend the deadline silently.

The existing volume `v53gj9flzs` in `EUR-IS-1` was reused. All 27 model files, totaling 61,084,222,203 bytes, were checked against the pinned manifest. Candidate A revision remains `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`; weights and the Veronica public alias are unchanged.

## Verified evidence

- `preflight.json`, `supervised-state.json`: live price, ownership, and deadline.
- `validated-model-manifest.json`, `configuration-fingerprint.json`, `runtime-packages.txt`, `gpu.txt`, `server-command.json`: actual model/runtime evidence copied locally.
- `provider-smoke.json`, `wrapper-smoke.json`: real generated text and recall checks passed through the private connection and Windows wrapper.
- `startup-ready.json`: original launcher completed at 03:53:05 UTC.
- `ui-observation.json`: the owner sent "Veronica are you online?" in the live UI and received a generated response; browser status was observed as "Core connected". No test messages were inserted into the owner's active conversation.

## Owner correction: UI before checks finish

The owner explicitly required the UI to open while checks and tests continue, because the old startup order hid it for too long. The already-running original launcher could not safely change its process order. A second wrapper of this same project was therefore opened at `http://127.0.0.1:8011/`, using the exact same private tunnel and run credential, while the original launcher retained `8010` for its own checks. This creates no second cloud resource. The user is chatting on 8011; do not redirect/reload that page and lose their active conversation.

For subsequent starts, `scripts/start-veronica.ps1` now launches the standard 8010 UI immediately after bootstrap/tunnel setup, before waiting for model readiness and before inference tests. It writes `startup-ui-ready.json` with `inferenceVerified=false` and `checksPending=true`; the agent must open that UI while the launcher continues. `startup-ready.json` remains the separate verified completion record. Ownership, price, approval, model-integrity, timeout, and termination safeguards remain in place.

The project skill, AGENTS.md and starting procedure reflect this instruction. `start-supervised-wrapper.ps1` gained a validated optional port, defaulting to 8010. The new order passed the existing local suite: 109 tests passed, one skipped, with the pre-existing Starlette warning (`ui-first-offline-tests.txt`). `ui-first-startup-plan.json` records the new order. The revised launcher order itself still needs its next authorized cold start; the current live run began with the original order and used the early UI helper.

## Quality limits

Basic smoke success is not capability qualification. Both reasoning responses again began with the wrong 3/5 before ending at the correct 3/10. The wrapper coding response claimed that assertions passed without any model execution tool. The observed UI greeting also claimed background monitoring unsupported by this wrapper. Keep these failures visible in qualification work; do not describe the model as a fully qualified capable core.

## Closure

Closed on the explicit owner STOP request. `termination.json` confirms Pod wosedisslfwffs absent and persistent volume retained. Paid compute for this run has ended; separate persistent-storage charges remain. The cold restart and shutdown are verified. The revised UI-first launcher order still awaits its next authorized live start.

