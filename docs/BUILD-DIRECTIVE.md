# Veronica Build Directive

Status: active architecture directive. `docs/SOURCE-OF-TRUTH.md` defines the
product; `TODO.md` is the execution checklist. This document fixes the operating
boundary between Veronica Core and image/video generation so future work and Pod
starts do not drift.

## Product decision

Veronica is one modular AI product. Its text/reasoning Core is the control plane:
it converses, plans, selects permitted capabilities, requests work, receives real
results, and explains failures. Image and video generation are Studio capabilities
that Veronica invokes through an explicit worker contract.

The Core does not claim an image or video was generated unless the Studio worker
returns a completed job record and output reference.

## Runtime profiles

| Requested work | Runtime profile | Required result |
| --- | --- | --- |
| Chat, reasoning, coding, Core evaluation | **Core**: vLLM text-model Pod and local Veronica wrapper | Actual model completion through the `Veronica` alias |
| Image or video workflow work | **Studio**: ComfyUI worker Pod/template | Actual ComfyUI job, progress, output, and failure records |
| End-to-end orchestration | **Integrated**: separately verified Core and Studio workers | Core submits a permissioned Studio job and shows its returned result |

`Start Veronica` means the Core profile unless the owner explicitly asks for
Studio or Integrated work. `Start Veronica Studio` will be a separate, bounded
launcher once its profile and evidence contract are implemented. Do not select a
ComfyUI template for ordinary text Core evaluation. Do not load the text model
and every Studio model into one development Pod by default.

## Required boundaries

1. Keep text-model artifacts under `/workspace/veronica-core/`; preserve existing
   ComfyUI work under its Studio paths.
2. Treat ComfyUI as a worker, never as Veronica's reasoning engine or API alias.
3. Give each worker its own pinned template/image, model manifest, GPU selection,
   budget, start record, shutdown receipt, and run evidence.
4. Studio requests require a typed job schema: prompt/workflow reference, input
   references, allowed parameters, job ID, progress events, output references,
   error state, and originating Core request ID.
5. Tool permissions, confirmation for consequential actions, timeouts, budgets,
   cancellation, and audit records are enforced by Core before a Studio job runs.
6. A failed or unavailable Studio worker returns an honest failure to Core; it
   never becomes fabricated text claiming completion.

## Build order

1. Stabilize and qualify the text Core without changing foundation weights.
2. Implement the native tool registry and the non-executing Studio job schema.
3. Create a dedicated ComfyUI Studio profile and prove one bounded image job with
   full evidence and clean shutdown.
4. Connect Core to Studio with permissions, real progress, cancellation, outputs,
   and failure behavior.
5. Add video workflows using the same contract rather than a parallel integration.
6. Run an Integrated acceptance test while retaining the ability to start Core or
   Studio independently.

## Acceptance checkpoints

- **Core Ready:** text Core has real, evidenced model behavior and remains usable
  when Studio is absent.
- **Studio Connected:** a ComfyUI job can be submitted, observed, cancelled, and
  returned through the typed contract without invented completion claims.
- **Integrated Veronica:** Veronica can decide when Studio is appropriate, obtain
  permission, use real worker results, and explain a worker failure accurately.

This directive does not mark any TODO item complete, start a Pod, approve GPU
spending, or authorize media generation. It records the architecture and order
for future bounded work.
