# Veronica.v4 project instructions

## Mandatory multi-agent collaboration preflight

For project planning, session resumption and recurring reviews, read
`docs/PROJECT-WORKFLOW.md` and `docs/GOALS.md`. Select a bounded ready packet,
record evidence and update its status at handoff. Use
`.agents/skills/veronica-project-review/SKILL.md` for the recurring review procedure.

These rules apply to Codex, Hermes, GitHub Copilot, and every model or agent surface used in this repository.

Before changing any file, read `docs/AGENT-COLLABORATION.md`, `docs/CURRENT-STATE.md`, `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, and the decision record named by `docs/CURRENT-STATE.md`; then run `python scripts/collaboration.py preflight`. Claim non-trivial work with `python scripts/collaboration.py claim` before editing. Do not edit paths claimed by another active task. Finish with `handoff` or `complete`, including files changed, tests, evidence, limitations, and the next safe action. Repository records override private chat history or assumed memory.

1. Read `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, and the authoritative decision named by `docs/CURRENT-STATE.md` before changing direction. Do not select a decision by filesystem modification time.
2. Build one capable Veronica core first. Basic text/chat precedes specialized modules, fine-tuning, billing, and production deployment.
3. Keep foundation weights unchanged during the initial alias/persona-wrapper stage.
4. Treat UI mode names as prompt presets until native model behavior has been verified.
5. Preserve the `Veronica` API alias and keep the upstream model configurable.
6. Keep donor projects read-only unless a specific component is deliberately ported and tested.
7. Keep source in `src/`, evidence in `runs/`, documentation in `docs/`, and prior research/media in `NON-SOURCE CODE/`.
8. Never mark a TODO item complete without evidence. Never call a mock response real model inference.
9. Do not create paid GPU resources without a bounded development deadline and current spending authorization.
10. Keep updates and handoffs short; link to the detailed plan instead of repeating it in chat.
11. For "Start Veronica", "launch Veronica", or "boot Veronica", use `.agents/skills/veronica-runpod-core/SKILL.md` and `scripts/start-veronica.ps1`. Ask one question if no duration was already specified: "How long would you like the pod to run? Default: 1 hour." Wait for the answer; keep one GPU. The default start request is one A100 80 GB at $1.75/hour. The saved ceiling is $2.09/hour because the configured fallback GPU is capped at $2.09/hour. Do not collapse those two limits. The owner accepted supervision from the awake/connected computer; a fresh actual start request still authorizes each individual Pod. Configuration discussions are not paid-start requests.
12. Open the chat UI as soon as its wrapper is available; model loading and checks continue in the background. Do not make the owner wait for response tests before seeing or using the UI. Keep UI readiness separate from verified inference, and do not interrupt an active owner conversation for tests.
