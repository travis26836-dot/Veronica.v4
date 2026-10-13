# Shared Agent Coordination

This directory is the durable, tool-neutral accountability layer for Codex, Hermes, and GitHub Copilot.

```text
coordination/
  tasks/completed/    immutable historical task records
  handoffs/           human-readable handoffs generated on completion
  sessions/           optional unique session notes; never one shared mutable log

Git common directory/
  veronica-collaboration/
    tasks/active/     one shared JSON record per claimed task
    .claim-lock/      atomic lock shared by linked worktrees
```

Use `python scripts/collaboration.py --help`. Claims use an atomic lock and reject known path overlap across linked worktrees of the same repository. Checkout-local active records from older versions are also honored until completed; separate clones do not share live state. Completed history and handoffs remain in the checkout.

Completed history is append-only in meaning: correct an earlier claim with a new task that references it through `supersedes`; do not rewrite another agent's record. Search completed records and handoffs before repeating work, especially `ruled_out` findings.

Do not store secrets, credentials, private transcripts, paid authorization files, or raw sensitive responses here.
