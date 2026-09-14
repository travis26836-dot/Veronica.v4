# Current single-model reality — documented 2026-09-09

**Decision:** Only one model (Candidate A) is currently wired into the wrapper and launcher. No Candidate B has been implemented yet. This run folder records the exact current state before proceeding with launcher verification and capability tests. This replaces the aspirational parallel-candidate language in the top-level TODO.md.

## Current wiring (verified from existing runs)
- **Model:** `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated`
- **Revision:** `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`
- **Size:** 13 weight shards, ~61 GB verified
- **Runtime:** vLLM 0.11.0 on CUDA, A100 80GB class (when available)
- **Wrapper:** Local OpenAI-compatible endpoint at 8010, `Veronica` public alias, mode-based persona injection, streaming SSE, browser UI with controls.
- **Status:** First multi-turn chat succeeded (see `../2026-08-30-supervised-first-chat/`). Pod terminated cleanly. Local wrapper reports provider status honestly when offline.

## Observed limitations (from prior manual review)
- Inconsistent math/reasoning on some probes.
- Occasional unsupported execution claims (model claims actions it did not perform).
- Context not fully stress-tested beyond 8k tokens.
- T2 full qualification (including Candidate B comparison) and native tool-calling parser not yet executed.
- Launcher UI-ready check (`startup-ui-ready.json`) still pending on fresh cold start.

**Candidate B status:** Not wired. No Hugging Face download, no RunPod profile, no launcher integration, no evaluation runs. Will be addressed only after current model is stabilized and fresh authorization is granted.

**Next actions recorded here:** 
1. Verify revised launcher opens 8010 UI before model readiness checks.
2. Build/run unambiguous capability and action-truthfulness tests.
3. Update top-level TODO.md to reflect single-model reality.

All evidence from prior runs preserved. No new compute started. This run folder itself serves as the immutable record.

**Owner acknowledgment:** Single-model baseline accepted. Proceed with stabilization before expansion.
