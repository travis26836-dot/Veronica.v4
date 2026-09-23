# Executable evaluation sandbox

Implemented for the T2 Python coding fixtures. Local validation is recorded in
`runs/2026-09-17-container-sandbox/`; work began September 17 and resumed
September 22. This validates the evaluator, not a foundation model.

## Operation

Docker Desktop/Engine must already be running, with the official Python image
pinned in `config/execution-sandbox.json` available locally. The evaluator never
starts Docker, pulls an image, calls a model, or creates paid compute. Remote
Docker endpoints are rejected. The selected local socket/pipe is pinned for all
container operations so an environment override cannot redirect later calls.

First check the runtime:

```powershell
uv run python scripts/verify_execution_sandbox.py
```

For a reviewed evaluation folder containing `results.jsonl`, run the existing
supplemental reporter with its explicit `--execute-code` flag:

```powershell
uv run python -m veronica_core.capability_reports --run-dir runs/ACTUAL-EVAL-RUN --execute-code
```

Missing runtime, missing pinned image, failed probe, or policy mismatch means no
generated source executes. There is no host-Python or network-namespace fallback.
Default reporting without that flag still does not execute code.

## Boundaries and scoring

Each fixture vector runs in a new container: no network or host mounts, read-only
root, unprivileged UID, all capabilities dropped, no new privileges, default
seccomp, private process namespace, no Docker socket and no restart policy.
Limits are 256 MiB RAM, no swap, 32 processes, one CPU, 16 MiB temporary storage,
and 64 file descriptors. The worker deadline defaults to eight seconds per
vector, excluding bounded Docker management calls. Output is monitored and
execution is killed above 1 MiB; a short polling interval can allow overshoot.

The host checks Docker's configuration before starting each container. A trusted
probe additionally checks the running container's network, filesystem,
privileges, namespaces and cgroup limits. Each exact generated container name is
removed after execution, including errors/timeouts. Unverified cleanup fails the
sample, revokes the sandbox attestation, and prevents subsequent vectors.

Only source, function name, input arguments and required SQLite setup enter the
worker. Expected answers stay on the host. The host parses one strict JSON
observation and compares values, exception names and declared input mutation
against independent fixtures. Extra pass/fail fields, duplicate JSON keys,
malformed output and model-written tests cannot count as grading evidence.
Reports retain source hashes, vector results, container identities and cleanup
status. Raw worker observations are untrusted output.

Docker and its host kernel are trusted. These controls are not a guarantee
against kernel vulnerabilities. The Python worker shares an interpreter with
the submitted function, so a deliberately adversarial function could fabricate
an observation (including reported argument mutation); human source review is
still required. Expected answers are never supplied to that interpreter.
The five coding fixtures are public regressions, not a sealed holdout or complete
coding qualification. SQL setup and Python signatures are fixture-specific.

## Validation

Ordinary unit tests require no Docker. Opt-in local integration tests execute
repository-owned programs in real containers, including correct/wrong answers,
SQL injection regression, forged passes, host-file/environment/socket checks,
network/root-write denial, process exhaustion, output flooding, memory
exhaustion, timeout cleanup, and the full five-case supplemental report.

```powershell
$env:VERONICA_TEST_DOCKER='1'
uv run pytest tests/test_execution_sandbox.py tests/test_capability_reports.py -ra
```

The frozen 60-case suite and model weights remain unchanged. Long-context,
schema, holdout, live model and human-review gates remain separate TODO items.

Reference: Docker's [container execution options](https://docs.docker.com/reference/cli/docker/container/run/)
and [Engine security model](https://docs.docker.com/engine/security/).
