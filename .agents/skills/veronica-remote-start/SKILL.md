---
name: veronica-remote-start
description: Start or stop Veronica from a mobile/cloud-triggered GitHub Actions workflow without bypassing the RunPod core safety contract.
---

# Veronica remote start

Use this skill only for a remote invocation when the workstation is unavailable.
The entry point is the `Veronica remote start` GitHub Actions workflow. It
delegates deployment to `scripts/runpod_core.py` and
`scripts/supervised_runpod.py`; it is not a second deployment profile.

## Safety contract

- Use `config/runpod-core.json` for the model, volume, GPU limits, fallback
  policy, and duration ceiling.
- `plan` is read-only and creates no Pod.
- `start` requires a fresh workflow dispatch with `authorization=START_VERONICA`
  and approval of the protected `veronica-remote-start` environment.
- Credentials are GitHub secrets only; never put them in inputs, logs, artifacts,
  or run evidence.
- The controller creates at most one Pod and never creates a replacement.
- Shutdown is controller-supervised, not platform-enforced. The workflow must
  remain alive until the deadline or a separate `stop` dispatch confirms absence.
- Persistent storage is retained.

## Remote access boundary

The workflow currently provides mobile-triggered control, logs, and downloadable
evidence. It does **not** expose vLLM or the local wrapper publicly. A remote
chat relay requires a separately authenticated service and must not be added by
opening the model server's port.
