# v3 Terminal Donor Inventory

**Status:** locally inspected; donor is read-only  
**Task:** `terminal-v3-donor-inventory-20260923`

## Exact donor

The complete terminal and action-feed implementation is in:

- `C:\Users\raine\.codex\worktrees\fd8f\Veronica AI\veronica-home\app.js`
- `C:\Users\raine\.codex\worktrees\fd8f\Veronica AI\veronica-home\index.html`
- `C:\Users\raine\.codex\worktrees\fd8f\Veronica AI\veronica-home\styles.css`
- `C:\Users\raine\.codex\worktrees\fd8f\Veronica AI\veronica-home\server.py`

It is a richer later local-console donor than `C:\Users\raine\veronica-ai-v2`. The latter has only a minimal `tools/terminal.py` subprocess helper and styling for an image-backend loading gate; it does **not** contain the complete interactive terminal panel.

## Reusable presentation pieces

The donor already has the interaction shape requested for the boot dashboard:

- `renderActionFeed()` in `app.js`: renders timestamped event records, command/path previews, status, stdout/stderr, and errors.
- `imageStartupView()` / `renderImageStartupGate()`: a live state machine with waiting, starting, ready, and error states; a bounded rolling feed; and visibly active/done steps.
- `index.html` lines 78-80: existing Action Feed mount point.
- `styles.css`: terminal-style monospaced feed, status colors, active/done indicators, animated loading core, reduced-motion support, and responsive behavior.

The current v4 UI already has compatible foundations in:

- `src/veronica_core/static/index.html`: live-activity rail.
- `src/veronica_core/static/app.js`: safe DOM text insertion, health polling, and a small activity list.
- `src/veronica_core/static/styles.css`: Veronica visual tokens, a monospaced activity feed, and loading-state styling.
- `src/veronica_core/app.py`: FastAPI home page and API seam.

## Do not port as startup telemetry

The donor's actual terminal executor is deliberately separate from the loader:

- `server.py` exposes `/api/terminal/status`, `/api/terminal/history`, `/api/terminal/assess`, and `/api/terminal/run`.
- It includes workspace confinement, risk assessment, approval staging, timeouts, output truncation, and action history.
- v4 has not reached E3 native tools, so copying that execution surface now would falsely advance an unfinished Core milestone.

The boot screen needs a **read-only startup-event feed**, not a command executor. It may visually look like Veronica's terminal, but it must never expose commands, credentials, raw SSH output, private key paths, or a way to run anything.

## Recommended v4 seam

Build a new read-only endpoint (for example `GET /api/startup`) owned by the startup-dashboard task. It should return an ordered, sanitized event list from the active run directory and nothing else. Map real artifacts to events only after each exists:

1. `startup-intent.json` — request accepted; deadline and selected profile (no approval contents).
2. `preflight.json` — capacity and cost gate passed, or a truthful no-stock/error state.
3. `supervised-state.json` — exact Pod created and supervision armed.
4. `bootstrap-start.json` — persistent-volume validation and model bootstrap started.
5. `tunnel.json` and `wrapper-process.json` — local bridge and chat wrapper started.
6. `startup-ui-ready.json` — UI usable; inference remains pending.
7. `provider-ready.json` — model alias responds; inference still not claimed.
8. `startup-ready.json` — wrapper verification completed.

Use file timestamps and only whitelisted JSON fields. Do not read `bootstrap-log.txt` into the browser; it can be redacted evidence but is not a browser contract. The event schema should include `id`, `atUtc`, `phase`, `level`, `message`, and optional `detail`; phase is one of `queued | preflight | pod | volume | bootstrap | tunnel | wrapper | provider | verified | failed`.

The UI should start rendering as soon as the local wrapper exists, preserve the user chat surface, and poll this endpoint until terminal state `verified` or `failed`. The display can use the donor's text-feed treatment and line-by-line typing effect, but each typed line must correspond to a returned event; do not invent progress.

## Validation required

- Unit-test artifact-to-event mapping for success, no-stock, failure, and partial-start paths.
- Verify no approval/private-key/token fields appear in serialized output.
- Browser test: UI appears before provider readiness; events remain ordered; ready state is only shown when `startup-ready.json` exists.
- Browser test: disconnect/error remains visible and no false “model loaded” claim is shown.

## Evidence

Read-only inspection completed on 2026-09-23. The currently running v4 start run proves the named inputs exist at `runs/2026-09-23T163608Z-start-veronica\`: `startup-intent.json`, `preflight.json`, `supervised-state.json`, `bootstrap-start.json`, `tunnel.json`, `wrapper-process.json`, `startup-ui-ready.json`, and `provider-ready.json`.

## Next safe action

The frontend/dashboard specialist should claim the v4 static UI plus the new read-only startup-status endpoint, implement the sanitised event contract first, then port only the donor's display patterns.
