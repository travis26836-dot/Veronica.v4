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
- Selective milestone queue: docs/NEXT-MILESTONES.md.
- Detailed verified status and execution plan: docs/CORE-STATUS-AND-EXECUTION-PLAN.md.

Cleanup commits 48645d1, d3f9e26, and 22b7140 were fast-forwarded onto the
original milestone branch. They are local; no push occurred in this task.
The cleanup branch remains as a historical pointer and is not the active goal.

**Model anchor (2026-09-29):** The installed Candidate A (huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated on volume v53gj9flzs) is the sole Veronica foundation per updated SOURCE-OF-TRUTH and model-registry.json. Candidate B is retired. No further shopping or forks. See config/model-registry.json and docs/SOURCE-OF-TRUTH.md section 4.

Foundation qualification remains pending. Historical run files are not evidence of a currently running provider or authorization for a new paid run. The anchor does not claim full qualification — it locks the engine so we stop restarting.

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
runs/2026-09-17-container-sandbox/decision.md (completed 2026-09-22). A pinned
local Docker sandbox now supports explicit supplemental code evaluation with
host-side fixture scoring and verified boundaries/resource limits. It supersedes
the temporary execution hold in runs/2026-09-17-qualification-execution-gate/decision.md;
missing runtime or failed verification still blocks execution. Live tests use
repository-owned programs, not model completions. Docker recovery was rechecked
after the owner reported a crash. M1 CP1 Schema Proven is now complete with
local evidence in runs/2026-09-22-cp1-schema-gate/decision.md. Next: M1 CP2
actual-token context packet, then CP3 evaluator integrity and CP4 frozen T2
readiness. Foundation qualification stays open; no Pod is required for M1.
