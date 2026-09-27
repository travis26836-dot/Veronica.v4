# Goal packet template

Copy under docs/goals/ only when selecting an actual work packet.

- ID / parent / owner:
- Outcome and observed problem:
- Status / last verified date:
- Dependencies and unblock condition:
- Existing implementation/evidence inspected:
- Paths and collaboration claim:
- Acceptance criteria and proving commands/artifacts:
- Effort / time or spending bound / approvals needed:
- CREATED stage and next executable action:
- Validation result, exit code and process handle if still running:
- Files changed / evidence / commit / remote integration state:
- Limitations / rejected approaches / rollback or recovery:
- Decision: accept, reject, hold, or supersede; next safe action:

Split this packet when parts can be accepted independently or require different
owners/approvals. Link children and require every necessary child before closing
the parent. Recurring operations generate packets; they never become an endless
single implementation goal.
