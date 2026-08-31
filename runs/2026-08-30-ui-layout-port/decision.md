# Chat surface port — 2026-08-30

## Outcome

The v4 chat interface now uses the selected visual foundation from the read-only donor at `/home/dubs/code/veronica-ai-v2/veronica-home`: celestial background, Veronica mark, icon assets, Cinzel/Rajdhani/JetBrains Mono typography, three-column desktop layout, and responsive single-column behavior.

## Deliberate boundary

Only layout, design assets, and behaviors compatible with v4's existing contract were ported. The legacy Image Studio, workspaces, tool queue, workstation event stream, and image backend controls were not imported because their APIs do not exist in v4. The Studio remains visibly deferred until the text core is proven.

Live interface updates are evidence-based: the UI polls `/api/health`, displays the actual provider state, records actual refreshes and chat outcomes, and updates the local clock. It does not fabricate tool execution, streaming output, or model availability.

## Verification

- `node --check src/veronica_core/static/app.js`: passed.
- `scripts/verify-local.ps1`: 13 tests passed; one existing Starlette TestClient deprecation warning remains.
- Served assets: celestial background and Veronica logo both returned HTTP 200 in the wrapper test.
- Rendered desktop check: chat layout, status controls, conversation mode, composer, and activity rail were present; no console errors.
- Rendered 390px check: Chat Workspace and Send control stayed visible; the desktop-only activity rail was hidden; no console errors.

## Decision

Checkpoint 1 is complete. This is a UI-only port and does not represent real model inference. The next active checkpoint is Candidate A storage integrity.
