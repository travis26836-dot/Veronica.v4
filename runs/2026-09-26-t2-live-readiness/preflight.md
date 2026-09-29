# T2 live-qualification preflight — 2026-09-26

Scope: prepare the four-model foundation qualification without creating a Pod
or making a model-capability claim.

The frozen protocol requires four models in two candidate/control pairs and
ten matched runs: deterministic and sampled chat for every model, plus native
thinking for the Qwen3.8 pair. The specified runtime is one A100-SXM4-80GB,
32K context, `max_num_seqs=1`, vLLM 0.28.0, Transformers 5.8.0, direct
surface, untouched weights, and the stable `Veronica` alias.

Before a live run can be authorized, the following must be true:

1. the RunPod policy and its tests agree on the $1.75 hourly ceiling;
2. a clean integration branch contains the required evaluator/context code;
3. the frozen packet validates from the checkout that will perform the run;
4. all template, tokenizer, protocol, CP2 and CP3 hashes match the actual
   runtime inputs; and
5. the run has a fresh bounded owner authorization and preserves raw
   response, host-side grading, latency/cost, human review and final decision
   evidence.

Current result: **blocked; no Pod started.**

The historical CP4 report says ready, but current revalidation from the
isolated checkout returns `valid=false`, `ready=false`: the frozen protocol,
CP2 decision and CP3 decision hashes do not match. The CP4 decision also
records an unresolved standalone chat-template discrepancy (4,125 vs 4,040
bytes). Separately, the focused evaluator commit cannot be cleanly applied to
`main`: its context prerequisite reveals snapshot-hash failures and its
`evaluation.py` change conflicts.

This is not a reason to relax the qualification. The next safe action is to
repair and validate the ordered integration set, then regenerate a T2 packet
from the accepted checkout. Only then may a fresh, bounded Pod request be
used for live collection.
