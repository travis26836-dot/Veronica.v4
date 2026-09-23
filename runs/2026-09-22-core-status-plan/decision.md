# 2026-09-22-core-status-plan

**Decision:** The repository status and dependency-ordered Veronica Core plan
are recorded in
[`docs/CORE-STATUS-AND-EXECUTION-PLAN.md`](../../docs/CORE-STATUS-AND-EXECUTION-PLAN.md).

Verified in this planning increment: CP1 schema gate is complete; Docker
sandbox validation and full local tests are complete; foundation qualification,
persona, tools, memory, external integration, recovery, and release remain
open. The next bounded action is M1 CP2 actual-token context preparation. No Pod
was started or authorized by this increment.

Validation: documentation links and repository state were reviewed; the plan
keeps `TODO.md` authoritative and separates evidence-backed completion from
smoke/provisional work. Next action: implement CP2, record its own decision,
then stop for checkpoint review before CP3.

This run folder was created by the immutable initializer. Replace this stub with the recorded decision.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
