# G0.1 integration review — 2026-09-26

Scope: compare `main` (`7435489`) with
`feature/complete-todo-milestones` and validate only the current evaluator
repairs in the isolated `agents/core-finish-20260925` worktree.

Result: the milestone carries 23 additional commits and 179 changed paths, so
it must not be merged wholesale into the dirty root checkout. A reviewed subset
was committed as `a6126ef`:

- fail-closed code extraction and source-span provenance;
- evidence redaction that keeps verified token-usage counters;
- host-side native-tool and context response graders;
- canonical LF hashing for repository text snapshots on Windows;
- a historical T2 rejection fixture needed by the qualification regression.

Validation:

- focused evaluator/context suite: 98 passed, exit 0;
- `pytest tests -q --ignore tests/test_start_veronica.py`: 310 passed, 8
  skipped, exit 0;
- `git diff --check`: exit 0 before commit.

Limitation: the startup-test file exceeded this terminal's 30-second command
window. No startup files were changed by `a6126ef`; the result remains pending
under G0.3. This record does not qualify a foundation model or authorize a Pod.

Next: reconcile the run-policy ceiling under G0.2, obtain a complete startup
test result under G0.3, then review the focused commit for integration.
