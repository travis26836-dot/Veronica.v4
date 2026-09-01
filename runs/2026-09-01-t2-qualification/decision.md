# T2 qualification checkpoint — offline protocol ready, live comparison pending

**Decision: continue under `benchmark_required`; T2 is not yet accomplished.**

## Verified in this checkpoint

- The canonical registry now contains Candidate A, Candidate B and both official controls at their immutable revisions.
- Twenty-three pinned metadata files were downloaded without model weights and hashed in `provenance-manifest.json`, including all eight required README/license snapshots plus runtime-relevant configs and chat templates.
- The license/lineage review records Apache-2.0 permissions and obligations, exact base-model relationships and the repository authors' stated ablation methods.
- `config/t2-qualification.json` freezes a paired, persona-free direct comparison: one full deterministic extended pass for all four models, repeated sampling on release blockers, and a separate native-thinking track only for Candidate B and its control.
- The matched runtime requires one A100 80 GB, BF16, 32,768 context, concurrency one, vLLM 0.17.0 and Transformers 5.8.0. The prior Candidate A smoke runtime (vLLM 0.11.0 / Transformers 4.57.1) is not accepted as the comparison runtime because it does not support Candidate B's documented requirements.
- Four immutable T2 launch profiles now bind each model to that matched target runtime and its family-specific reviewed parser arguments. Plan-only validation does not prove the image/runtime combination will install or serve; a paid compatibility run remains required.
- The launcher now accepts only the default profile or a direct `config/runpod-t2-*.json` profile, and every profile blocks creation when either a `veronica-core-` or `veronica-t2-` Pod already exists.
- The evaluator now records `top_p` and per-request thinking state. The T2 verifier checks exact identities, pairs, suite/case hashes, settings, sample pairing, human reviews and supplemental evidence before a signed selection decision can be prepared.
- Full local verification passed: 130 tests, 2 skipped, with the pre-existing Starlette/httpx deprecation warning. The protocol audit reports four models, two candidate/control pairs, ten required model-track collections and zero protocol issues. See `verification.json`.

## Not yet verified

- Candidate A control, Candidate B and Candidate B control weights have not been transferred and hash-validated on the RunPod volume.
- No model has been served under the new matched runtime.
- None of the ten required model-track collections exists.
- Human review, executable-code sandbox reports, long-context stress reports, deployed native-tool parser reports and the paired comparison are missing.
- No signed model-selection decision exists.

## Spending and state

No Pod, endpoint, paid judge, training job or model-weight download was started. A live read-only preflight at `2026-09-01T11:01:17.080706Z` confirmed the 300 GB volume, a listed A100 price of $1.59/hour and zero account Pods, but reported `stock: none` for the required A100 in `EUR-IS-1`; see `runpod-preflight-20260901T110117Z.json`. The earlier paid authorization is consumed. Every future Pod still requires a fresh bounded start request, duration and exact termination evidence. The protocol preserves the one-A100 and $1.75/hour ceiling.

## Next legitimate action

Wait for the required A100 to return to stock, obtain a fresh bounded paid-run authorization and duration, then perform a compatibility run on the pinned vLLM/Transformers stack before transferring the three missing models or collecting comparison outputs. If compatibility fails, record `hold`; do not silently change only one model's runtime.
