# Reusable RunPod core workflow — 2026-08-30

## Outcome

Created the versioned `config/runpod-core.json` profile and `.agents/skills/veronica-runpod-core/SKILL.md`. A Codex skill-directory junction points at the same canonical project skill; Copilot can discover `.agents/skills/` directly. No duplicate skill instructions or secrets are stored.

Added reusable Python tools for pinned provenance capture, live inventory/price preflight, safe on-Pod model preparation, basic real-response testing, and scoped shutdown. Retired the old environment example to `ARCHIVE/runpod-legacy/runpod.env.example`. The legacy launcher now calls the fail-closed controller instead of using broken timer flags. No old run evidence was moved or rewritten.

## Completed verification

- Build/contract validation passed; 22 tests passed with one existing Starlette TestClient deprecation warning. These are offline wrapper/safety/integrity tests, not inference.
- Skill validator passed; Bash entrypoint syntax passed.
- Captured candidate/control cards, full Apache-2.0 license files, configurations, Hub metadata, and expected hashes. Both license snapshots have SHA-256 `05cab46843576551502bfdf712f84e93e6e9590d9997306ed4f6635ef82811d9`.
- Manifest expects 27 files, 61,084,222,203 bytes, including 13 weight shards. It describes expected source artifacts; remote actual files remain unverified.
- Live preflight: CLI 2.12.0, zero Pods, volume `v53gj9flzs` in `EUR-IS-1`, A100-SXM4-80GB listed at $1.59/hour with Low stock. See the timestamped preflight JSON.
- Runtime choices are compatibility candidates only: pinned RunPod PyTorch 2.8/CUDA 12.8 image, vLLM 0.11.0, Transformers 4.57.1. No GPU install, model load, API response, or UI inference occurred. Development serving is restricted to Pod loopback plus SSH; public deployment remains out of scope.

## Critical correction and launch hold

The owner authorized one two-hour Pod at up to $1.60/hour **with automatic termination**. Before creating it, CLI update revealed that the termination flag was removed. RunPod's [official report](https://github.com/runpod/runpodctl/pull/330) confirms the flags never worked: the backend accepted them while continuing to bill beyond the deadline. The [restoration PR](https://github.com/runpod/runpodctl/pull/331) was still open and blocked on backend enforcement when inspected.

The old starting procedure's shutdown guarantee was incorrect. No paid Pod was created, and no model weights were downloaded. New `start` deliberately refuses creation; it is not a completed deployment adapter. Do not downgrade to a binary that advertises the broken flag or clear the hold by editing a boolean.

Local timers depend on this computer staying awake/online; on-Pod watchdogs depend on container startup and continued execution. Neither provides the independent shutdown protection previously promised. Next: establish and test a suitable independent termination controller, or obtain owner authorization for a supervised/alternative shutdown arrangement. Then implement the deployment adapter, validate the actual model files, load the model, run provider and wrapper smoke tests, inspect a UI conversation, and confirm Pod termination while retaining the volume.

The approval is recorded for this one run only and does not authorize future/replacement Pods. No model milestone is marked complete by this preparation work.
