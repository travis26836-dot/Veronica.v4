# Research result (raw `deep-research-2` agent output)

**Archived:** 2026-09-08. This is the unedited workflow report. Canonical synthesis is `2026-09-08-candidate-a-huihui-qwen3-30b-a3b-instruct-2507-abliterated.md`. Several claims below inspected `/home/dubs/projects/veronica-v4-LOCAL` and a local Ollama `Veronica:latest` Dolphin GGUF; those are **not** the installed RunPod foundation.

**Status: Partial**

The checkpoint installed on RunPod network volume `v53gj9flzs` and served by vLLM under `--served-model-name Veronica` is `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` at git revision `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`, an Apache-2.0 abliterated derivative of `Qwen/Qwen3-30B-A3B-Instruct-2507`. [S1][S10] That serve name is an alias for this Hub dump, not a separately trained Veronica model: local v4 source-of-truth still names chat as Ollama `veronica-v.2:dolphin3-8b-uncensored`, and this revision is not a T2-qualified or selected foundation. [S4] `huihui-ai/Huihui-Qwen3.8-27B-abliterated` is a different lineage and was not present on the volume.

### Identity and lineage
The published Huihui repo is tagged Apache-2.0 and `text-generation`, with `qwen3_moe` / `Qwen3MoeForCausalLM` and Hub `base_model` `Qwen/Qwen3-30B-A3B-Instruct-2507`; `commits/main` HEAD is that SHA, titled “Upload Modelfile” (2025-08-02). The official untouched control is `Qwen/Qwen3-30B-A3B-Instruct-2507` at `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` (HEAD “Update tokenizer_config.json”, 2025-09-17), shipping Apache License 2.0 with Copyright 2025 Alibaba Cloud. [S2] Veronica.v4 pins that Qwen commit as Candidate A’s `official_control` only—not the live foundation—and would store it at `/workspace/veronica-core/models/Qwen3-30B-A3B-Instruct-2507/0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` on volume `v53gj9flzs`. [S9]

Candidate B (`huihui-ai/Huihui-Qwen3.8-27B-abliterated` at `739e3c5b89849f6c238ce1e5b70008612ae42cdd`) is an abliterated `Qwen/Qwen3.8-27B` checkpoint with `qwen3_5` / `Qwen3_5ForConditionalGeneration` and pipeline tag `image-text-to-text`, not the served MoE causal LM. [S3]

The local public Ollama library alias `Veronica:latest` is also not this checkpoint: it reuses the `sunrise-dolphin:latest` blob, a 4,920,746,560-byte bartowski `dolphin-2.9-llama3-8b` Q4_K_M GGUF (`sha256:7dcc6b844c309701ddcb20642d5729736a04c70cf10fdd6b3c0653b16eb649f4`). The Huihui card recommends `ollama run huihui_ai/qwen3-abliterated:30b-a3b-instruct-2507-q4_K_M` and does not name a Veronica alias. [S5]

### Architecture and serving
The served files are a full BF16 Qwen3-MoE weight dump—30,532,122,624 BF16 parameters in 13 safetensor shards (`model-00001-of-00013` … `model-00013-of-00013`)—with architecture fields matching the control (`Qwen3MoeForCausalLM`, `qwen3_moe`, `hidden_size` 2048, 48 layers, 128 experts, 8 experts per token, `torch_dtype` bfloat16) and identical `generation_config.json` (temperature 0.7, `top_k` 20, `top_p` 0.8). [S14] The pinned control config also sets SiLU, 32 attention heads, 4 key-value heads, `moe_intermediate_size` 768, and `max_position_embeddings` 262144. [S6] The 2507 Instruct card states 30.5B total parameters with 3.3B activated, 48 layers, 128 experts with 8 activated, native context length 262,144, and non-thinking-only operation. [S7] The official Hub snapshot ships the same BF16 parameter count as 16 shards with 61,064,245,248 bytes of mapped weights. [S8]

On-disk validation for the volume run recorded that Huihui 13-shard set (not Qwen’s 16-shard layout), including `model-00001-of-00013.safetensors` at 4,997,184,968 bytes (`sha256 a2c987dc…`) and `model-00013-of-00013.safetensors` at 1,094,220,288 bytes (`sha256 374e82aa…`); `prepare_runpod_model.py` `verify_files()` rejects size or sha256/git-blob mismatches before serve. [S11] The 2026-09-08 start served that validated Huihui directory with vLLM 0.11.0, `--dtype bfloat16`, `--max-model-len 8192`, and `served_model_name=['Veronica']` on `127.0.0.1:8000`; the volume mount listed only the Huihui model directory.

### Weight changes versus control versus the Veronica name
The Huihui card describes an uncensored derivative of the official 2507 Instruct model created with abliteration, citing only `Sumandora/remove-refusals-with-transformers`, plus an unspecified “new and faster” ablation said to yield better results. [S12] It claims refusals were removed and that safety filtering was “significantly reduced,” but it does not name layer/tensor edits, rank-1 orthogonalization, LoRA, SFT, or DPO; the Hub still tags the repo as a finetune of the Qwen control. [S13]

The cited method repo computes a unit refusal direction as harmful-minus-harmless hidden-state means (at about 60% depth) and, at inference, inserts `AblationDecoderLayer` modules that subtract that direction’s projection from activations; its public tree has no weight-save or orthogonalization script. [S15] That technique is credited to Arditi et al. 2024, which treats refusal as a single residual-stream direction and an equivalent rank-one edit \(W_{out}' \leftarrow W_{out} - \hat{r}\hat{r}^{T} W_{out}\) on residual-writing matrices (embedding, positional, attention-out, MLP-out), not gradient fine-tuning. [S16]

### What Veronica.v4 has done with this revision

| Date (UTC) | Action | Result |
|---|---|---|
| 2026-08-30 | Live serve on one A100, vLLM 0.11.0, alias Veronica | Five direct-provider responses, five Windows-wrapper responses, and a two-turn browser chat; pod `r2c0u02vforaqe` terminated and confirmed absent at 23:11:49; 300 GB volume `v53gj9flzs` (EUR-IS-1) retained [S17] |
| 2026-08-31 | Recorded-conversation eval of that chat (no new model calls) | 3/3 samples human-reviewed; human mean 0.667/4; 2 critical failures; gate `blocked_on_observed_failures`; not a foundation pass or training authorization [S19] |
| 2026-09-04 | Authorized recovery START on existing volume, vLLM 0.11.0 | Direct and wrapper smokes produced real text; Candidate B and both controls not served; frozen T2 runtime (vLLM 0.17.0 + Transformers 5.8.0) unsatisfiable; pod `pbym3oq2acr3uj` at $1.59/hour confirmed absent at 08:05:58Z [S21] |

The first live UI exchange was Chat-mode with “Core connected”: the user asked Veronica to remember “silver compass,” and the follow-up answer was exactly that phrase. [S18]

### What has not been done, and documented limits
T2 (`t2-untouched-foundation-v2`) remains `frozen_before_live_runs`: a four-model comparison of Candidate A, Candidate B, and both official controls. It explicitly does not treat the Candidate A smoke conversation as a T2 pass and does not authorize paid compute, downloads, transcript upload, training, or foundation-weight changes. [S20] No four-model matched-runtime comparison has been run; the 2026-09-04 recovery was not that comparison.

Native context is 262,144 but serving used `--max-model-len 8192`, and the 2507 Instruct line is non-thinking only. The Huihui card warns that safety filtering is significantly reduced. Human review of the retained first conversation scored invented quote/calendar-email scanning and invented telemetry (after being told it was hallucinating) as critical failures, with no code or tools executed.

## Sources
- [S1] "Hugging Face model API: huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated" — "https://huggingface.co/api/models/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated" (independently checked against "Hugging Face model API and README: huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated" — "https://huggingface.co/api/models/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated")
- [S2] "Hugging Face model API: Qwen/Qwen3-30B-A3B-Instruct-2507" — "https://huggingface.co/api/models/Qwen/Qwen3-30B-A3B-Instruct-2507" (independently checked against "Hugging Face model API and LICENSE: Qwen/Qwen3-30B-A3B-Instruct-2507" — "https://huggingface.co/api/models/Qwen/Qwen3-30B-A3B-Instruct-2507")
- [S3] "Hugging Face model API: huihui-ai/Huihui-Qwen3.8-27B-abliterated" — "https://huggingface.co/api/models/huihui-ai/Huihui-Qwen3.8-27B-abliterated"
- [S4] "VERONICA v4 execution rules / donors / checkpoints / .env" — "/home/dubs/projects/veronica-v4-LOCAL/AGENTS.md" (independently checked against "VERONICA v4 LOCAL docs, .env, server.py, and Windows Ollama manifest" — "/home/dubs/projects/veronica-v4-LOCAL/AGENTS.md")
- [S5] "Local Ollama manifest: registry.ollama.ai/library/Veronica:latest" — "/home/dubs/.ollama/models/manifests/registry.ollama.ai/library/Veronica/latest" (independently checked against "Local Ollama manifests plus bartowski/dolphin-2.9-llama3-8b-GGUF" — "/home/dubs/.ollama/models/manifests/registry.ollama.ai/library/Veronica/latest")
- [S6] "Qwen3-30B-A3B-Instruct-2507 config.json @ 0d7cf239" — "https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507/raw/0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe/config.json"
- [S7] "Qwen3-30B-A3B-Instruct-2507 model card" — "https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507" (independently checked against "Qwen3-30B-A3B-Instruct-2507 model card and config.json" — "https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507")
- [S8] "Hugging Face model API and tree for Qwen3-30B-A3B-Instruct-2507" — "https://huggingface.co/api/models/Qwen/Qwen3-30B-A3B-Instruct-2507"
- [S9] "Veronica.v4 runpod-core.json and T2 control profile" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/config/runpod-core.json" (independently checked against "Veronica.v4 runpod-core.json, T2 Candidate A control profile, model-registry.json" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/config/runpod-core.json")
- [S10] "2026-09-08T040904Z-start-veronica serve evidence" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-09-08T040904Z-start-veronica/server-command.json"
- [S11] "validated-model-manifest.json and prepare_runpod_model.py" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-09-08T040904Z-start-veronica/validated-model-manifest.json" (independently checked against "validated-model-manifest.json, Qwen 16-shard Hub siblings, prepare_runpod_model.py" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-09-08T040904Z-start-veronica/validated-model-manifest.json")
- [S12] "huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated README" — "https://huggingface.co/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated/raw/main/README.md"
- [S13] "Hugging Face model API for Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated" — "https://huggingface.co/api/models/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated" (independently checked against "Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated model card and Hub API" — "https://huggingface.co/api/models/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated")
- [S14] "Huihui and official Qwen3-30B-A3B-Instruct-2507 config.json / Hub files" — "https://huggingface.co/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated/raw/main/config.json"
- [S15] "Sumandora/remove-refusals-with-transformers" — "https://github.com/Sumandora/remove-refusals-with-transformers"
- [S16] "Refusal in Language Models Is Mediated by a Single Direction (Arditi et al., 2024)" — "https://arxiv.org/html/2406.11717"
- [S17] "First real Veronica conversation — achieved; Pod terminated" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-08-30-supervised-first-chat/decision.md"
- [S18] "ui-live-transcript.txt" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-08-30-supervised-first-chat/ui-live-transcript.txt"
- [S19] "Veronica evaluation report (recorded conversation)" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-08-31-recorded-conversation-eval/report.md"
- [S20] "t2-qualification.json" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/config/t2-qualification.json"
- [S21] "Recovery start — Candidate A answered; deadline shutdown confirmed" — "/mnt/c/Users/raine/DEVELOPMENT/Projects/Veronica.v4/runs/2026-09-04T070444Z-start-veronica/decision.md"

## Coverage and uncertainty
- "Question 1 uncertainty: No inspected local file uses the labels “Candidate A” or “Candidate B” for these Hugging Face repos; v4 checkpoint A/B instead means UI ports 4175 (3.1) vs 4176 (v4), both on Dolphin 3."
- "Question 1 uncertainty: Hugging Face does not declare a public API alias named Veronica for Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated; the local Veronica Ollama tag is a different 8B Dolphin model."
- "Question 1 uncertainty: Weights could exist on uninspected stores (Runpod volumes, extra disks, other Hugging Face cache roots); only the listed Ollama manifests and two hub caches were checked."
- "Question 1 uncertainty: Whether anyone later intended to retarget Veronica.v4 onto Candidate A is not recorded in the inspected source-of-truth files."
- "Question 2 uncertainty: No inspected volume listing or validated-model-manifest shows official Qwen/Qwen3-30B-A3B-Instruct-2507 weights present or hash-checked on v53gj9flzs."
- "Question 2 uncertainty: The T2 official-control profile would serve Qwen with vLLM 0.28.0 and maxModelLen 32768, not the live 0.11.0 / 8192 command; that control serve was not observed in the inspected run artifacts."
- "Question 3 uncertainty: The Huihui card does not state which tensors, layers, or scale the “new and faster method” actually changed, so the published shards cannot be mapped to a documented per-weight recipe from that card alone."
- "Question 3 uncertainty: Hugging Face’s base_model:finetune tag is Hub taxonomy for a derived model, not a claim in the card that Huihui ran SFT/LoRA/DPO."
- "Question 3 uncertainty: Sumandora’s public inference path is activation ablation via inserted layers, while Huihui uploaded full safetensors; the card does not say they applied Arditi-style weight orthogonalization to produce those files."
- "Question 3 uncertainty: src/veronica_core/persona.py was not found anywhere in the inspected workspace; wrapper-only persona is evidenced by MODELFILE SYSTEM and AGENTS.md, not by that file."
- "Question 3 uncertainty: Canonical docs mention /home/dubs/projects/veronica-v4, but that path does not exist; the live tree inspected is /home/dubs/projects/veronica-v4-LOCAL."
- "Question 4 uncertainty: Later START folders after 2026-09-04 (including 2026-09-06T081556Z and 2026-09-08T023524Z / 2026-09-08T040904Z) contain additional Candidate A manifests, provider-smoke, and some termination receipts, but several of those folders have no decision.md, and 2026-09-08T040904Z has startup-ready/provider-smoke without a termination.json, so post-snapshot Pod state is not established from a single closeout record."
- "Question 4 uncertainty: config/t2-qualification.json now pins vLLM 0.28.0 / Transformers 5.8.0 (protocol v2); the inspected 2026-09-04 T2 compatibility failure was against the earlier frozen v1 pair vLLM 0.17.0 + Transformers 5.8.0. No inspected run proves that the v2 0.28.0 stack installed or served Candidate A."
- "Question 4 uncertainty: No inspected volume listing after 2026-09-08T023524Z shows a Candidate B weight directory; that is evidence B was not present then, not a proof it was never added later."
- "Question 5 uncertainty: These named sources do not by themselves prove that no later unrecorded training or four-model live run occurred outside the repository; they only record that this revision does not claim those actions."
- "Question 5 uncertainty: Some T2 run temp directories were unreadable (permission denied), so they were not used as evidence."
- "Question 6 uncertainty: TODO.md cites runs/2026-08-31-recorded-conversation-eval/report.json with human_reviewed=3, human_critical_failures=2, and gate blocked_on_observed_failures, but that run directory was not present in the inspected worktrees, so those owner-adjudication numbers were not independently verified."
- "Question 6 uncertainty: The frozen T2 matched runtime uses maxModelLen 32768, while recovery serving of Candidate A uses 8192; no inspected live run has executed the four-model T2 comparison or a native 262,144-token stress test."
- "Question 6 uncertainty: The 2026-09-04 CC/MB critical flags are assistant-advisory; that packet's decision says owner/human adjudication of those six samples was still pending."
- "10 malformed or over-cap candidate claim(s) were excluded before verification."
- "Claim claim-5 was excluded by verification: Ollama/HF caches indeed lack Huihui, but the stated tag inventory is wrong (four tags, not “Veronica/sunrise-dolphin” plus two others) and Veronica.v4 contains many Huihui matches.."
- "Claim claim-17 was excluded by verification: LOCAL v4 does use Dolphin 3 plus MODELFILE SYSTEM, but canonical Veronica.v4 chats with Huihui Candidate A and contains src/veronica_core/persona.py.."
- "Claim claim-18 was excluded by verification: The 2026-08-30 download into .uploading-e2f73ec7… of 27 files, VERIFIED lines for all 13 safetensor shards, and promotion after checks are documented, but expected-model-manifest.json has sha256 null for 13 of 27 files. executed-bootstrap.py only SHA-256-compares files with an expected sha256 (the 13 shards plus tokenizer.json); other files are accepted via git-blob SHA-1. That is not SHA-256 verification of every file.."
