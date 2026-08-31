# Krea2 Adult Studio research brief

Research date: 2026-08-30  
Status: evidence gathered; visual direction pending before UI implementation

## Executive decision

Build the Studio around the official Krea2 family, but keep the pipeline modular:

- **Krea2 RAW** is the trainable base for Studio-owned LoRAs and later fine-tuning.
- **Krea2 Turbo** is the fast image-generation target. Krea's own guidance supports training LoRAs against RAW and applying them to Turbo.
- **Third-party Krea2 checkpoints and LoRAs remain runtime patches** unless their creator explicitly permits commercial derivatives. Do not merge or bake restricted assets into a Studio checkpoint.
- **Wan2.2** is the recommended open video stage: Krea2 makes controlled keyframes; Wan2.2 animates short image-to-video shots; RIFE and/or SeedVR2 finish them; an editor assembles the film.
- **Veronica is the primary code and visual donor.** Port its backend lifecycle, resource catalog, prompt planning, generation history, and celestial/noir design language. Recompose them into a focused shot workspace instead of copying the crowded page wholesale.

This can be an adult-capable creator product, but not literally “nothing off limits.” The Krea2 license requires reasonable content filtering and its acceptable-use policy prohibits CSAM, non-consensual intimate imagery, rights violations, and unlawful content. The product boundary should be **lawful, consensual adults only**, with provenance and reporting built in.

## Reference video: confirmed evidence

User-supplied media:

- Original media URL: <https://image-b2.civitai.com/file/civitai-media-cache/5ded13a3-7106-4660-9330-29c063a07797/original>
- Local evidence file: `research/civitai-reference/reference-media`
- SHA-256: `FA5F0EEDC35871AFB88561DC68AEBEFD199B537AE944BFB48CF42B29BD681D36`
- File size: 57,441,687 bytes
- Video: H.264 Main, 1080×1920, 24 fps, 3,190 frames, 132.9167 seconds
- Audio: AAC stereo, 48 kHz, approximately 320 kbps
- Container metadata: created 2026-08-28; encoded by Blackmagic Design DaVinci Resolve; timecode `01:00:00:00`
- Scene-change sampling found about 35 threshold hits. After discounting fades and duplicate hits, the film contains roughly 25–30 real cuts—an average shot length around four to five seconds.

Connected public records:

- Image/video record: <https://civitai.red/images/141118212>
- Post: <https://civitai.red/posts/30680384>
- Series article: <https://civitai.red/articles/32664/fade-into-darkness-video-series>
- Title: **Fade Into Darkness 🖤 (017)**
- Uploaded filename: `Fade_016.mp4`
- Creator: **RLS_Animation / Red Line Studios**
- Published: 2026-08-28
- Story setting: an aging adult-video store in a forgotten strip mall; chapter 17 of a short-film series.

Recorded generation metadata:

- Prompt: `masterpiece, detailed_eyes, high_quality, best_quality, highres, absurdres, 8k, subject_focus, depth_of_field`
- Negative prompt: `blurry`
- Steps: `30`
- CFG: `6`
- Sampler: `Euler a`
- Checkpoint: **LUSTIFY! [NSFW checkpoint]**, version **v10 (Krea 2)**
- Recorded tools: **ComfyUI, KREA, DaVinci Resolve**
- Technique tags: `txt2img`, `img2img`, `inpainting`, `workflow`, `vid2vid`, `txt2vid`, `img2vid`, `controlnet`
- Public content tags are sparse: article tag `story`; post tag `woman`.

The technique tags describe the creator's broad process and do not prove that every technique was used in every shot. The final video file independently confirms DaVinci Resolve as the finishing/editor stage.

### What the evidence supports

The visual consistency, cut count, broad workflow tags, and editor metadata support a production pattern of:

1. Character and location bible.
2. Individually composed keyframes or stills.
3. Short motion clips generated from those keyframes.
4. Selective repair, interpolation, and/or upscale.
5. Final assembly, audio, titles, and pacing in Resolve.

The public metadata does **not** identify the exact motion model. Treat any claim that a particular video model created these shots as unverified.

## Exact checkpoint page and license consequence

Checkpoint page: <https://civitai.red/models/573152/lustify-nsfw-checkpoint?modelVersionId=3112728>

The recorded version is `lustify-v10-krea-turbo-fp8.safetensors`:

- Size: 11.94 GB
- AutoV2: `94D92700FC`
- SHA-256: `94D92700FC45200EF053895EC5655D4F64A69B924C1EFAA457521DFC22BD5E00`
- Published variants include Turbo FP8, int8-convrot, BF16, Q2 GGUF, Q4 GGUF, and Raw variants.

The creator's page currently marks commercial generated images as allowed but **derivative models as not allowed** (`allowDerivatives: false`). Therefore:

- Allowed role: optional, separately licensed inference checkpoint/profile.
- Disallowed role without written permission: fine-tuning base, merged checkpoint, baked LoRA bundle, or redistributed Studio model.
- Before charging for hosted generations through this third-party checkpoint, obtain explicit creator permission or a legal review of the intended service model; the current flags do not clearly grant every hosted-API use.

The creator's recommended Krea workflow is published as `LustiKrea.json`, but the workflow download was inaccessible from the current Civitai account state. We did not bypass that access control. Its public metadata confirms a Krea2 workflow designed to minimize custom nodes and use subgraphs.

## Krea2 model contract

Primary sources:

- Technical report: <https://www.krea.ai/blog/krea-2-technical-report>
- Official code: <https://github.com/krea-ai/krea-2>
- Official ComfyUI tutorial: <https://docs.comfy.org/tutorials/image/krea/krea-2>
- Comfy model files: <https://huggingface.co/Comfy-Org/Krea-2>
- Community license: <https://www.krea.ai/krea-2-licensing>
- Acceptable-use policy: <https://www.krea.ai/krea-2-use-policy>
- Safety documentation: <https://github.com/krea-ai/krea-2/blob/main/docs/safety.md>

Krea2 is a 12.9B diffusion transformer using Qwen3-VL text features and a Qwen Image VAE. The practical split is:

| Variant | Role | Starting inference profile |
|---|---|---|
| Krea2 RAW | LoRA training, fine-tuning, maximum exploration | 52 steps, CFG 3.5 |
| Krea2 Turbo | Routine Studio inference | 8 steps, CFG 1/disabled |

The official ComfyUI asset contract is a Krea2 diffusion model, the Krea Qwen3-VL 4B text encoder, the Qwen Image VAE, and optional compatible Krea2 LoRAs. The currently running local ComfyUI version supports native Krea2 nodes, but this laptop's 6 GB GPU and 8 GB system RAM cannot load the installed 13.1 GB FP8 diffusion file. Local development should therefore exercise the UI, API, graph compilation, validation, and queue states; full renders belong on a rented GPU.

Krea's current community license permits commercial use below USD $1 million in company-wide trailing-12-month revenue, subject to its terms; an enterprise license is required at or above that threshold. Distributed derivatives must retain the license and notice, disclose modification, and begin the model name with “Krea.”

## Video stage

Recommended open model: **Wan2.2**.

- Official repository: <https://github.com/Wan-Video/Wan2.2>
- Official ComfyUI workflows: <https://docs.comfy.org/tutorials/video/wan/wan2_2>
- License: Apache 2.0 according to the official repository and ComfyUI documentation.
- `Wan2.2-TI2V-5B` handles both text-to-video and image-to-video. The official repository documents 720p generation on a 24 GB GPU with offloading; ComfyUI documents more aggressive native offloading for lower-VRAM experiments.
- `Wan2.2-I2V-A14B` is the higher-capacity image-to-video path and should be scheduled on a larger cloud GPU.

Finishing candidates:

- RIFE frame interpolation: <https://github.com/hzwer/Practical-RIFE>
- SeedVR2 video restoration/upscale: <https://github.com/ByteDance-Seed/SeedVR>
- Final edit: DaVinci Resolve, matching the reference file's encoder metadata.

Run the image and video stages sequentially and let ComfyUI own model unloading/offloading. Do not try to keep Krea2 and Wan resident together on a budget GPU.

## Custom-node candidates

These are candidates for review, not pre-approved dependencies:

| Candidate | Purpose | Studio use |
|---|---|---|
| <https://github.com/lbouaraba/comfyui-krea2edit> | Identity-preserving Krea2 edits/restaging | Repose or restage a locked character while preserving identity |
| <https://github.com/facok/comfyui-krea2-controlnet> | Krea2 Control LoRA and depth control | Camera blocking, pose/depth consistency, video-frame batches |
| <https://github.com/januspluto/ComfyUI-Krea2-Regional> | Regional prompting and per-region LoRAs | Multi-character scenes without LoRA or identity bleed |
| <https://github.com/lokitsar/ComfyUI-Krea2-MultiLoRA-Composer> | 1–5 character LoRA layout and scene JSON | Strong donor for the Studio's scene/character data contract |
| <https://github.com/Shrey-1o1/ComfyUI-Krea2-FilmStudio-Vionex> | Film-oriented Krea2 graph composition | Research donor for reference routing, two-pass render profiles, and hidden reproducible config |

Every custom node must pass a source review, pinned-commit check, dependency review, and small workflow test before installation. Low-adoption nodes should not become required infrastructure until their code has been audited.

## Curated workflow architecture

The Studio should compile a stable **shot package** into backend-specific graph JSON:

1. **Intent** — natural-language concept and legal/adult-only declaration.
2. **Continuity** — project, sequence, shot, character IDs, wardrobe, location, and reference images.
3. **Composition** — shot size, camera angle, lens, framing, pose/action, lighting, mood, and aspect ratio.
4. **Model profile** — Krea2 variant, checkpoint, LoRA stack, per-region assignments, triggers, weights, and schedules.
5. **Motion** — still, first/last-frame, image-to-video, duration, motion amount, camera move, and FPS target.
6. **Finishing** — repair mask, interpolation, upscale, color target, audio, and export preset.
7. **Provenance** — model/version/hash, workflow revision, seed, source references, consent/license records, and output lineage.

The natural-language prompt stays visible. Selected controls add structured clauses through a versioned prompt dialect; they should not silently overwrite the user's text. Advanced values live behind a compact inspector and can be exposed as fine-tuning sliders.

## LoRA and checkpoint migration rules

1. Register every asset with family, base variant, architecture, text encoder, VAE, trigger tokens, recommended strength, source, license, commercial-output rights, derivative rights, file size, and SHA-256.
2. Do not apply SDXL, Pony, Flux, or Krea2 LoRAs across model families. “Safetensors” is only a file format, not compatibility proof.
3. Train Studio-owned Krea2 LoRAs on official RAW and validate them on both RAW and Turbo.
4. Keep third-party LoRAs as non-destructive runtime patches. Never bake them into a Studio checkpoint unless derivative and commercial rights are explicit.
5. Namespace prompt recipes by asset and version. A LoRA trigger should come from its registry record, not hard-coded UI conditionals.
6. Support ordered LoRA slots, per-region assignment, weight, start/end schedule, and conflict warnings. Preserve the complete stack in the shot manifest.
7. Install through a server-side job: download to a hidden `.uploading` file, resume when possible, verify byte count and SHA-256, atomically promote, then refresh the resource registry. Credentials never reach the browser.

## Veronica donor reuse map

Canonical donor: `/home/dubs/code/veronica-ai-v2/veronica-home`

| Donor capability | Verified donor implementation | Adult Studio destination |
|---|---|---|
| Backend selection and warm-up | `start_image_backend`, `image_launcher_status`, `stop_conflicting_image_runtime`; `/api/image/start` and launcher feed/status routes | Backend adapter and runtime-state service |
| ComfyUI/A1111 isolation | Explicit `comfyui_base_url`; competing-runtime shutdown before start | One active GPU backend at a time |
| Resource discovery | `/api/image/resources`, `loadImageResources`, backend model/LoRA/sampler inspection | Model registry and live compatibility selector |
| Reviewed downloads | `image_catalog`, `start_image_catalog_install`, catalog install route | License-aware asset installer with hash validation |
| Prompt planning | `prepare_image_prompt`, `image_prompt_plan`, `refreshImagePromptPlan` | Versioned prompt compiler and transparent trigger preview |
| Structured adult prompt schema | `list_nsfw_prompt_schema`, `build_nsfw_prompt`, schema/plan renderers | Replace hard-coded dialect conditions with registry-driven field definitions |
| Generation and history | `/api/image/generate`, Comfy prompt queue/history/view polling, `renderImageHistory` | Shot job queue, output lineage, compare/rerun |
| Visual system | `styles.css`, Image Studio screenshot, celestial noir palette and typography | Preserve tokens and brand; redesign layout around one selected shot |

The current NoirWorks `ComfyUI-Pipeline-Foundation` remains the durable operations/research scaffold. New application source should live in its own clean app package; research, logs, exports, and scratch material should not be mixed into source directories.

## Five build steps

### 1. Lock the foundation profile

Approve official Krea2 RAW + Turbo, exact text encoder/VAE, hashes, licenses, and RunPod storage locations. Mark LUSTIFY and the current six adult LoRAs as separately reviewed optional assets, never assumed mergeable.

**Done when:** `model-profile.json` has no hold status and a reproducible minimal cloud render proves the base graph.

### 2. Port the control plane

Extract Veronica's backend lifecycle, guarded API proxy, resource discovery, reviewed installer, workflow profiles, queue polling, and history into a clean Studio service. Keep ComfyUI/A1111 adapters behind one interface.

**Done when:** the local UI can select a backend, warm/check it, read inventory, compile a graph, queue a mocked or remote job, and show durable state without exposing secrets.

### 3. Build the selected shot workspace

Implement the chosen visual direction with project/sequence/shot navigation, a large preview, natural-language prompt, structured shot controls, active model/LoRA stack, references, queue status, and output comparison. Preserve Veronica's celestial/noir design system.

**Done when:** a user can create and rerun a fully specified shot without opening raw ComfyUI.

### 4. Ship versioned graph profiles

Create tested graph templates for Krea2 text-to-image, identity edit, depth/control, regional Multi-LoRA composition, Wan2.2 image-to-video, and finishing. Compile shot packages into graphs rather than editing node IDs directly in UI code.

**Done when:** each profile passes schema validation, dry-run compilation, and one cloud evidence render with a saved manifest.

### 5. Productionize cloud execution

Use short-lived RunPod Pods during development with automatic termination. When the workflow is stable, package the worker for RunPod Serverless scale-to-zero, add authenticated jobs, quotas/credits, retry/idempotency, provenance, moderation gates, and metered storage.

**Done when:** an idle system has no GPU worker cost and each paid request has auditable input, model, workflow, output, duration, and cost records.

## First implementation boundary

The next source-code change should begin **after selection of one UI direction**. The first implementation slice is Steps 1–3 only: profile/registry, donor control-plane extraction, and the selected shot workspace wired to local ComfyUI's API states. Video generation and billing follow after the core shot workflow is usable.

