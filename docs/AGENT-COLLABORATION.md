# Veronica.v4 Multi-Agent Collaboration Contract

**Status:** mandatory project rule

**Owner:** Travis

**Applies to:** Codex, Hermes, GitHub Copilot, every model selected inside those products, and every Desktop, IDE, terminal, cloud, or automation surface

## 1. Authority and truth

Use this precedence when instructions disagree:

1. The owner's current explicit instruction.
2. Safety, permission, privacy, paid-resource, and external-action gates.
3. `docs/SOURCE-OF-TRUTH.md` and `TODO.md`.
4. `docs/CURRENT-STATE.md` and its named decision record.
5. This contract and `AGENTS.md`.
6. Agent-specific adapter files.
7. Private chat history, plans, memories, summaries, and assumptions.

Report unresolved conflicts. Never silently choose the most convenient instruction. Repository evidence is authoritative over an agent's recollection. A mock, wrapper, port, health response, log line, or `/v1/models` result is not proof of real inference.

## 2. Required preflight

Before changing a file:

1. Confirm the repository root, worktree, branch, and `git status`.
2. Read `AGENTS.md`, this file, `docs/CURRENT-STATE.md`, `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, and the decision explicitly named by `docs/CURRENT-STATE.md`.
3. Search `coordination/tasks/active/`, `coordination/tasks/completed/`, and `coordination/handoffs/` for related work, evidence, failures, and ruled-out approaches.
4. Run `python scripts/collaboration.py preflight`.
5. For non-trivial work, create a claim before editing.

Do not choose a "latest" run by modification time. Update `docs/CURRENT-STATE.md` deliberately when a newer decision becomes authoritative.

## 3. Identity and task claims

Every claim records the agent family, specific model when known, surface, worktree, branch, base commit, scope, intended paths, start time, and status. Agent family and surface are separate: changing the model inside Copilot does not change the surface's obligations.

Only one active task may own a file, feature, test suite, operational procedure, or overlapping path at a time. The claim lock makes creation atomic, but agents must still re-run preflight after switching branches or worktrees. Unclaimed trivial reads are allowed; edits are not.

Never overwrite, reset, discard, stash, clean, reformat, relocate, or "fix" another task's changes without explicit owner approval. Existing dirty changes belong to their prior author until established otherwise.

## 4. Work and evidence

Keep changes narrow and inspect `git status` before and after work. Record:

- actions completed;
- files changed;
- commands and tests actually run;
- evidence paths or commit IDs;
- limitations and unverified claims;
- failed or ruled-out approaches and why;
- the next safe action.

A prior result may prevent duplicate work only when its evidence exists and its inputs, configuration, revision, and acceptance criteria still apply. If re-running work is necessary, record exactly what changed. Never suppress verification merely to save tokens.

Use these truth labels consistently: `proposed`, `implemented`, `locally-tested`, `live-verified`, `production-ready`, `blocked`, `superseded`, and `retracted`. Do not upgrade a label without proportionate evidence.

## 5. Handoffs and disagreements

Use `python scripts/collaboration.py handoff` when another agent must continue. A handoff must include scope, files, tests, evidence, limitations, ruled-out approaches, and next action. The receiving agent must verify the repository state before relying on it.

Never edit another agent's completed record to make history agree with a new conclusion. Create a new record that references and supersedes or retracts the earlier claim. The owner decides conflicts affecting behavior, scope, architecture, safety, privacy, cost, or external state.

## 6. Git and worktrees

Use a named branch and, for concurrent substantial work, a separate worktree. A worktree is isolation, not permission to ignore shared claims. Make focused commits only after validation. Do not amend, rebase, force-push, reset, delete branches/worktrees, or discard changes unless the owner explicitly requests it.

Never use `git add .` in a dirty worktree. Stage exact paths or reviewed hunks. Do not commit credentials, approval files, private transcripts, generated weights, disposable logs, or unrelated changes.

## 7. Protected actions

Fresh owner authorization is required for paid compute, purchases, publishing, sending messages, external commits or pushes, destructive data changes, releases, and other consequential external actions. Authorization is scoped to the stated action and is never reusable.

For Veronica, preserve the `Veronica` API alias, configurable upstream model, unchanged foundation weights during the wrapper/persona stage, prompt-preset status of unverified modes, evidence-first qualification, `src/` for source, `docs/` for documentation, `runs/` for evidence, and `NON-SOURCE CODE/` for retained non-source material.

## 8. Completion gate

Work is complete only when the intended result exists, appropriate validation passed, evidence is durable, the task record is complete, and the final `git diff` contains no unexplained overlap. Otherwise use `handoff` or leave the task active with an honest status.

This protocol coordinates agents through the repository. It does not claim that separate products share live memory, tools, permissions, or settings.
