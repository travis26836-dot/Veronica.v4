# Veronica.v4 GitHub Copilot instructions

Before doing any work, read and follow `AGENTS.md`, `docs/AGENT-COLLABORATION.md`, and `docs/CURRENT-STATE.md`. They are the shared contract for Codex, Hermes, GitHub Copilot, and every model selected inside Copilot.

Run `python scripts/collaboration.py preflight`. Claim non-trivial work before editing, identify the surface as `copilot-vscode`, `copilot-cli`, or `copilot-cloud`, and never edit a path claimed by another active task. Finish with a durable handoff or completion record. Do not use private chat history, Copilot session checkpoints, or model-specific memory as repository authority.

For "Start Veronica", "launch Veronica", or "boot Veronica", follow `.agents/skills/veronica-runpod-core/SKILL.md` and the paid-action rules in `AGENTS.md`. A current explicit start request authorizes only one bounded run. Never reuse an old approval or infer live model readiness from saved evidence.

The legacy `SessionStart` archival hook may preserve the completed 2026-08-30 handoff, but it is not the current coordination system and does not override `docs/CURRENT-STATE.md` or `coordination/`.
