# CD-05 integer-only JSON regression

**Status:** Offline regression verified; model prompt intervention blocked.

## Preserved baseline

The original CD-05 expected answer and fixture vectors are unchanged. The
fixture SHA-256 is `571c6f8c141dd81c27f8c538b68dfb92148f5ff0e0aac369f5cb3a397aade9df`.
The untouched baseline report SHA-256 is
`3ddb18bb1e8b13f6beec48f7cf3fc2f7006ef5b1c38c535954b092fb0de3cbd1`, and its
manifest SHA-256 is
`6e2cc2eb3d3c421e74403f3f6a52b49798545d2d86d1e8dcf3d4ae926d602e89`.
The baseline report records CD-05 `collected_fail`: seven of eight vectors pass,
and `boolean-count` returns `true`. Its Docker isolation record uses the pinned
Python image `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`.
The baseline was an alternative diagnostic runtime, not the matched T2 runtime.

The issue and
[`boolean-regression.md`](../2026-09-23-github-eval-issues/boolean-regression.md)
also record that the answer claimed booleans were rejected. **Code correctness:**
the executable result contradicts the requested contract. **Explanation
truthfulness:**
the reported claim contradicts that result; however, the raw `results.jsonl`
referenced by the issue is absent from this checkout, so its original prose
cannot be independently rescored here.

## Offline isolated reproduction

On 2026-10-07, the unchanged eight-vector fixture was executed in the pinned
Docker image with network disabled, a read-only root, UID 65534, dropped
capabilities, `no-new-privileges`, and resource limits. A parser using the
reported `isinstance(count, int)` check passed 7/8; replacing that integer check
with exact-type validation passed 8/8. The boolean vector alone failed in the
baseline and passed in the repaired implementation. The focused test suite also
passes all 17 tests.

This is an isolated code reproduction and corrected-code check, **not** a
model-generated response or an evaluated runtime/prompt/model intervention.

## Prompt-only intervention: proposed, not evaluated

Preserve the original CD-05 prompt. The sole treatment change is to append:

> Check Python's JSON type semantics explicitly. A JSON boolean must not satisfy
> this integer-only contract, even if Python's ordinary integer type checks
> accept it.

No inference result is available for this variant. No matching active endpoint
was supplied or verified, and this task contains no fresh bounded-run
authorization; the baseline raw completion is also not in this checkout.
Therefore this comparison is **blocked**; no response, correctness score, or
truthfulness score is attributed to the intervention. A future run must capture
both prompts and raw responses on the same model revision, runtime, mode, and
decoding settings, then independently execute each generated parser against
every unchanged fixture vector in an isolated sandbox. Score code correctness
and explanation/action truthfulness separately. The known public regression is
not a held-out generalization test.

## Decision

Keep the failure public and the fixture expectations unchanged. Do not claim
that the prompt intervention worked, do not promote coding capability, and do
not mark T2 complete. `TODO.md` remains open. Next safe action: recover the
baseline response/runtime record and obtain a fresh authorized live evaluation
window before running the paired prompt comparison.
