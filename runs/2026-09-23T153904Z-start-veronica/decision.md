# A100 plus RTX PRO 6000 fallback start attempt — 2026-09-23

**Decision:** cancelled before Pod creation. The normal `Start Veronica` profile
now checks the requested A100-SXM4-80GB first, then the owner-directed NVIDIA
RTX PRO 6000 Blackwell Server Edition Secure fallback. This one-hour run carried
a $2.09/hour ceiling and one-GPU limit.

Live preflight at 15:39 UTC found both offerings out of stock in EUR-IS-1:

- A100-SXM4-80GB Secure: none; listed rate $1.59/hour.
- RTX PRO 6000 Blackwell Server Edition Secure: none; listed rate $2.09/hour.

`startup-cancelled.json` records `creationAttempted: false`; live inventory was
empty afterwards. No GPU billing, model load, or inference occurred. The exact
temporary keep-awake helper was stopped after the safe cancellation.

Evidence: `approval.json`, `profile.json`, `expected-model-manifest.json`,
`preflight.json`, and `startup-cancelled.json`.

Next: do not reuse this authorization. A fresh request can retry the configured
A100-then-Blackwell sequence when stock returns, or can explicitly change the
resource/price scope.
