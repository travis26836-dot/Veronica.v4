# Veronica.v4 current state

Update deliberately; timestamps do not determine authority.

- Product contract: docs/SOURCE-OF-TRUTH.md.
- Product execution checklist: TODO.md.
- Active branch: feature/complete-todo-milestones.
- Branch objective: advance the unfinished TODO and milestones, committing
  verified increments. The branch objective is not complete.
- Last accepted live checkpoint: runs/2026-09-13T135326Z-start-veronica/decision.md.
- Maintenance checkpoint: runs/2026-09-16-uncommitted-cleanup/decision.md.
- Working-system plan: docs/CREATED-WORKING-SYSTEM.md.
- Collaboration contract: docs/AGENT-COLLABORATION.md.
- Collaboration integration: runs/2026-09-17-collaboration-integration/decision.md.

Cleanup commits 48645d1, d3f9e26, and 22b7140 were fast-forwarded onto the
original milestone branch. They are local; no push occurred in this task.
The cleanup branch remains as a historical pointer and is not the active goal.

Foundation qualification remains pending. Historical run files are not evidence
of a currently running provider or authorization for a new paid run.

Planning checkpoint: runs/2026-09-17-core-completion-plan/decision.md.
Core completion sequence: docs/CORE-COMPLETION-PLAN.md (proposed).

Collaboration code is integrated locally on the milestone branch. Both working
continuity and collaboration preflight rules are retained. Claims are local to
each checkout; use one writer rather than assuming cross-worktree locking.

Next action: finish the T2 qualification-readiness packet. Scheduling automation
is deferred behind core delivery. No CREATED automation has been installed;
this checkpoint does not complete a product milestone or authorize paid compute.
The integration decision records the separate remote PR status.

Qualification execution checkpoint:
runs/2026-09-17-qualification-execution-gate/decision.md. Generated-code reporting
now refuses execution until a complete sandbox is verified. The previous network
namespace alone was insufficient. Next local implementation: isolated execution
backend and boundary tests, followed by schema and long-context readiness gaps.
