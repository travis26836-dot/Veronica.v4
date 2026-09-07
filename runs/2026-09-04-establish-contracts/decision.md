# Establish contracts checkpoint — 2026-09-04

**Decision: contract artifacts added; `Trail Marked` is not earned until the owner commits this baseline.**

No model inference, weight download, or paid compute was started. The live Pod from `runs/2026-09-04T070444Z-start-veronica/` was not terminated.

## Outcome

Establish (E) items that do not require T2 live GPU comparison now have schemas, generators, an immutable run folder, and an offline provenance checklist. This run folder itself was created by `scripts/init_run_folder.py` and then refused a second create.

## TODO items with proof

- JSON schemas for run records, model records, evaluation cases, and module manifests: `config/schemas/`. Canonical instances pass `scripts/validate_contracts.py` (`outputs/validate_contracts.json`). `scripts/validate-project.ps1` now requires the schema files; `scripts/verify-local.ps1` runs instance validation after `uv sync`.
- Configuration fingerprint generator: `scripts/configuration_fingerprint.py` hashes non-secret profile/runtime/identity settings. Digest `c7e3871ec0843da0b46bbebc484a8d68386fe312758a4902a740238dd2d99088` in `configuration-fingerprint.json`. Secrets are omitted.
- Immutable run-folder initializer: `scripts/init_run_folder.py`. Overwrite refusal: `outputs/init-overwrite.txt`.
- License/provenance checklist: `scripts/check_license_provenance.py`. Four pinned snapshots have README, LICENSE, and 40-character revisions (`outputs/provenance.json`). Presence only; not legal review, not a weight download.

The source-of-truth baseline commit is still unchecked. **`Trail Marked` still requires an owner commit.**

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Contract unit tests | **12 passed** | `outputs/test_contracts.txt` |
| Full local pytest (Linux/WSL, isolated 3.12 venv) | **145 passed, 30 skipped, 2 failed** | `outputs/pytest-full.txt` |
| Schema instance validation | ok, no compute | `outputs/validate_contracts.json` |
| Provenance checklist | 4/4 complete, no network | `outputs/provenance.json` |
| Project-contract validator | schema files present | `outputs/validate-project.txt` |

The two full-suite failures are the existing frozen-suite SHA check (`ce1644f04595…`) versus this checkout's LF bytes of `data/evals/veronica-core-v1.json`. Replacing LF with CRLF reproduces the frozen digest. Those tests were not changed. `config/t2-qualification.json` and the eval suite were not edited.

## Limits

- Not a T2 pass, model selection, or `Trail Marked` acknowledgment.
- Module manifests are a schema only; no application module was implemented.
- The provenance script does not download cards/weights or start compute.
- Historical `run.json` files remain heterogeneous; new runs from the initializer match `config/schemas/run-record.schema.json`.

## Next legitimate action

Owner commits this source-of-truth baseline. T2 remains `hold` on the unsatisfiable matched runtime; do not start a Pod from this checkpoint.
