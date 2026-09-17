# Veronica.v4 project instructions

## Working continuity

- Apply Trav's CREATED skill for staged work. Read `docs/CURRENT-STATE.md` and
  `docs/CREATED-WORKING-SYSTEM.md` alongside the product checklist.
- Preserve the active branch's stated objective. A commit is a progress checkpoint;
  a push, merge, and completed milestone are separate events. Do not introduce a
  replacement branch for routine cleanup and lose the original workstream.
- End each work increment with evidence, remaining work, and the next action.
  Scheduled work may implement only an approved bounded item; roadmap existence
  alone is not permission to build every remaining feature.

## Product rules

1. Read `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, and the latest `runs/*/decision.md` before changing direction.
2. Build one capable Veronica core first. Basic text/chat precedes specialized modules, fine-tuning, billing, and production deployment.
3. Keep foundation weights unchanged during the initial alias/persona-wrapper stage.
4. Treat UI mode names as prompt presets until native model behavior has been verified.
5. Preserve the `Veronica` API alias and keep the upstream model configurable.
6. Keep donor projects read-only unless a specific component is deliberately ported and tested.
7. Keep source in `src/`, evidence in `runs/`, documentation in `docs/`, and prior research/media in `NON-SOURCE CODE/`.
8. Never mark a TODO item complete without evidence. Never call a mock response real model inference.
9. Do not create paid GPU resources without a bounded development deadline and current spending authorization.
10. Keep updates and handoffs short; link to the detailed plan instead of repeating it in chat.
11. For "Start Veronica", "launch Veronica", or "boot Veronica", use `.agents/skills/veronica-runpod-core/SKILL.md` and `scripts/start-veronica.ps1`. Ask one question if no duration was already specified: "How long would you like the pod to run? Default: 1 hour." Wait for the answer; keep one A100 80 GB and the $1.75/hour ceiling. The owner accepted supervision from the awake/connected computer; a fresh actual start request still authorizes each individual Pod. Configuration discussions are not paid-start requests.
12. Open the chat UI as soon as its wrapper is available; model loading and checks continue in the background. Do not make the owner wait for response tests before seeing or using the UI. Keep UI readiness separate from verified inference, and do not interrupt an active owner conversation for tests.
