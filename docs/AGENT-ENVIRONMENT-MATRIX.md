# Agent Environment Matrix

This file separates repository-wide rules from settings that differ by product, surface, account, host, or session. Record observed behavior; never copy secrets into this matrix.

| Surface | Repository instruction entrypoint | Project settings | Durable shared state | Notes |
| --- | --- | --- | --- | --- |
| Codex Desktop | `AGENTS.md` | trusted `.codex/config.toml`, plus host/user policy | `docs/`, `coordination/`, Git | App capabilities, permissions, memories, and tools may differ by host/session. |
| Codex VS Code | `AGENTS.md` | trusted `.codex/config.toml`, extension/host settings | same | Confirm correct worktree and restart the agent after instruction changes. |
| Codex CLI | `AGENTS.md` | user config plus trusted project config | same | Launch from the intended worktree; instruction discovery occurs per launched session. |
| GitHub Copilot VS Code | `.github/copilot-instructions.md`, then linked shared rules | VS Code/Copilot settings | same | The selected model does not replace the repository protocol. |
| GitHub Copilot cloud | `.github/copilot-instructions.md`, then linked shared rules | GitHub repository/agent settings | same after branch/PR checkout | Verify branch and remote state; do not assume local dirty changes exist remotely. |
| Hermes Desktop/IDE/terminal | `AGENTS.md` is loaded normally; `HERMES.md` is the concise adapter | Hermes host/session settings | same | Verified from the installed Hermes CLI help; do not launch with `--ignore-rules` or `--safe-mode` for project work. |

## Repository-controlled settings

- Project instructions and authority documents.
- Task claims, handoffs, evidence pointers, and status vocabulary.
- Project-safe Codex sandbox default.
- Which VS Code tasks are exposed to agents.
- Source, documentation, and evidence locations.

## Host-controlled settings

- Authentication, credentials, account limits, billing, model availability, extensions, and installed tools.
- User-level prompts, memories, approval policies, telemetry, notification preferences, and provider configuration.
- Desktop/IDE UI preferences and machine-specific paths.

Host-controlled settings must not be treated as project truth. When they affect reproducibility, record the setting name and observed value without credentials in the task record or run evidence.

## Known reconciliation decisions

- `.codex/config.toml` uses `workspace-write`, replacing the prior project-wide `danger-full-access` setting.
- The legacy two-hour paid VS Code task remains available to the owner but is not exposed to agents (`inAgents: false`).
- `docs/CURRENT-STATE.md`, not file modification time, selects the authoritative decision.
- The old Copilot archive hook is historical compatibility only; `coordination/` is the active cross-agent record.

Official OpenAI documentation states that Codex loads `AGENTS.md` as project guidance and trusted projects can load `.codex/config.toml`; some provider, authentication, host metadata, notification, profile, and telemetry settings remain user/host scoped.
