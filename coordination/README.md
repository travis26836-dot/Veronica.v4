# Shared Agent Coordination

This directory is the durable, tool-neutral accountability layer for Codex, Hermes, and GitHub Copilot.

```text
coordination/
  tasks/active/       one JSON record per claimed task
  tasks/completed/    immutable historical task records
  handoffs/           human-readable handoffs generated on completion
  sessions/           optional unique session notes; never one shared mutable log
```

Use `python scripts/collaboration.py --help`. Claims use an atomic repository lock and reject known path overlap. Each task owns its own record, which avoids multiple agents appending to one fragile shared file.

Completed history is append-only in meaning: correct an earlier claim with a new task that references it through `supersedes`; do not rewrite another agent's record. Search completed records and handoffs before repeating work, especially `ruled_out` findings.

Do not store secrets, credentials, private transcripts, paid authorization files, or raw sensitive responses here.
