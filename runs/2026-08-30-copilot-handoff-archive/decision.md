# Automatic handoff archive — 2026-08-30

## Outcome

The completed Codex-to-Copilot handoff is configured to archive when a new VS Code Copilot agent session begins. The hook runs `scripts/archive-copilot-handoff.ps1` from `.github/hooks/archive-copilot-handoff.json`.

## Exact archive scope

The script moves only these completed handoff documents to `docs/COMPLETED/copilot-handoff-2026-08-30/`:

- `docs/CODEX-CREDIT-CHECKPOINT.md`
- `docs/COPILOT-HANDOFF.md`
- `docs/COPILOT-RESTART-PROMPT.md`

It writes an `archive-manifest.json` timestamped at the real move. It is idempotent after that manifest exists and rolls already-moved files back if a move fails.

## Retained evidence

`runs/2026-08-30-copilot-handoff/` is not moved. Project policy requires run evidence to remain in `runs/`; it records the completed handoff and does not remain an active instruction surface.

## Verification

- `scripts/archive-copilot-handoff.ps1 -DryRun`: passed; reported all three exact sources and did not move them.
- `scripts/build.ps1`: passed; 13 tests passed, with the existing Starlette TestClient deprecation warning.

## Status

Configured, pending the first VS Code Copilot agent-session prompt. No archive has been claimed before that trigger occurs.
