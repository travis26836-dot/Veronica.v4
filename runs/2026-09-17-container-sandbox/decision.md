# 2026-09-17-container-sandbox

**Decision:** isolated executable evaluation implemented and locally verified.
Work began September 17 and completed September 22, 2026. This earns the
executable-environment TODO subtask, not model qualification or T2 Mind Proven.

The supplemental reporter now explicitly executes coding samples through pinned
local Docker containers, one per independent fixture vector. There are no host
mounts or network access; root is read-only, UID is unprivileged, privileges are
dropped, and memory/process/CPU/temp-space/time/output limits apply. The host
validates the container configuration before execution and compares returned
values against expected answers that never enter the worker. Removed the old
host-Python/network-namespace execution helpers. Missing runtime and failed
verification still stop execution. No image pull or Docker startup occurs inside
the evaluator; local Docker was started explicitly for this development check.

Verified evidence:

- initial-probe.json: September 17 actual container boundary probe.
- probe-2026-09-22.json: fresh local socket, pinned image, network/root/privilege,
  cgroup/resource and cleanup observations.
- tests-2026-09-22.xml: full suite, 223 passed and one platform skip, including
  opt-in real Docker tests. The user subsequently reported Docker crashing.
- probe-after-docker-recovery-2026-09-22.json: fresh successful boundary probe
  after the reported crash; Docker was confirmed running before rechecking.
- tests-after-docker-recovery-2026-09-22.xml: 40 targeted tests passed after recovery.
- tests-final-2026-09-22.xml: 46 capability/sandbox/qualification tests passed
  after final grading corrections for null exceptions, numeric overflow, bounded
  output reads, and revoked cleanup attestations.
- validation.json: source hashes, JUnit counts and final container inventory.

Real container tests cover correct fixture programs and rejected wrong code,
forged pass output, SQL interpolation, host file/environment/socket boundaries,
network/write denial, process/memory exhaustion, output flooding, and timeout
cleanup. All use repository-owned fixtures, not newly generated model responses.
No sandbox containers remained after verification. The original startup command
timed out while Docker was starting; checking the same runtime showed it became
available, so no restart loop was used. Crash root cause is not established.
An initial worker syntax error was corrected before the passing live checks.

Limits: Docker/kernel trust remains necessary. Worker observations are untrusted;
the same Python interpreter can be manipulated by deliberately adversarial
source, so human source review remains necessary. Public fixtures are not a
sealed holdout. Full schema and actual-token context environments remain open.
The frozen four-model protocol still passes offline validation and still reports
foundation_qualified=false. No model weights, persona or serving runtime changed.

Next: complete schema qualification checks, then actual-token long-context
readiness and independent holdout work before a fresh authorized model run.
The unrelated untracked Veronica.v4.worktrees directory was left untouched.
No paid resource, remote push, PR merge or product release occurred here.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
