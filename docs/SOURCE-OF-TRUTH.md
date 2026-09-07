# Veronica Core - Source of Truth

**Document status:** canonical

**Last structural reset:** 2026-08-30

**Evaluation checkpoint, 2026-08-31:** The [development evaluation system](evals/README.md) now has 60 cases, 69 turns, transcript intake, human/advisory scoring, dataset checks and a reusable skill. The saved conversation is authorized as evaluation input; its assistant outputs are untrusted evidence, not approved training targets. Offline harness validation does not qualify the foundation. The [checkpoint decision](../runs/2026-08-31-evaluation-foundation/decision.md) records the evidence. Foundation weights and the `Veronica` alias are unchanged; no training, new inference or paid compute was started for this checkpoint.

**Chat-wrapper checkpoint, 2026-09-04:** The local wrapper now forwards `stream=true` SSE when the provider supports it, and the browser chat persists the session, exposes retry/stop/copy/regenerate, and renders escaped Markdown. Native tools, memory, fine-tuning, and T2 qualification are unchanged. Evidence: `runs/2026-09-04-a1-chat-controls/decision.md`.

## 1. What we are building

Veronica is one highly capable general-purpose AI with a unique identity and a modular agent wrapper. The core must chat naturally, reason deeply, write creatively, code, and call tools before specialized applications are added.

We are not training a foundation model from zero. We are combining:

1. An already-trained, openly licensed, uncensored model.
2. A stable public identity named `Veronica`.
3. A local API and agent wrapper.
4. Reversible personality and application adapters.
5. Scoped memory and retrieval.
6. Tools and application modules.

The resulting system is the Veronica model product even when its foundation began with third-party weights.

## 2. What must remain intact

- General knowledge and instruction following.
- Reasoning and problem solving.
- Creative and long-form writing.
- Coding and debugging.
- Native structured output and function calling.
- Long-context behavior.
- Multimodal understanding when provided by the selected foundation.

No personality dataset may be merged until regression tests show these capabilities are preserved.

## 3. Stable identity versus replaceable engine

| Layer | Stable name | Replaceable implementation |
| --- | --- | --- |
| Public AI | Veronica | No |
| API model alias | `Veronica` | No |
| Agent wrapper | Veronica Core | Internals may evolve |
| Foundation weights | Hidden behind registry | Yes, after qualification |
| Personality | Veronica Persona | Prompt first, LoRA later |
| Application behavior | Application module | Yes |

Applications must call Veronica's API alias, never a hard-coded Hugging Face repository name.

## 4. Current model decision

No final foundation has been selected. Selection status is `benchmark_required`.

**Live checkpoint (2026-08-30):** Candidate A now has verified artifacts and real API/UI chat evidence. Its supervised A100 run ended with confirmed Pod termination and retained storage. The first evaluation exposed contradictory math and an unsupported code-execution claim, so it is not yet a qualified capable core. See `runs/2026-08-30-supervised-first-chat/decision.md` and `manual-review.md`.

### Candidate A - available first-run candidate

- Repository: `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated`
- Reason: owner reported a prior Hugging Face bucket copy; the pinned candidate has now been downloaded and hash-verified on the existing RunPod volume. The first supervised A100 run used a verified $1.59/hour rate; final billing is separate from measured inference performance.
- Known concern: this Instruct variant is non-thinking-only according to its official base card. It can perform reasoning tasks, but a prompt preset cannot turn it into a native thinking-mode model. It is not the automatic final choice for the requested core.

### Candidate B - capability challenger

- Repository: `huihui-ai/Huihui-Qwen3.8-27B-abliterated`
- Reason: newer dense multimodal reasoning model with image/video understanding and stronger agent-oriented base capabilities.
- Known concern: newer community ablation and denser inference cost require careful validation.

### Control models

The official unmodified base corresponding to each candidate is a control, not the uncensored production choice. It reveals whether ablation or quantization damaged capability.

The selection suite must test quality, sarcasm and implied meaning, personality adaptability, writing, coding, reasoning, long context, structured JSON, tool calling, lawful adult prompt following, latency, and VRAM.

## 5. First deliverable

The first deliverable is deliberately small:

1. Verify an uncensored candidate's provenance and file integrity, then start it behind an OpenAI-compatible server.
2. Start the local Veronica wrapper.
3. Open Veronica's chat page.
4. Hold a multi-turn text conversation.
5. Change among Chat, Deep Reasoning, Creative, and Coding modes.
6. Record the exact model revision, runtime, GPU, and acceptance results.

Tool execution, long-term memory, fine-tuning, media generation, billing, and public hosting remain off until this works.

First chat does not require the entire future roadmap to be complete. Full model qualification is required before final selection, fine-tuning, and capability claims. See `docs/EVIDENCE.md` for the technical basis and known limitations.

## 6. Target capability modules

1. **General Assistant:** conversation, questions, planning, and summaries.
2. **Deep Reasoner:** difficult research, architecture, analysis, and decisions.
3. **Generative Writer:** stories, dialogue, scripts, rewriting, and voice control.
4. **Tool-Using Agent:** validated function calls, file work, APIs, and workflows.
5. **Studio Director:** natural-language control of image and video workers.
6. **Application Builder:** creates and validates new application modules.
7. **Scoped Memory:** session, user, project, and application memory boundaries.

The first four behaviors should originate in the foundation model. The wrapper exposes and tests them; it does not pretend to create missing intelligence.

## 7. Runtime architecture

```text
Browser / Client
       |
       v
Veronica API and Agent Wrapper
  - public alias
  - persona and modes
  - request validation
  - future tools and memory
       |
       v
OpenAI-compatible Model Server
  - vLLM or qualified equivalent
       |
       v
Selected Uncensored Foundation
       |
       +--> Later: reversible LoRA adapter
```

The image/video stack is a future tool target. It is not the text model itself.

## 8. Wrapper contract

Initial endpoints:

- `GET /` - local chat interface.
- `GET /api/health` - wrapper and provider state.
- `GET /api/capabilities` - implemented versus planned capabilities.
- `GET /v1/models` - stable Veronica alias.
- `POST /v1/chat/completions` - OpenAI-compatible chat. `stream=false` returns a full completion. `stream=true` forwards upstream SSE when the provider supports it, and returns an honest 501/503 if it cannot. The wrapper rewrites the streamed `model` field to the public `Veronica` alias.

The request may include `veronica_mode` with `chat`, `deep-reasoning`, `creative`, or `coding`. The wrapper removes this extension before forwarding the request.

These initial modes are prompt presets, not proof of native reasoning capability and not yet model-specific reasoning switches. Native controls are enabled only after the chosen server/model combination is qualified.

An Ollama `Modelfile` is one engine-specific way to define an alias and system prompt; it is not a newly trained foundation. This project uses the same identity-wrapper concept through a provider-neutral API so it can run on vLLM/RunPod without being tied to Ollama.

## 9. Persona strategy

Phase 1 uses a concise system persona. It defines identity and conversational character without teaching facts or replacing reasoning.

Phase 2 collects owner-approved examples covering tone, sarcasm, initiative, honesty, disagreement, creativity, and boundaries.

Phase 3 trains a small reversible adapter. The adapter advances only when it matches the baseline on capability regression tests.

## 10. Evidence and change control

Every model, quantization, persona, adapter, or serving change must create a dated run record containing:

- Input model repository and immutable revision.
- License and provenance check.
- Artifact hashes or storage manifest.
- Runtime image and package versions.
- GPU and memory configuration.
- Start command and environment variable names, excluding secrets.
- Evaluation outputs and summary.
- Decision: rejected, hold, qualified, selected, or superseded.

If evidence conflicts with this document, preserve the evidence first, then update this document and the TODO together.

## 11. Definition of completed Veronica Core

Veronica Core is complete only when:

- A selected uncensored foundation passes the complete evaluation suite.
- The API alias remains stable across model-server changes.
- Text chat, reasoning, writing, coding, and tool calls pass acceptance thresholds.
- Persona adaptation passes regression tests.
- Scoped memory can be enabled or disabled per application.
- At least one external application integrates without hard-coding the foundation model.
- Local and RunPod deployments are reproducible.
- Serverless deployment scales to zero and enforces authentication, quota, and cost controls.
- Documentation and a recovery run prove another session can resume the system.
