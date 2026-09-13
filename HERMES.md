# Veronica.v4 Hermes entrypoint

Before doing any work, read and follow `AGENTS.md`, `docs/AGENT-COLLABORATION.md`, and `docs/CURRENT-STATE.md`. These repository records, not private Hermes plans, chat history, kanban state, or model memory, are authoritative.

Run `python scripts/collaboration.py preflight`. Claim non-trivial work before editing with surface `hermes-desktop`, `hermes-ide`, or `hermes-terminal`; do not edit paths claimed by another active task; and finish with a durable handoff or completion record.

The installed Hermes CLI confirms that `AGENTS.md` is loaded normally. Do not use `--ignore-rules` or `--safe-mode` for project work. If a different Hermes surface does not load this adapter, the opening prompt must say: `Read HERMES.md and AGENTS.md before making changes.`

For any Veronica start request or paid RunPod action, follow `.agents/skills/veronica-runpod-core/SKILL.md` and the fresh authorization rules in `AGENTS.md` exactly.
