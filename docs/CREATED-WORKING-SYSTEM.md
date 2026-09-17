# Trav's CREATED working system

Status: proposed automation design; local workflow rules established. Scheduling
implementation deferred as of 2026-09-17 behind the core completion sequence in
docs/CORE-COMPLETION-PLAN.md. Retain this design for later use.
Owner: Travis. Pilot: Veronica.v4.

## C - Capture

Build a personal working system that turns approved goals into checked work,
durable evidence, and an unambiguous next action using Trav's CREATED skill.
Veronica's existing TODO remains its execution source of truth. This document
does not replace the product roadmap or declare its milestones finished.

Confirmed branch: `feature/complete-todo-milestones`.
A local commit saves a verified increment. A push publishes branch progress.
Neither completes the branch goal. Merge and milestone completion are separate
decisions requiring their own evidence and authorization.

## R - Research

Read AGENTS.md, docs/SOURCE-OF-TRUTH.md, TODO.md, docs/CURRENT-STATE.md,
and the decision records it names before choosing work.
The reusable skill lives at C:/Users/raine/.codex/skills/travs-created-workflow/SKILL.md.
The collaboration implementation is integrated on this milestone branch as of
2026-09-17. Use scripts/collaboration.py for task claims and handoffs. Claims are
per checkout, not globally synchronized across worktrees; retain one writer.

## E - Establish

One ordered queue and one writer per project. Each work item must name its
objective, CREATED stage, owner, allowed paths, inputs, output, validation,
failure state, approval boundary, evidence, and next action.
Use statuses proposed, ready, in-progress, locally-tested, blocked, and completed.
Use live-verified only with actual live evidence. Missing required inputs mean
blocked, not permission to invent scope or acceptance criteria.

Preserve the active branch through its stated goal. Create a new branch only
for a distinct workstream or required isolation, and record its relationship to
the original goal before switching. Never treat cleanup as product completion.

## A - Assemble

Implement three sequential processes, with one scheduler coordinating them:

1. Intake and planning: read the approved queue and current state; choose one
   eligible bounded item; record its inputs, ownership, and acceptance check.
2. Build and verify: implement the item, run appropriate checks, preserve failures
   and recovery evidence. Make local commits of exact reviewed files only.
3. Evidence and handoff: link the output, validation, commit, limitations, and next
   safe action. Update a TODO checkbox only when its stated proof exists.

These are proposed processes, not yet installed scheduled automations. Reuse the
existing collaboration tooling where suitable instead of inventing competing
task records. No separate simultaneous writers should work in this checkout.

## T - Test

Before scheduling: run one complete local cycle and one blocked-input case.
Verify that a restarted run finds the last durable handoff, that a repeated run
does not repeat completed work, and that an occupied task is not overwritten.
Confirm that failing validation cannot produce a completed status or commit.
Verify all three processes produce useful artifacts, not just status messages.

## E - Execute

Scheduling awaits the owner's scope and cadence choice. Automated construction
is limited to approved local work items and their named paths. A broad roadmap
does not authorize arbitrary implementation, paid compute, or external actions.
Preserve existing changes and stop on unresolved ownership or scope conflicts.
Paid starts, pushes, merges, publishing, messaging, and destructive changes need
authorization appropriate to the action. Never reuse historical launch approvals.
Notify on meaningful progress, completion, failure, or required input; stay quiet
when nothing actionable has changed.

## D - Document

Use new dated run folders; never overwrite prior evidence. Each handoff records
what changed, validation, limitations, failures, next action, and branch/commit.
Keep project evidence in the repository. Personal memory updates require an
explicit user request and do not substitute for repository evidence.

Next for the product: integrate collaboration and complete qualification
readiness under docs/CORE-COMPLETION-PLAN.md. Resume scheduler design only after
a useful product work cycle and an authorized scope/cadence decision.
