# T2 compatibility run — matched runtime unsatisfiable; Pod terminated

**Decision: `hold` on the frozen T2 runtime.** No model was served. No comparison outputs were collected. Foundation selection remains `benchmark_required`.

## Authorization and spend

The owner requested continuing T2 and starting Veronica, then "One hour is fine". This one-use approval covered one A100 80 GB, 60 minutes including startup, at most $1.75/hour, and supervised shutdown. Profile: `config/runpod-t2-candidate-a.json` (vLLM 0.17.0 / Transformers 5.8.0), not the default vLLM 0.11.0 chat stack.

Live preflight at 06:51:43 UTC and launcher recheck at 06:53:31 UTC: A100 stock Low in `EUR-IS-1`, listed **$1.59/hour**, volume `v53gj9flzs` 300 GB, zero existing Pods. Created Pod `cds4rrvw2nmm4w` / `veronica-t2-20260904-065331-479fba6e`. UI opened at `http://127.0.0.1:8010` before inference (`startup-ui-ready.json`); the model server never answered.

Exact Pod absence confirmed at **2026-09-04T07:01:18.175004Z**. Persistent volume retained. Do not reuse this approval.

## Compatibility result

Candidate A files on the volume hashed successfully. Install of the frozen matched runtime then failed:

```text
Because vllm==0.17.0 depends on transformers>=4.56.0,<5 and you require
vllm==0.17.0, we can conclude that you require transformers>=4.56.0,<5.
And because you require transformers==5.8.0, we can conclude that your
requirements are unsatisfiable.
```

Proof: `bootstrap-log.txt`. The 0.11.0 runtime directory remains on the volume and was not used. Weights were not modified.

This is the failure the 2026-09-01 protocol predicted: plan-only checks cannot prove the image/runtime combination will install. That protocol also required: if compatibility fails, record `hold`; do not silently change only one model's runtime.

## Why the pin is internally inconsistent

`config/t2-qualification.json` froze vLLM 0.17.0 and Transformers 5.8.0 because the Qwen3.8-27B card/recipe needs Transformers >= 5.8.0. Published vLLM 0.17.0 still declares `transformers>=4.56.0,<5`. Those two pins cannot be installed together. The current official vLLM Qwen3.8 recipe still requires Transformers >= 5.8.0 and documents much newer vLLM builds (for example 0.26.x / 0.28.x for later features). A replacement matched stack must be chosen for **all four** T2 models, then frozen, then compatibility-tested on a new authorized Pod.

## What this run is not

- Not a T2 pass or model selection.
- Not proof Candidate A or B is incapable; the server never started.
- Not permission to fall back to vLLM 0.11.0 for the four-model comparison.
- Not permission to change only Candidate B's runtime.

## Next legitimate action

1. Owner adjudicates the first-conversation advisory reviews (`runs/2026-08-31-recorded-conversation-eval/`).
2. Choose and freeze one installable matched runtime for all four T2 models (a vLLM release that actually accepts Transformers >= 5.8.0, plus a complete resolved package freeze). Do not serve mixed runtimes.
3. New start request, duration, and approval for a compatibility run of that revised stack.
4. Only after that stack serves a real completion, transfer the three missing weight sets and collect comparison outputs.

Chat UI at 8010 was wrapper-only and is down with the Pod. Say **Start Veronica** again only when a new bounded run is authorized.
