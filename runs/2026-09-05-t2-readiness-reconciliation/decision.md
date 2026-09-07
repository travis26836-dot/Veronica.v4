# T2 readiness reconciliation

## Owner-requested stopping checkpoint

Owner requested a checkpoint at 9% remaining usage. Work stopped before paid creation.

- All four T2 profiles now target vLLM 0.28.0 / Transformers 5.8.0 with isolated environments and shared resolved constraints `config/runpod-runtime-t2-0.28.0.txt`.
- Active protocol and comparison template now identify `t2-untouched-foundation-v2`; the prior protocol is preserved in `protocol-v1-snapshot.json`. Model revisions, suite and track scope are unchanged.
- `verify_t2_qualification.py protocol` returned exit 0, protocol_ready true, zero issues, four models and ten required tracks. This is offline configuration validation only; foundation_qualified remains false.
- No new Pod was created. No live comparison outputs were collected. Runtime installation/CUDA compatibility and generated responses remain unverified.
- Resume by reviewing the v2 runtime rationale and full constraints, checking actual driver compatibility and live inventory, then performing the bounded compatibility run when the owner resumes. Do not launch while this checkpoint pause is in effect.

Earlier paragraphs below describe intermediate states, superseded by this checkpoint where noted.

## Dependency-resolution progress

Bootstrap now supports `runtime.isolatedEnvironment: true`, creates a venv without inherited image packages, and rejects reuse of a system-package-inheriting environment when isolation is requested. Legacy chat defaults are unchanged. Three focused tests pass in `tests/test_runtime_isolation.py`. Replacement profiles have not yet enabled this option. The resolved candidate pulls CUDA 13 packages; historical driver evidence is 580.159.04, but a new host's actual driver must still be checked. Do not infer runtime compatibility from the image tag or dependency resolution alone.

Public PyPI metadata for vLLM 0.28.0 declares Transformers >=5.5.3, permitting the required 5.8.0. A metadata-only `uv pip compile` of `runtime-candidate.in` succeeded (exit 0) for Python 3.12 and x86_64-manylinux_2_39, matching Ubuntu 24.04's glibc target, with binary wheels required. The complete resolved candidate is `runtime-candidate.lock`. The initial generic Linux target rejected llguidance wheels; using the explicit actual glibc target resolved that limitation.

This proves dependency resolution only, not CUDA driver compatibility, installation, model loading, inference, or four-model qualification. Production T2 profiles and the original protocol have not been changed. Next verify wheel/CUDA requirements and the bootstrap installation path before promoting this candidate consistently across all four profiles.

Sources: https://pypi.org/pypi/vllm/0.28.0/json and https://huggingface.co/Qwen/Qwen3.8-27B . No package installation, weight download or paid resource creation was performed for this resolution.

T2 remains unfinished. No new Pod creation was attempted in this continuation.

## Authoritative findings

- The current Candidate A T2 profile still pins vLLM 0.17.0 and Transformers 5.8.0.
- `runs/2026-09-04T065235Z-start-veronica/bootstrap-log.txt` and its decision record document an actual dependency-resolution failure: vLLM 0.17.0 requires Transformers below 5, conflicting with 5.8.0. That Pod was terminated; no comparison was collected.
- `runs/2026-09-04T070444Z-start-veronica/decision.md` records successful recovery chat on the older runtime and confirmed termination. That recovery is not matched T2 evidence.
- Today's offline launcher plan passed for one A100, 60 minutes, ceiling $1.75/hour. Live preflight failed while reading the network volume: RunPod REST request timed out. Current inventory, stock and price remain unverified.

## Next action

Resolve and verify an installable shared runtime for all four models before paid creation. Preserve the frozen failed protocol and record any replacement as an explicit protocol revision; do not silently mix runtime versions or count old smoke responses as comparison evidence. The owner's current one-run authorization has not been consumed by a Pod creation in this continuation. No additional or replacement Pod is authorized.

The phrase MILESTONE ACCOMPLISHED in the goal objective is not evidence of completion. Full four-model outputs, supplemental capability evidence, review and selection remain required.
