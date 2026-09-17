# 2026-09-17-qualification-execution-gate

**Decision:** generated-code execution is blocked until complete isolation is
verified. This closes an unsafe fallback, not the T2 executable qualification gate.

Found: executable_code_report ran extracted source even if unshare was absent or
its network probe failed; only its final status reflected the isolation failure.
Network namespaces also do not protect host files or constrain child resources.

Changed: --execute-code now reports isolation_unverified with
generated_code_executed=false. Removed caller-supplied isolation attestation
parameters. No generated sample reaches the harness, even if the network probe
passes, until a complete execution backend is implemented and verified. This is
an intentional temporary execution hold, not a functioning sandbox claim.

Validation: 22 targeted capability/qualification tests passed. The full tests
suite exited 0 with one platform skip. New regression tests forbid entry to the
execution harness under failed and network-only isolation, confirm no marker
file is written, and verify report_run persists the blocked status. Trusted
repository fixture programs still run against independent vectors and reject
bad pagination and SQL interpolation. These fixture tests do not prove isolation
or model-generated coding quality. Frozen evaluation suite hash remains intact.

Environment check: Docker CLI exists, but docker version cannot connect to
dockerDesktopLinuxEngine (named pipe absent). WSL lists Ubuntu and Docker
Desktop distributions; no execution sandbox was verified or started here.

Remaining readiness gaps: complete filesystem/process/resource-isolated backend
and escape/limit tests; parent-trusted grading so generated code cannot forge
its own score; full schema validation; actual-token long-context runner; heldout
qualification; matched model/runtime evidence and fresh paid authorization.

Next action: prepare and validate a complete local sandbox backend, retaining
fail-closed behavior when its runtime is unavailable. Then finish the other T2
readiness checks. No model inference, paid resource, remote merge or push occurred.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
