# Shared Agent Coordination

This directory is the durable, tool-neutral accountability layer for Codex, Hermes, and GitHub Copilot.

```text
coordination/
  tasks/active/       one JSON record per claimed task
  tasks/completed/    immutable historical task records
  tasks/released/     handoff records whose paths are available to new claims
  handoffs/           human-readable handoffs generated on handoff or completion
  sessions/           optional unique session notes; never one shared mutable log
```

Use `python scripts/collaboration.py --help`. Claims use an atomic repository lock and reject known path overlap. A `handoff` releases its paths and moves the original identity-bearing record to `tasks/released/`; a `blocked` task retains its claim. Each task owns its own record, which avoids multiple agents appending to one fragile shared file.

Completed and released history is append-only in meaning: correct an earlier claim with a new task that references it through `supersedes`; do not rewrite another agent's record. Search task records and handoffs before repeating work, especially `ruled_out` findings.

Do not store secrets, credentials, private transcripts, paid authorization files, or raw sensitive responses here.
