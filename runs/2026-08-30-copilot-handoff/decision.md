# Copilot restart handoff — 2026-08-30

## Safe checkpoint

The safe checkpoint is immediately after the verified UI port. No model files, weights, provider configuration, or paid RunPod resources were changed. This is the correct restart point because the next task—Candidate A artifact integrity—has a clear evidence boundary and can stop safely if the copied storage location is unavailable.

The agent could not inspect the account-level Codex credit meter. The handoff therefore records a conservative process guard: the operator checks the UI meter before a new checkpoint, and the agent stops at the active checkpoint boundary or the operator's 25% reserve, whichever comes first.

## Reconciliation

- Current branch: `main`; worktree is intentionally uncommitted and must be preserved.
- Verified build: `scripts/build.ps1` passed with 13 tests and one existing Starlette TestClient deprecation warning.
- Verified package: `dist/veronica_core-0.1.0-py3-none-any.whl`, SHA-256 `2E249DBFBDAF94A3F7754B974DF8925310E604ECB6575FF2048655D92E9D5E33`.
- Current model state: Candidate A revision is pinned but files remain unvalidated; no inference has occurred.
- Current UI state: v2 visual assets/layout were ported to v4, and only honest v4 health/request activity behavior is active.

## Restart instruction

Use `docs/COPILOT-RESTART-PROMPT.md` in VS Code Copilot. Its first and only task is Checkpoint A: Candidate A storage integrity. Do not create a Pod or start a model server until the copied artifact manifest is recorded and the owner supplies a current spend ceiling and UTC termination deadline.
