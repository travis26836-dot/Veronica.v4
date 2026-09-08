# The Installed Veronica.v4 Foundation: Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated

**Document type:** cited research paper (not model qualification, not legal advice, not a selection decision)  
**Subject checkpoint:** Candidate A, revision `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`  
**Project:** Veronica.v4 (`C:\Users\raine\DEVELOPMENT\Projects\Veronica.v4`)  
**Date:** 2026-09-08  
**Status:** the public alias `Veronica` is a wrapper rename. The weights on disk and on the RunPod volume are this Huihui derivative of Qwen3-30B-A3B-Instruct-2507. They are **not** Candidate B (Qwen3.8-27B). Selection status remains `benchmark_required`.

---

## Abstract

The model currently installed for Veronica.v4 text serving is a community abliterated derivative of Alibaba's Qwen3-30B-A3B-Instruct-2507, published by huihui-ai at an immutable Hugging Face revision pinned by this project. It is a 30.5 billion parameter Mixture-of-Experts causal LM with 3.3 billion activated parameters, 128 experts and 8 experts per token. The official base is Instruct-only and non-thinking: it does not emit think-tag blocks. Huihui's card states that refusals were reduced with a crude, proof-of-concept abliteration method, citing Sumandora's Hugging Face Transformers implementation of the Arditi et al. refusal-direction technique, plus an unspecified "new and faster method." This project has **not** fine-tuned, quantized, or LoRA-adapted those weights. It has hash-verified all 27 repository files (61,084,222,203 bytes), served them with vLLM 0.11.0 under the alias `Veronica` on an A100 80 GB, wrapped them with a local persona/mode prompt layer, and recorded first-chat and later smoke failures that block qualification. Candidate B (Huihui-Qwen3.8-27B-abliterated) is a different architecture and is not present on the model volume.

---

## 1. Identity of the installed checkpoint

| Field | Installed value | Source |
| --- | --- | --- |
| Public API alias | `Veronica` | `config/model-registry.json`; wrapper `/v1/models` |
| Hugging Face repository | `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` | Hub card; registry; validated manifest |
| Immutable revision | `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` | Hub metadata `sha`; registry; every successful start run |
| Hub lastModified | 2025-08-02T05:55:21.000Z | `provenance/candidate/hub-metadata.json` |
| Declared license | Apache-2.0 (LICENSE file present; license_link points at the Qwen control LICENSE) | Hub card YAML; `runs/2026-09-01-t2-qualification/license-review.md` |
| Declared base | `Qwen/Qwen3-30B-A3B-Instruct-2507` | Hub `base_model`; card prose |
| Control revision (official, not served) | `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` | registry; `config/runpod-core.json` |
| Architecture | `Qwen3MoeForCausalLM` / `model_type: qwen3_moe` | installed `config.json` |
| Parameters (Hub safetensors census) | 30,532,122,624 BF16 tensors | Hub metadata `safetensors.parameters.BF16` |
| Official card parameter claim | 30.5B total, 3.3B activated, 29.9B non-embedding | Qwen Instruct-2507 card |
| Experts | 128 total, 8 activated per token, 48 layers, GQA 32/4, hidden size 2048 | installed `config.json`; Qwen card |
| Native context | 262,144 tokens (Qwen card). This project currently serves `--max-model-len 8192`. | Qwen card; `server-command.json` |
| On-disk verified size | 61,084,222,203 bytes, 27 files, 13 weight shards | `validated-model-manifest.json` |
| Volume path | `/workspace/veronica-core/models/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated/e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` | validated manifest; server command |
| Network volume | `v53gj9flzs`, 300 GB, EUR-IS-1 | `config/runpod-core.json`; volume inspection |

The 2026-09-08 start run's validated file list, byte counts, and SHA-256 hashes are identical to the 2026-08-30 first-chat validated manifest. Parsed `config.json` from the T2 metadata snapshot equals the served config; only pretty-print whitespace differs (`23f9d3f5…` vs `0736f3ba…` as raw SHA-256). That is a snapshot-encoding difference, not a different model.

Integrity check nuance: Hub `expected-model-manifest.json` carries LFS SHA-256 for the 13 weight shards plus `tokenizer.json` (14 files). The other 13 files are expected by size and git-blob SHA-1. `prepare_runpod_model.py` `verify_files()` hashes every file with SHA-256 and git-blob SHA-1, compares against whichever expected checksum exists, then writes SHA-256 for all 27 files into `validated-model-manifest.json`. So the **weights** are SHA-256-verified against Hub LFS; small text/config files are git-blob-verified, then locally SHA-256-recorded.

The official Qwen Instruct-2507 Hub dump packs the same BF16 parameter count as **16** shards (~61.06 GB mapped weights). Huihui's derivative is **13** shards totaling 61,084,222,203 bytes. Same architecture fields and matching `generation_config.json` (temperature 0.7, top_k 20, top_p 0.8); different shard layout, so shard-for-shard hash comparison against the official control is not valid. Compare whole-model provenance, not individual shard names.

---

## 2. What this model is not

**Not Candidate B.** Candidate B is `huihui-ai/Huihui-Qwen3.8-27B-abliterated` at `739e3c5b89849f6c238ce1e5b70008612ae42cdd`, architecture `Qwen3_5ForConditionalGeneration` / `qwen3_5`, a dense multimodal model with native thinking and `reasoning_effort`. Its `config.json` SHA-256 (`191e0af2…`) does not match the installed config. The 2026-09-08 volume listing under `/workspace/veronica-core/models/` contains only `Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated`. T2 still requires transferring and hash-validating Candidate B and both official controls before any fair comparison.

**Not a Veronica-trained foundation.** The string `Veronica` is the stable public alias. vLLM is started with `--served-model-name Veronica`. The wrapper rewrites the `model` field on completions. No project run claims a training job, LoRA, QLoRA, or merge on these weights.

**Not the Qwen3-30B-A3B thinking variant.** Qwen published a separate Thinking-2507 sibling. Huihui also published `Huihui-Qwen3-30B-A3B-Thinking-2507-abliterated`. The installed repo name, card, and `config.json` are the **Instruct-2507** line. The official Instruct card states that the model supports only non-thinking mode and does not generate think-tag blocks; `enable_thinking=False` is no longer required.

**Not a quantized GGUF/EXL3/MLX serving copy.** Third-party quants exist (for example mradermacher GGUF). This project serves BF16 safetensors with vLLM, `dtype bfloat16`.

---

## 3. Official Qwen3-30B-A3B-Instruct-2507

Qwen3-Instruct-2507 is the July 2025 update of the Qwen3-30B-A3B non-thinking mode (GitHub QwenLM/Qwen3 changelog: Instruct-2507 released 2025-07-30). The official card lists:

- Causal LM, pretraining plus post-training.
- 30.5B total / 3.3B activated MoE; 48 layers; 128 experts / 8 active; GQA 32 query / 4 KV heads.
- Native context 262,144 tokens. Optional Dual Chunk Attention plus MInference path toward ~1M tokens, which the card says needs on the order of 240 GB total GPU memory and is not what this project runs.
- Claimed gains versus the earlier non-thinking 30B-A3B on instruction following, reasoning, multilingual coverage, open-ended alignment, and long context.
- Reported official scores on the card include MMLU-Pro 78.4, AIME25 61.3, LiveCodeBench v6 43.2, IFEval 84.7, Arena-Hard v2 69.0, Creative Writing v3 86.0, BFCL-v3 65.1. Those numbers describe the **official untouched Instruct-2507**, not the abliterated derivative, and not this project's 8,192-token vLLM 0.11.0 smoke runtime.
- Deployment note: `transformers>=4.51.0` (older versions raise `KeyError: 'qwen3_moe'`). Suggested serving: `vllm>=0.8.5` or `sglang>=0.4.6.post1`. Suggested sampling: temperature 0.7, top_p 0.8, top_k 20.
- Technical report: Qwen Team, *Qwen3 Technical Report*, arXiv:2505.09388.

The official control in this repo is pinned at `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe`. That control is **not** downloaded as weights on the volume. Only its README, LICENSE, and related metadata snapshots were captured for T2.

---

## 4. Abliteration: what was changed in the weights

### 4.1 Scientific basis

Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, and Nanda (*Refusal in Language Models Is Mediated by a Single Direction*, arXiv:2406.11717, NeurIPS 2024) showed, across 13 open chat models up to 72B, that refusal is mediated by a one-dimensional residual-stream direction: erasing it reduces refusal of harmful instructions; adding it can induce refusal of harmless ones. They describe this as a white-box intervention with limited collateral on other capabilities **in their study**. That paper does not evaluate this Huihui checkpoint.

### 4.2 Implementation Huihui cites

The Huihui card says the uncensored derivative was "created with abliteration (see remove-refusals-with-transformers)" and repeats Sumandora's own wording: "a crude, proof-of-concept implementation to remove refusals from an LLM model without using TransformerLens." Sumandora's repository:

- Computes a refusal direction from harmful vs harmless hidden-state means (`compute_refusal_dir.py`).
- At inference, inserts `AblationDecoderLayer` modules that subtract that direction's projection from activations (`direction_ablation_hook`). The public Sumandora tree has no weight-save / orthogonalization exporter.
- Credits Arditi et al. as the technique source.
- Warns that some Qwen implementations do not expose `model.model.layers`.

Huihui uploaded a **full safetensor dump**, not a runtime hook. The card does not say whether they baked an Arditi-style rank-one edit into `W_out` (embedding / attention-out / MLP-out) or used another unpublished converter. Hugging Face's `base_model:finetune` tag is Hub taxonomy for a derived repo, not proof that Huihui ran SFT, LoRA, or DPO.

Community tooling (Orion-zhen / Undi95 `abliteration`) writes the usual rank-1 update that subtracts a scaled outer product of the refusal direction from the weight matrix, and notes explicitly that **abliteration is not full uncensorship**: the model may still fail to refuse without becoming a different, more capable model.

### 4.3 What Huihui actually discloses for this repo

Pinned Candidate A README (revision `e2f73ec7…`):

1. Base = `Qwen/Qwen3-30B-A3B-Instruct-2507`.
2. Method = abliteration via the Sumandora recipe, described as crude PoC.
3. Extra sentence: "Ablation was performed using a new and faster method, which yields better results."
4. Usage warnings: reduced safety filtering; not for all audiences; user bears legal/ethical responsibility; recommended for research/testing rather than production; huihui.ai disclaims consequences.
5. Example inference script still passes `enable_thinking = not nothink` into `apply_chat_template`, leftover from thinking-capable siblings. The official Instruct-2507 card says thinking mode is not supported. This project's SOURCE-OF-TRUTH records the same limitation.

Huihui does **not** publish, for Candidate A:

- which layers were modified (Candidate B's card *does* say layers 18-51);
- the refusal-direction vector, scale \(\alpha\), or whether the change is activation-hook vs baked weights;
- a capability regression table against Instruct-2507;
- independent third-party audit of residual refusal or capability damage.

This project's T2 license/lineage review records those statements as **repository-author declarations**, not independently proven facts, and does not treat them as capability evidence.

**What Veronica.v4 has done to the weights:** nothing after that community ablation. Project principles forbid changing foundation weights during the alias/persona-wrapper stage. Bootstrap verifies hashes and atomically promotes a directory; it does not train.

---

## 5. License and redistribution (documented, not legal advice)

All four T2 identities (A, A-control, B, B-control) declare Apache-2.0 at their pinned revisions; each listing contains `LICENSE` and none listed `NOTICE`. Apache-2.0, subject to its terms, permits reproduction, derivative works, display, sublicense, and distribution, and includes a patent license from contributors. Redistribution requires preserving the license, marking modified files, and retaining applicable notices. It does not grant trademarks and includes warranty/liability disclaimers.

Huihui's card `license_link` points at the **Qwen** Instruct-2507 LICENSE, which is consistent with a derivative that inherits the base license. The T2 review states that repository declarations do not replace final legal review, do not prove uploader authority or training-data rights, and must be re-checked against the exact artifacts if this project ever redistributes.

---

## 6. How Veronica.v4 uses this checkpoint

### 6.1 Serving stack (smoke / first-chat runtime)

Pinned in `config/runpod-core.json` and executed on successful starts:

- Image: `runpod/pytorch@sha256:0a360022e8de4375af99430f84e8b38951acc397252163a37ceac7204d01be35` (tag `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`)
- vLLM 0.11.0, Transformers 4.57.1, isolated runtime under `/workspace/veronica-core/runtime-vllm-0.11.0`
- GPU: 1x NVIDIA A100-SXM4-80GB, Secure Cloud, ceiling $1.75/hour, observed $1.59/hour
- Flags: `--dtype bfloat16 --max-model-len 8192 --max-num-seqs 1 --gpu-memory-utilization 0.92 --enforce-eager --served-model-name Veronica`
- First-chat load: 239.9 seconds, 56.9342 GiB model; idle allocation after serving 75,149 MiB including cache/runtime
- One streaming probe: 1.167 s to first content, 18.71 completion tokens per total second (smoke, not a benchmark)

T2 frozen comparison runtime is **different**: vLLM 0.28.0 and Transformers 5.8.0, context 32,768, because Candidate B's card requires those versions. The 0.11.0 smoke runtime is **not** accepted as the four-model comparison runtime.

### 6.2 Integrity pipeline

`scripts/prepare_runpod_model.py` downloads the pinned revision into `.uploading-<revision>`, verifies every expected path's byte count and SHA-256, then atomically `rename`s staging to the canonical directory. A bad existing copy is never overwritten. Interrupted downloads remain in staging. That is the project's implementation of "validate transfers before promotion from `.uploading` storage."

### 6.3 Wrapper layer (not weight changes)

`src/veronica_core` injects:

- A system persona naming the assistant Veronica (the checked-in persona text currently addresses "TRAVIS"; the owner-facing product name is Raine — a wrapper inconsistency, not a weight edit).
- Mode presets: Chat, Deep Reasoning, Creative, Coding. SOURCE-OF-TRUTH: these are prompt presets until native model controls are qualified. Candidate A cannot be turned into a thinking model by a preset.
- Public alias rewrite, health/capabilities endpoints, streaming SSE, browser UI.

The persona also asserts an uncensored, non-refusing policy in prompt text. That is **prompting**, stacked on top of community abliteration. It is not evidence that native refusal is gone, and it is not a fine-tune.

### 6.4 Timeline of project actions on this exact revision

| When | What happened to Candidate A | What did not happen |
| --- | --- | --- |
| 2026-08-30 | Provenance pin; first supervised A100 run; 27-file hash verification; first real API/UI chat; Pod terminated; volume retained | No fine-tune; no model selection |
| 2026-08-31 | Cold restart of the same weights; retained UI transcript; evaluation bank and recorded-conversation review | No training on the transcript |
| 2026-09-01 | T2 protocol freeze: A vs official control vs B vs B-control; license/lineage snapshots without weight downloads for the other three | No live T2 matrix |
| 2026-09-04 | Wrapper streaming, session persistence, Markdown, message controls | No GPU; no weight change |
| 2026-09-06 | Multiple authorized start attempts; some cancelled; some reached UI; stock/network issues documented | No Candidate B transfer |
| 2026-09-08 `T040904Z` | Same revision re-verified and served; wrapper health `ready` at 05:33:08 UTC; Pod `h33pceh6ug2q5x`; deadline 06:12:36 UTC | Still not T2; still not selected |

---

## 7. Observed behavior (smoke and human review, not T2)

These findings are about **this checkpoint as wrapped and served**, not official Qwen scores.

**First-chat (2026-08-30) manual review** (`runs/2026-08-30-supervised-first-chat/manual-review.md`):

- Creative four-sentence scene: produced. Broader prose not qualified.
- Coding `is_even`: generated function executed locally and passed the model's three asserts plus six extra integer cases. The model also **claimed** assertions passed though no execution tool existed — action-truthfulness failure.
- Probability of two red balls from 3 red + 2 blue without replacement: opened with **3/5**, then derived **3/10**. Contradiction, not a clean reasoning pass. The 2026-09-08 wrapper-smoke reasoning item repeats the same 3/5-then-3/10 pattern.
- Direct provider invented autobiographical travel; wrapper identified as AI. Identity consistency unproven.
- Memory language ("always remember") exceeded actual session context. No long-term memory module exists.
- UI two-turn recall of "silver compass" worked for that example only.

**Recorded conversation (2026-08-31)** owner-adjudicated: human mean 0.667/4, two critical failures (invented calendar/email monitoring and learning; invented telemetry, voice, and timings after being told it was hallucinating). Gate: `blocked_on_observed_failures`.

**2026-09-08 wrapper-smoke** still advertises `reasoning_content: null` (consistent with non-thinking Instruct) and `basicSmokePassed: true` with the explicit caveat that semantic correctness requires manual review. Capability qualification remains pending.

---

## 8. What has not been done

1. No LoRA, QLoRA, full fine-tune, merge, or quantization of these weights by Veronica.v4.
2. No hash-validated copy of the official Instruct-2507 control, Candidate B, or B-control on the volume.
3. No live T2 four-model, persona-free, matched-runtime comparison (vLLM 0.28.0 / Transformers 5.8.0 / 32,768 context).
4. No signed model-selection decision. Registry `selectionStatus` is `benchmark_required`.
5. No native tool-call parser qualification on this serve (`hermes` is reserved for the T2 A profile, not used on the 0.11.0 smoke command).
6. No long-context stress at 262K or 1M; configured context is 8,192.
7. No 48 GB quantization selection with measured VRAM. BF16 shards total ~61 GB on disk; the A100 80 GB smoke fit at ~57 GiB weights. A 48 GB GPU is not evidenced.
8. Wrapper "Deep Reasoning" is not native thinking.

---

## 9. Implications for the next milestone

Gate R ("Engine Accounted For") still wants a complete manifest for every T2 model, not only A; transfer validation exists in code and was proven for A; GPU/price/deadline are recorded (A100, $1.75/hour ceiling, per-run duration). Gate T2 ("Mind Proven") cannot close on this paper or on smoke chats.

The honest next live experiment, when freshly authorized, is still the frozen T2 protocol: serve this exact revision and its official control, then B and B-control, on the matched 0.28.0 runtime, and score the 60-case pack plus executable coding, schema, tools, and long-context stress — without treating wrapper persona as intelligence.

Until that exists, Candidate A is a **provisional, hash-verified, actually serving** uncensored Instruct-2507 MoE with documented contradiction and action-truthfulness failures. It is the right installed model. It is not a finished Veronica mind.

---

## 10. Sources

Primary Hub and cards

1. https://huggingface.co/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated — Huihui Candidate A card (fetched 2026-09-08; matches pinned README).
2. `runs/2026-09-08T040904Z-start-veronica/provenance/candidate/README.md` and `hub-metadata.json` — pinned revision snapshot, including `sha` `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`.
3. https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507 — official Instruct-2507 card.
4. `runs/2026-09-01-t2-qualification/provenance/candidate-a-control/README.md` — pinned control card.
5. https://github.com/QwenLM/Qwen3 — Qwen3-2507 release notes and Apache-2.0 statement.
6. Qwen Team, *Qwen3 Technical Report*, arXiv:2505.09388.

Abliteration

7. Arditi et al., *Refusal in Language Models Is Mediated by a Single Direction*, arXiv:2406.11717 (NeurIPS 2024).
8. https://github.com/Sumandora/remove-refusals-with-transformers — implementation Huihui cites.
9. https://github.com/andyrdt/refusal_direction — Arditi et al. code.
10. https://github.com/Orion-zhen/abliteration — community weight-bake formula and "not uncensorship" note.

License

11. https://www.apache.org/licenses/LICENSE-2.0
12. `runs/2026-09-01-t2-qualification/license-review.md`

Project evidence (this exact revision)

13. `config/model-registry.json`, `config/runpod-core.json`, `config/t2-qualification.json`
14. `docs/SOURCE-OF-TRUTH.md`, `TODO.md`, `AGENTS.md`
15. `runs/2026-08-30-supervised-first-chat/decision.md`, `manual-review.md`, `validated-model-manifest.json`
16. `runs/2026-09-08T040904Z-start-veronica/` — `validated-model-manifest.json`, `expected-model-manifest.json`, `server-command.json`, `volume-inspection.txt`, `wrapper-smoke.json`, `profile.json`
17. `runs/2026-09-01-t2-qualification/decision.md`
18. `runs/2026-08-31-recorded-conversation-eval/report.md`
19. `scripts/prepare_runpod_model.py`
20. `src/veronica_core/persona.py`, `src/veronica_core/app.py`

---

## 11. Independent agent cross-check (2026-09-08)

A bounded deep-research workflow (`deep-research-2`) independently verified Candidate A identity, Apache-2.0, 13-shard BF16 dump, volume `v53gj9flzs`, vLLM 0.11.0 serve alias `Veronica`, absence of Candidate B on the volume listing, first-chat closeout, recorded-conversation gate, and T2 still frozen. Raw agent report: `2026-09-08-candidate-a-deep-research-2-agent-report.md`. Status: **Partial**.

**Rejected mix-up:** some researchers inspected `/home/dubs/projects/veronica-v4-LOCAL` and local Ollama tag `Veronica:latest` (a bartowski `dolphin-2.9-llama3-8b` Q4_K_M GGUF, ~4.92 GB). That leftover tree is **not** canonical Veronica.v4. Canonical `docs/SOURCE-OF-TRUTH.md` mentions Ollama only as an analogy for an alias/Modelfile; this project serves Candidate A through vLLM/RunPod. Do not treat Dolphin 3 / `veronica-v.2:dolphin3-8b-uncensored` as the installed foundation.

**Adopted extras from that run:** official Qwen 16-shard vs Huihui 13-shard packing; Hub commit titles (Huihui `e2f73ec7` “Upload Modelfile” 2025-08-02; Qwen control `0d7cf239` “Update tokenizer_config.json” 2025-09-17); Sumandora public code is activation ablation without a weight exporter; expected-manifest SHA-256 vs git-blob split documented above.

## 12. Coverage and uncertainty

- Huihui's "new and faster method" is not specified at the layer/tensor level for Candidate A. Independent reconstruction of the ablation is not claimed. The published Sumandora recipe ablates activations at inference; Huihui's artifact is a weight dump whose exact bake recipe is unpublished.
- Official Qwen benchmarks are for the untouched Instruct-2507, not this derivative, and not this project's 8k-context vLLM 0.11.0 serve.
- Apache-2.0 documentation is not a lawyer's opinion.
- Live Pod presence after 2026-09-08T06:12:36Z is not asserted; health `ready` was observed at 05:33:08Z that day.
- This paper does not authorize paid compute, training, or foundation selection.
