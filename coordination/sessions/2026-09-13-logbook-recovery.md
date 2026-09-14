# Legacy logbook recovery

**Date:** 2026-09-13

**Source worktree:** `C:/Users/raine/DEVELOPMENT/Projects/Veronica.v4.worktrees/multi-llm-logbook-collaboration`

**Source branch:** `agents/multi-llm-logbook-collaboration`

The source branch had no commits unique from `agents/multi-agent-collaboration`; it was an ancestor of the current branch. Two untracked collaboration documents were inspected before retirement:

- `docs/COPILOT-LOGBOOK.md` — SHA-256 `285BB3F1FB2DE8CB637FF4F89E822761AE0A8F5B46B351A61F87FEF5CEC83F3F`
- `docs/MULTI-LLM-HANDOFF-PROTOCOL.md` — SHA-256 `7059623E481ECCDC52C56BCAA45EC7C1BA83F566FEFBDCBC04EDED0718A4F970`

## Recovered ideas

- Shared, model-neutral records instead of private model logs.
- Agent, model, surface, session, timestamps, commits, actions, evidence, limitations, and ruled-out approaches as explicit fields.
- Evidence-linked claims and explicit superseding rather than silent rewriting.
- Fast search of prior negative results before repeating investigations.

These ideas were incorporated into `docs/AGENT-COLLABORATION.md`, `coordination/`, `config/schemas/collaboration-task.schema.json`, and `scripts/collaboration.py`.

## Deliberately superseded

The static Copilot-only commit log was not copied forward. Git remains the authoritative commit ledger, while a hand-maintained snapshot would immediately become stale and privilege one agent over the others. The new system records task meaning and evidence per agent while leaving commit facts in Git.

A single append-only JSONL file was also superseded. Concurrent products can collide while appending to one file, so the adopted design uses one atomically claimed JSON record per task plus one handoff file per completed task.
