# A1 remaining chat-wrapper work — 2026-09-04

## Outcome

The Veronica wrapper now forwards real upstream SSE for `POST /v1/chat/completions` when `stream=true`, keeps `stream=false` unchanged, and refuses to fake a stream. The local chat page persists the browser session, adds retry / stop / copy / regenerate, and renders Markdown/code with HTML escaped.

Native tools, MCP, memory, fine-tuning, and T2 four-model comparison were not implemented. The live paid Pod was not terminated and no replacement Pod was created.

## What changed

- `src/veronica_core/provider.py`: `stream()` relays `text/event-stream` (or a `data:` body). JSON completions and HTTP 501 become `StreamingNotSupported`. Other upstream failures stay generic `ProviderError` without leaking bodies or secrets.
- `src/veronica_core/app.py`: streaming path rewrites the public `model` alias to `Veronica`, returns 501 if the provider has no stream or cannot stream, 503 if the provider is down. Capabilities list `streaming_chat` as implemented and note loopback-only access without blocking the UI.
- `src/veronica_core/static/app.js` plus `index.html` / `styles.css`: `localStorage` conversation restore, Stop during generation, Copy / Retry / Regenerate, safe Markdown. The UI sends `stream=true` only when `/api/capabilities` reports `streaming_chat`, so an older wrapper process still accepts `stream=false`.

## Verification

- `UV_PROJECT_ENVIRONMENT=/tmp/veronica-core-py312 uv run --python 3.12 --frozen pytest tests/test_app.py tests/test_provider.py`: **20 passed**, existing Starlette TestClient deprecation warning unchanged. Log: `pytest.txt`.
- `node --check src/veronica_core/static/app.js` and `node tests/test_chat_markdown.js`: parse plus XSS/persistence helper checks.
- Mock wrapper on `127.0.0.1:8012` (not the live 8010 process, not GPU): curl SSE in `stream-smoke.txt` uses `"model":"Veronica"` and ends with `data: [DONE]`.
- Headless Chrome against that mock UI (`ui-browser.json`):
  - tokens streamed; Stop hid the in-flight request (`Generation stopped`, Retry appeared)
  - Retry replaced the stopped turn; Copy set notice to `Copied`; Regenerate control present
  - reload restored the transcript; New conversation stored `{messages:[]}` and showed the welcome line
  - `**Raine**` rendered as `<strong>`; fenced code shown as text; zero `<img>` / `<script>` nodes; `javascript:` links not promoted to `href`

## Not claimed

- Live GPU streaming through the already-running 8010 wrapper. That process still reports old capabilities (`streaming` planned) and `stream=true` as 501 until it is restarted against this source. `/api/health` on 8010 returned 500 during this check; that process was not restarted so an owner session would not be interrupted.
- Token/context usage display, native reasoning-effort controls, or auth beyond the capabilities loopback note.
- T2 qualification or E3 native tools.

## Decision

A1 streaming, session persistence, message controls, and safe Markdown are implemented and tested against mocks plus a local mock-provider browser. They are wrapper features, not foundation qualification. Remaining A1 items stay open.
