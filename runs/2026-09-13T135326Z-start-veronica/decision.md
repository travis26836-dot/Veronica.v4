# 2026-09-13T135326Z-start-veronica

**Decision:** Cold-start success on revised launcher. Verified early UI readiness via `startup-ui-ready.json`, model load + full hash validation on persistent volume, wrapper and direct provider smoke tests (multi-turn context recall of name + "copper lantern", creative writing, coding with self-verified function, reasoning with self-correction from 3/5 to 3/10), streaming support in backend, clean supervised termination with volume retained and Pod confirmed absent. Single Candidate A (huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated @ e2f73ec7...) baseline advanced; foundation qualification remains pending per smoke notes. No new compute beyond this bounded supervised run.

## Evidence in this run folder
- `preflight.json`: A100-SXM4-80GB SECURE @ $1.59/hr (no fallback used), 60min, safeToCreate, volume v53gj9flzs EUR-IS-1.
- `profile.json`: pinned model/rev, vLLM 0.11.0, bf16, max_model_len=8192, gpuMemoryUtilization=0.92, server on 127.0.0.1:8000.
- `validated-model-manifest.json` + `volume-inspection.txt`: complete file manifest with byte sizes and sha256 for all 13 safetensors shards + tokenizer/config/etc. (~61 GB total weights).
- `bootstrap-log.txt`: "VERIFIED" every file (gitattributes through vocab.json), vLLM startup, Qwen3MoeForCausalLM resolved, EngineCore init, model loaded from persistent /workspace/veronica-core/models/... .
- `startup-ui-ready.json` (13:54 UTC): uiReady=true, chatUrl http://127.0.0.1:8010, inferenceVerified=false (checks pending) — UI before full readiness.
- `startup-ready.json` (14:05): ready=true, podId=jmvzzr6qygy90d, wrapper+server up.
- `wrapper-smoke.json` + `provider-smoke.json`: 5 tests each (intro, context, creative scene, coding is_even+asserts, reasoning prob). All basicCheckPassed + basicSmokePassed=true. Wrapper uses injected Veronica persona ("sharp... with TRAVIS"); direct provider uses base. Responses identify as Veronica, recall phrase, produce code/creative/reasoning. Automated checks note: "semantic correctness and action-truthfulness require manual review"; "capabilityQualification": "pending".
- `termination.json` (14:53): confirmedAbsent=true, networkVolumeRetained=true.
- `tunnel.json`, `server-command.json`, `runtime-packages.txt`, logs (wrapper.stdout etc.), `keep-awake-state.json`, `watchdog-*`.
- `configuration-fingerprint.json`, `expected-model-manifest.json`, `provenance/`, `supervised-state.json`.

## Verified per TODO / SOURCE-OF-TRUTH
- Revised launcher opens 8010 UI via startup-ui-ready.json *before* waiting for full model readiness/tests.
- Model server recreatable from records; clean shutdown no data loss.
- Multi-turn chat, creative smoke, coding smoke (model-produced + claimed verification), context retention, Veronica identity in responses.
- Complete file manifest + transfer validation (hashes + VERIFIED logs) recorded.
- Pod terminated post-evidence; volume retained.
- Backend: non-stream + SSE streaming support, persona/mode injection, alias rewrite, honest health.
- Local wrapper + static UI (mode select, chat, health polling, activity) functional via mocks and prior live.

## Limitations observed (consistent with prior)
- Reasoning: self-corrected math (3/5 → 3/10) in this run — progress but full T2 needed.
- No native tool calls, long-context stress, JSON schema, or full eval pack executed.
- UI: basic (textContent, no MD/persistence/retry/stop in this smoke; JS implements core send/fetch).
- Single model only (Candidate B not wired).
- No live owner multi-turn beyond smoke; qualification pending.

## Next legitimate actions
1. Write this decision.md (done here); reconcile TODO.md with new proofs.
2. Run full local test suite (mocks cover core paths; deprecation warning noted).
3. Owner review of smoke transcripts for semantic/action-truth issues.
4. Bounded T2 eval pack execution on fresh authorized Pod (or offline extension).
5. Stabilize before wiring Candidate B or expanding.
6. If core holds, implement deferred A1 UI (persistence, MD, controls) and E3 tools.

**Gate progress:** Advances A2 (launcher/UI/terminate), E1 (smokes + shutdown), R (manifest/validate). E1 "Veronica Speaks" closer but full capable-core acceptance requires T2 pass. No claims of final qualification.

**Owner acknowledgment:** Latest cold-start + evidence verified. Proceed with documentation, tests, and next bounded eval. Single-model reality per 2026-09-09 decision maintained.

Run dir created by immutable initializer; this decision replaces stub. All artifacts preserved.
