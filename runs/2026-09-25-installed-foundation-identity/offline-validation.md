# Offline validation — installed-foundation identity

**Branch:** `docs/installed-foundation-identity`  
**Validation scope:** offline only; no model start, RunPod action, weight download, paid compute, or qualification claim.

## Repository state inspected

The worktree already contained the installed-foundation migration: active configs, schemas, scripts, application code, docs, and tests were modified; retired Candidate A/B configuration files were deleted; and foundation-baseline configuration/run-record files were untracked. This validation did not alter historical run folders. Candidate A/B references remaining outside `runs/` are archival/research/completed-handoff material or the migration task description, not active configuration. All active `publicAlias` fields found in model/run profiles and schemas resolve to **`Veronica.v.4.1-30B-A3B-BF16`**.

## Commands and results

| Command | Result |
|---|---|
| `uv run python scripts/verify_t2_qualification.py protocol` | **PASS** — `protocol_id: foundation-baseline-v1`, `protocol_ready: true`, 0 issues; 1 registered foundation; 2 required baseline tracks; `paid_compute_started: false`; `foundation_qualified: false`. |
| `uv run python -m pytest tests/test_qualification.py tests/test_contracts.py tests/test_app.py tests/test_provider.py tests/test_evaluation.py tests/test_runpod_core.py tests/test_start_veronica.py tests/test_supervised_start.py -ra` | **PASS** — 119 passed, 31 skipped, 1 FastAPI/Starlette deprecation warning (0.78 s). |
| `uv run python -m pytest -ra` | **PASS** — 169 passed, 31 skipped, 1 FastAPI/Starlette deprecation warning (1.74 s). |
| `git diff --check` | **PASS** — no whitespace errors. |

The 31 skips are Windows/PowerShell launcher and keep-awake policy checks, skipped because PowerShell 7 is unavailable in this Linux sandbox. They are not live-network or paid-compute execution failures.

## Repair made

- `tests/test_supervised_start.py` — changed the wrong-model readiness assertion from the retired generic `Veronica alias` wording to the exact required public alias, `Veronica.v.4.1-30B-A3B-BF16 alias`. This matched the migrated production error emitted by `scripts/supervised_runpod.py` and converted the sole targeted-suite failure to a pass.
- `runs/2026-09-25-installed-foundation-identity/outputs/offline-validation.md` — this completion report.

## Remaining failures and closure decision

**No offline test failures remain.** The only unexecuted checks are the 31 platform-gated PowerShell tests above. Live baseline collection remains pending; no inference was performed, no provider readiness was claimed, and the foundation is **not qualified**.

**Identity checkpoint:** the offline identity-migration validation checkpoint **can close** once the existing migration changes are reviewed/integrated: active wiring consistently uses the exact installed-foundation alias and the full offline suite passes.  
**Qualification checkpoint:** **cannot close** until a separately authorized fresh live baseline collects the two required foundation-track runs and satisfies the protocol; this validation makes no such claim.
