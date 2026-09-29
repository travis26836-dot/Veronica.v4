# Handoff: start-gpu-alternatives

**Status:** completed

**Agent:** codex / codex-desktop

**Started:** 2026-09-23T08:22:45Z

**Ended:** 2026-09-23T15:40:32Z

## Scope

Configure user-authorized GPU alternatives within current limits

## Files changed

- `config/runpod-core.json`

## Tests

- Plan-only validation shows one-hour 2.09 cap; live preflight considered intended fallback

## Evidence

- `runs/2026-09-23T153904Z-start-veronica/preflight.json`

## Limitations

- Fallback currently has no stock

## Ruled out

- None recorded.

## Next safe action

Use configured A100 then Blackwell fallback for next fresh authorized start
