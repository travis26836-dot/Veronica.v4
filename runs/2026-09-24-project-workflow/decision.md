# Ongoing project restructuring

Owner accepted the ongoing-project structure in this task and requested implementation.
This decision changes planning and review workflow, not model selection or spending.

P0 is ongoing Veronica development; CORE-1 is bounded by SOURCE-OF-TRUTH section 11
with the original October 23 target. G0-G8 decompose delivery; O1-O3 cover recurring
repository care, model improvement and workflow improvement. GOALS.md maps these
to existing TODO gates. No product checklist items are newly checked.

Inspected main at 7435489, dirty source/test changes, zero active claims before
this task, the named September 13 decision and the milestone-branch completion
plan via git show. No branch integration was performed. Repository instructions,
README and TODO now link the ongoing workflow and reusable project review skill.

Known corrections: the app goal is task-scoped; origin/main equality was previously
reported without live remote checks; partial pytest output did not prove a hang;
the launch instructions and dirty cost ceiling conflict. These remain explicit
G0 verification tasks, not assumed resolved by this planning decision.

Existing daily and weekly automations are to use this register, fresh observations,
due-time deduplication and concise change-only updates. Event-driven regression
and session handoffs are prescribed workflow, not an installed background service.

Next: G0.1 branch/evidence map, followed by policy and test-result reconciliation.
CORE remains open and foundation selection remains benchmark_required.

Validation: git diff --check passed; project-venv quick_validate.py reported
Skill is valid. System Python lacked PyYAML, so validation used the existing
project environment without installing packages. Collaboration preflight passed.
Both existing automations were updated successfully and their persisted records
show ACTIVE with daily 09:00 and Monday 09:15 recurrence fields. Actual delivery
time remains subject to the app scheduler; prior unexpectedly frequent wakes are
handled by the new review-period deduplication instruction. No new app goal or
task was created, and the existing CORE app goal remains open.
