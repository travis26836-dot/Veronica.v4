# Veronica Core: selective milestones and checkpoints

Date: 2026-09-22  
Owner: Travis  
Branch: `feature/complete-todo-milestones`

This is the short execution queue for the unfinished Core. `TODO.md` remains the
authoritative checklist. A milestone is earned only when its checkpoint evidence
exists; a plan or passing local mock does not earn a product milestone.

## M1 — T2 Qualification Readiness

This is the next milestone. It is local and does not start a Pod.

Allowed scope: evaluation code/tests, frozen evaluation configuration, evaluation
documentation, and one new dated run folder. Do not change foundation weights,
start paid compute, build persona/tools/memory, or add unrelated UI work.

### Tasks

1. **Schema gate** — define required JSON schemas and semantic checks for the
   existing `SO-*` cases; add negative fixtures for missing keys, wrong types,
   extra keys, malformed/duplicate JSON, and fabricated tool results; distinguish
   `not_collected`, `incomplete`, and `collected_fail`.
2. **Actual-token context gate** — keep the nine synthetic cases outside the
   frozen 60-case suite; add the tokenizer and exact runtime metadata; prepare
   8K, 16K, and 32K probes with the needle at beginning, middle, and end; record
   truncation, latency, token usage, and retrieval accuracy. Word count is not a
   context-window result.
3. **Evaluator integrity gate** — run Docker verification and fixture tests;
   verify host-side expected answers, fail-closed isolation, cleanup, raw-result
   retention, redaction, and runtime provenance.
4. **Qualification packet** — freeze protocol hash, revisions, runtime pins,
   thresholds, cases, sampling, and required Candidate A/B/control artifacts;
   add a negative packet that the verifier rejects.

### Checkpoints

- **CP1 — Schema Proven:** schema fixtures pass, negative fixtures fail.
- **CP2 — Context Packet Ready:** actual-token generator and metadata validate;
  no model behavior claim is made.
- **CP3 — Evaluator Trusted:** Docker and redaction checks pass; no containers
  remain.
- **CP4 — T2 Ready:** frozen and negative packets validate as expected. This is
  readiness only, not `Mind Proven`.

Exit evidence: `runs/<date>-t2-readiness/decision.md`, packet/config hashes,
machine-readable reports, negative-fixture output, and local test output. Missing
inputs mean `blocked` with the exact recovery action.

## M2 — Mind Proven: live foundation qualification

Begins only after M1 CP4 and fresh owner authorization for a bounded paid run.
Run the approved Candidate A diagnostic first, review truthfulness/reasoning,
then execute the matched Candidate A/B and official-control matrix. Save raw
responses, runtime attestations, code/schema/tool/context reports, human reviews,
and owner adjudication. Record a signed selection, rejection, or hold decision.

Checkpoints: **CP5 Diagnostic Reviewed**, **CP6 Matrix Complete**, **CP7 Human
Adjudicated**, **CP8 Selection Signed**.

## M3 — Voice Recognized

After M2: approve examples, tune wrapper persona, run blind baseline comparisons,
and pass capability regression before considering a reversible adapter.
Checkpoints: **CP9 Examples Approved**, **CP10 Prompt Persona Pass**, **CP11
Regression Pass**.

## M4 — Hands Online and Memory With Boundaries

Keep native tools and scoped memory as separate packets. Each needs schemas,
permission/disable behavior, negative tests, audit evidence, and a handoff.
Checkpoints: **CP12 Tools Safe**, **CP13 Tools Truthful**, **CP14 Memory
Isolated**, **CP15 Memory Disable-Proven**.

## M5 — Facets and Controlled Release

After M4: integrate one external application through `Veronica`, then removable
Studio Director/Application Builder modules, reproducible local/Pod packaging,
and authorized Serverless staging. Checkpoints: **CP16 Alias Integration**,
**CP17 Module Removal**, **CP18 Recovery Proven**, **CP19 Staging Verified**,
**CP20 Owner Release Decision**.

## Stop rules

Do not skip a checkpoint because a later feature is attractive. Do not mark one
from a mock, port, `/v1/models`, nonempty response, or model claim. Do not reuse
old paid authorization. Preserve failed runs and record the next action in the
dated handoff.
