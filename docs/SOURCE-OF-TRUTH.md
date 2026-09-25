# Veronica Core — Source of Truth

**Document status:** canonical
**Active identity decision:** [2026-09-25 installed-foundation identity](../runs/2026-09-25-installed-foundation-identity/decision.md)

## What we are building

Veronica is one general-purpose AI product with a modular wrapper. It must chat naturally, reason, write, code, and use native tools before specialized applications are added.

| Layer | Active identity | Rule |
| --- | --- | --- |
| Product | Veronica | Stable product name |
| Public API/model alias | `Veronica.v.4.1-30B-A3B-BF16` | Exact stable client-facing identifier |
| Agent wrapper | Veronica Core | Internals may evolve |
| Foundation | Installed foundation baseline | Internal, provenance-controlled implementation |
| Persona | Veronica Persona | Prompt first; reversible adapter only after regression evidence |

Applications call **only** `Veronica.v.4.1-30B-A3B-BF16`; they must not hard-code an upstream repository or storage location.

## Active foundation decision

The installed foundation baseline is the only active foundation configuration. Its **qualification remains `pending`**. Historical chat/smoke evidence and verified persistent storage do not establish full capability qualification. No inference, paid GPU start, download, or weight modification occurred while the 2026-09-25 identity migration was made.

### Internal provenance

| Field | Value |
| --- | --- |
| Repository | `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` |
| Immutable revision | `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` |
| Persistent storage path | `/workspace/veronica-core/models/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated/e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` |
| Declared license | Apache-2.0 |
| Architecture | Qwen3MoeForCausalLM; 30.5B total / 3.3B active parameters |
| Weight format | BF16; no quantization |
| Weights | Unchanged |
| Active registry | `config/model-registry.json` |
| Baseline protocol | `config/foundation-baseline-qualification.json` |

Pinned card/license snapshots for this active record are preserved at `runs/2026-09-25-installed-foundation-identity/provenance/foundation-baseline/`. The records establish declared provenance, not model quality or legal finality.

## First deliverable

1. Verify the installed foundation's integrity and provenance record.
2. Serve it behind an OpenAI-compatible server only under fresh bounded authorization.
3. Start the local wrapper and open the chat page.
4. Hold a multi-turn text conversation through the exact public alias.
5. Record runtime, GPU, revision, acceptance results, and confirmed shutdown.

Native tools, memory, fine-tuning, media generation, billing, and public hosting remain off until their own gates pass.

## Runtime architecture

```text
Browser / client
       |
       v
Veronica API and agent wrapper
  - public alias: Veronica.v.4.1-30B-A3B-BF16
  - persona and prompt-preset modes
  - request validation
       |
       v
OpenAI-compatible model server
       |
       v
Installed foundation baseline (internal provenance)
       |
       +--> Later: reversible adapter
```

## Wrapper contract

- `GET /` — local chat UI.
- `GET /api/health` — honest wrapper/provider state.
- `GET /api/capabilities` — implemented versus planned capabilities.
- `GET /v1/models` — exposes only `Veronica.v.4.1-30B-A3B-BF16`.
- `POST /v1/chat/completions` — OpenAI-compatible chat. The wrapper maps all completion and streaming `model` fields to the exact public alias while forwarding to the configurable internal upstream.

`veronica_mode` accepts `chat`, `deep-reasoning`, `creative`, or `coding`. These are prompt presets, **not** proof of native reasoning controls or qualified capability.

## Qualification and change control

The frozen baseline protocol is one-model evidence collection, not a selection contest. It requires pinned provenance, direct persona-free tracks, raw outputs, automated checks, human review, executable-code evidence, long-context evidence, native-tool evidence, and a signed decision. Missing or inconclusive evidence yields **hold**, never qualification.

Every model, runtime, quantization, persona, adapter, or serving change creates a dated run record with provenance, artifact hashes, runtime/GPU configuration, command, outputs, failures, and disposition. Preserve completed historical records. A new decision supersedes obsolete active terminology rather than rewriting history.

## Completion criteria

Veronica Core is complete only when the installed foundation has complete qualification evidence, the exact public alias remains stable across server changes, chat/reasoning/writing/coding/tool acceptance thresholds pass, persona adaptation passes regression checks, and local/RunPod recovery is reproducible. Production remains a separate authentication, observability, cost-control, and release gate.
