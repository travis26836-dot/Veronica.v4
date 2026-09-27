# One-hour Start Veronica attempt — 2026-09-23

**Decision:** cancelled before Pod creation. The owner requested a new one-hour
run. The launch used one A100-SXM4-80GB, one persistent volume, and a $1.75/hour
ceiling. Live preflight found no A100 stock in EUR-IS-1. The configured H100
fallback also had no stock and, at $3.49/hour, was outside this run's ceiling.

`startup-cancelled.json` records `creationAttempted: false`; live inventory was
empty after cancellation. No GPU billing or model inference occurred. The
temporary keep-awake helper ended after the safe pre-creation cancellation.

Evidence: `approval.json`, `profile.json`, `expected-model-manifest.json`,
`preflight.json`, and `startup-cancelled.json`.

Next action: use a fresh authorization only after an eligible one-GPU offer is
available within the agreed cap, or receive an explicit changed price/resource
scope. Do not reuse this approval or retry this run directory.
