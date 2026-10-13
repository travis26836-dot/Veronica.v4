# Veronica ongoing development workflow

Accepted direction: owner request to restructure the project, 2026-09-24.
Veronica is an ongoing product. CORE is its first bounded release milestone.
The original target is October 23, 2026; weekly forecasts must disclose slippage
instead of weakening acceptance. Maintenance continues after CORE acceptance.

## C - Capture

Product requirements remain in SOURCE-OF-TRUTH.md; TODO.md owns detailed
acceptance checkboxes. [GOALS.md](GOALS.md) owns goal priority, dependency and
status. CURRENT-STATE.md names authoritative decisions. This workflow governs
delivery, not a replacement definition of CORE.

Capture each request, defect or evaluation finding under a goal ID. Record the
observed problem, intended outcome and evidence. Use [GOAL-TEMPLATE.md](GOAL-TEMPLATE.md)
for a work packet. Split a packet when it spans different owners, dependencies,
approvals, or independently testable outcomes. Aim for one session per packet;
split again if its next action cannot be stated concretely.

## R - Research

Inspect the actual checkout, branch, dirty diff, relevant handoffs and evidence.
Compare other branches read-only before declaring earlier work missing. Identify
existing implementations and exact gaps; never reproduce a capability merely
because it is absent from the current branch. Resolve conflicts in authority
with an explicit decision. Cached origin refs do not prove current GitHub state.

## E - Establish

Each packet has one responsible writer, paths, dependencies, acceptance proof,
effort estimate, spending/approval needs and a recovery action. Follow the
collaboration preflight and claim protocol. Default WIP: one implementation
packet and one independent read-only review. Parallel writers require disjoint
claims; linked worktrees share claims through Git's common directory, while
separate clones still require verified external coordination.

Statuses: backlog -> ready -> active -> review -> accepted. Use blocked only with
a named dependency and unblock condition; superseded records retain their history.
Accepted requires evidence, reviewed integration and a handoff. Report implementation,
tests, commits, push/merge and live qualification separately. A completed child
does not accept its parent; all required child gates must pass.

## A - Assemble

Choose the highest-priority ready packet on the CORE dependency path. Make the
bounded change and preserve unrelated dirty work. Classify pending changes as:
keep (supported work), review (uncertain provenance/behavior), commit (reviewed,
validated and publishable), or discard candidate (demonstrably obsolete, requiring
owner authorization before removal). Never infer benefit from filenames alone.

Use existing tools first. Promote a repeated, proven procedure into a skill;
add a plugin only when a missing integration justifies one. Every automation
needs an owner, trigger, inputs, expected output, failure handling and stop rule.

## T - Test

Define acceptance before implementation. Match proof to the claim: mocks for
wrapper contracts, independently scored real completions for model behavior,
and recovery runs for deployment. Capture the complete command result including
exit code and any process/session handle. If a command yields, poll that handle;
never launch duplicate suites because only partial output was returned.

For model improvement: capture -> validate evidence -> classify failure layer ->
adjudicate -> select intervention -> add regression -> compare -> accept/reject/hold.
Scores recommend evaluator, runtime, prompt, foundation or adapter work. A low
score alone neither identifies a training method nor authorizes training.
Critical failures block promotion; human review, provenance, independent holdouts
and capability preservation remain required. See evals/RUBRIC-ROUTING.md.

## E - Execute

Deliver packets through reviewed exact-path commits and integration checks.
External pushes, paid workloads and release follow existing authorization rules.
Reassess the next dependency after each accepted packet. Every model, persona,
template, runtime or tool change triggers affected regression checks. A failed
gate creates a corrective packet, not a weaker threshold.

| Trigger | Operation | Output and limit |
| --- | --- | --- |
| Session start | Read CURRENT-STATE, goals, TODO; preflight | One selected ready packet |
| Session end | Record actual outcomes and next action | Handoff and goal status; no success without proof |
| Daily | Repo/evidence hygiene and changed blockers | At most three actionable bullets; quiet if unchanged |
| Weekly | Dependency, capacity and CORE forecast review | Top three risks/gates; next week's ready queue |
| Each relevant change | Targeted regression and evidence review | Pass/fail/unknown with complete process result |
| Each accepted milestone | Integration and recovery review | Milestone decision; update project state |

Daily and weekly reviews are scheduled app tasks. Session/change/milestone
triggers are workflow obligations, not claimed background services. Reviews
must perform fresh checks or explicitly mark them unavailable. Never replay an
old 'unchanged' statement without inspection. Record last successful review and
next due time in the automation's own history; early duplicate wakes stay quiet.
If GitHub cannot be checked, say remote status is unknown. Repeated check failure
is reported once and again only on change or a scheduled weekly escalation.

## D - Document

Evidence goes in runs/, code in src/, plans in docs/, and claims/handoffs in
coordination/. Every packet leaves files, validation, evidence, limitations,
integration state and next safe action. Weekly report accepted gates, unresolved
critical failures, age of blocked packets and date forecast; do not invent a
percentage from unchecked TODO counts. Ongoing operations stay active after a
release, while each improvement packet ends with an explicit decision.

Repository goals are shared across agents. The app goal remains task-scoped;
this register supplies the ongoing hierarchy without creating uncontrolled
background development tasks. New app tasks are created only when requested.
