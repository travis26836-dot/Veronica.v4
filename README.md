# Veronica.v4

Veronica.v4 is a capable, locally controlled AI built by wrapping and selectively adapting an already-trained open model. The first deliverable is dependable text chat. Reasoning, creative writing, coding, tool calling, scoped memory, and media direction expand from that same core without replacing it.

This repository is the canonical source of truth for the product, wrapper, tests, model-selection evidence, and build history.

## Project contract

**Objective:** Deliver one impressive general-purpose AI named Veronica that retains the base model's capabilities and can be extended into many applications.

**Owner:** Raine makes product, personality, model, cost, and release decisions.

**Operating mode:** Local development and validation; short-lived RunPod GPU workloads; eventual Serverless scale-to-zero production.

**Canonical home:** `C:\Users\raine\DEVELOPMENT\Projects\Veronica.v4`

**Source of truth:** [`docs/SOURCE-OF-TRUTH.md`](docs/SOURCE-OF-TRUTH.md)

**Execution checklist:** [`TODO.md`](TODO.md)

**Build pipeline:** [`docs/BUILD-PIPELINE.md`](docs/BUILD-PIPELINE.md)

**Response evaluations and improvement:** [`docs/evals/README.md`](docs/evals/README.md) — 60 original cases, saved-transcript review, scoring, dataset safeguards, and the reusable `veronica-evals` skill. Prepared and tested offline; live model qualification and training remain pending.

**RunPod-backed start:** [`docs/STARTING-PROCEDURE.md`](docs/STARTING-PROCEDURE.md)

Say **"Start Veronica"** in Codex/Copilot. The agent asks **"How long would you like the pod to run? Default: 1 hour."** unless your request already supplies a duration. Saved settings: one A100 80 GB on the existing model volume, **at most $1.75/hour**, with supervised shutdown from this awake/connected computer. An actual start request authorizes one run; configuration and previews create nothing. Offline preview: `./scripts/start-veronica.ps1 -PlanOnly`. Say **"Stop Veronica"** to terminate the Pod while retaining the model volume. See the starting procedure for the local-watchdog limitation.

**First real conversation:** achieved 2026-08-30 through the API and restored UI. The test Pod is terminated and persistent storage retained. This is a working chat pipeline, not final model qualification; see the [run decision and quality findings](runs/2026-08-30-supervised-first-chat/decision.md).

**Reusable RunPod profile:** [`config/runpod-core.json`](config/runpod-core.json), operated through the [`veronica-runpod-core` skill](.agents/skills/veronica-runpod-core/SKILL.md). Paid startup requires fresh authorization. A supervised controller is available, but RunPod's old timer flags were ineffective and its local backup is not a platform guarantee. Latest checkpoint: [`supervised first-chat run`](runs/2026-08-30-supervised-first-chat/decision.md).

**First-conversation checkpoints:** [`docs/SUBDEVELOPMENT-FIRST-CONVERSATION.md`](docs/SUBDEVELOPMENT-FIRST-CONVERSATION.md)

**Copilot restart package:** automatically archived at Copilot session start in [`docs/COMPLETED/copilot-handoff-2026-08-30/`](docs/COMPLETED/copilot-handoff-2026-08-30/)

## Non-negotiable principles

1. Capability comes first. Do not fine-tune until the original model has a recorded baseline.
2. `Veronica` is the stable public alias; the underlying model may change after evidence-backed evaluation.
3. Personality belongs in the wrapper first and in a reversible adapter later.
4. Application knowledge belongs in scoped retrieval or an application adapter, not indiscriminately in the core.
5. No milestone is complete without reproducible evidence.
6. No paid GPU remains running without an explicit development deadline.
7. Source code stays separate from research, logs, generated media, and scratch material.

## Current verified state

- The canonical repository and research artifacts exist.
- A model-agnostic Veronica wrapper and basic chat interface are scaffolded.
- The wrapper can target an OpenAI-compatible local or RunPod model server.
- Local tests use a mock provider and do not consume GPU credits.
- No Veronica.v4 base model has passed the qualification suite yet.
- No Veronica.v4 personality fine-tune has been performed yet.
- No production deployment exists yet.

## CREATED workflow

### C - Capture

- Scope: capable text/chat core, persona wrapper, reasoning modes, coding, native tool calls, scoped memory, module expansion, and production packaging.
- Exclusions for the first milestone: billing, public accounts, autonomous publishing, image/video generation, and irreversible training.
- Inputs: approved model repositories, persona decisions, evaluation prompts, and application requirements.
- Success outcome: Veronica answers through its own UI and API using a qualified uncensored base model while preserving reasoning, writing, coding, and tool behavior.

### R - Research

- Prefer official base-model cards, licenses, serving-engine documentation, pinned revisions, and reproducible evaluations.
- Treat community abliterated derivatives as candidates until integrity, license inheritance, and capability retention are verified.
- Record GPU memory, latency, output quality, function-calling reliability, and refusal behavior before selection.

### E - Establish

- Stages: verify candidate integrity -> serve model -> first chat -> capability baseline -> shape persona -> add modules -> package -> deploy.
- Agents: Core Builder, Capability Evaluator, and Release Keeper.
- Handoffs: every stage writes configuration, test results, and a durable status into a dated run folder.

### A - Assemble

- Runtime: Python 3.12, FastAPI, HTTPX, pytest, and an OpenAI-compatible upstream such as vLLM.
- Configuration: environment variables plus versioned, secret-free files in `config/`.
- Validation: schema checks, API tests, capability evaluations, license records, and deployment preflight.

### T - Test

- Run the wrapper locally with a mock provider before renting a GPU.
- Benchmark the untouched candidate before changing weights.
- Test interruption recovery, malformed output, provider failure, long context, and tool-call structure.

### E - Execute

- Development Pods require a termination deadline.
- Fine-tuning requires an approved dataset manifest and a preserved baseline.
- Public deployment requires authentication, quotas, observability, and cost controls.

### D - Document

- Preserve each run under `runs/<YYYY-MM-DD>-<purpose>/`.
- Record model revision, quantization, GPU, server command, configuration, tests, failures, and final disposition.
- Update the source of truth only after evidence changes the project state.

## Quick start: wrapper-only development

```powershell
uv sync --python 3.12
Copy-Item .env.example .env
./scripts/start-wrapper.ps1
```

Open `http://127.0.0.1:8010`. The wrapper will report that the model provider is unavailable until an OpenAI-compatible server is configured and running.

Run `./scripts/verify-local.ps1` for local tests, or `./scripts/build.ps1` to test and build the wrapper package. These commands do not rent GPUs or download model weights.

## Folder guide

- `src/veronica_core/`: application source.
- `tests/`: local, provider-mocked verification.
- `docs/`: source of truth, architecture, and build pipeline.
- `agents/`: durable role and handoff instructions.
- `config/`: model registry, workflow status, JSON schemas, and secret-free controls.
- `data/`: intake, normalized training/evaluation data, and approved assets.
- `runs/`: immutable evidence from each execution.
- `scripts/`: repeatable setup, validation, and start commands.
- `NON-SOURCE CODE/`: research, designs, references, and other non-runtime material.

## Donor projects

Donors remain read-only until a component is deliberately ported and tested:

- `/home/dubs/code/veronica-ai-v2/veronica-home`
- `/home/dubs/code/NoirWorks Adult Studio/ComfyUI-Pipeline-Foundation`
