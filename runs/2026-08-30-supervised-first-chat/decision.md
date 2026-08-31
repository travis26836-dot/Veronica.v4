# First real Veronica conversation — achieved; Pod terminated

**Decision:** the deployment/API/UI pipeline works with Candidate A. This is not final model selection or a clean capability pass. Read `manual-review.md`: inconsistent math and unsupported execution claims need qualification before tuning or expansion.

## Verified result

- Candidate: `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated`, revision `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`. Public alias remains `Veronica`; no weight tuning occurred.
- All 27 files, including 13 weight shards, passed remote size/hash verification before atomic promotion: **61,084,222,203 bytes**. Local manifest comparison found no mismatch. See `validated-model-manifest.json` and `configuration-fingerprint.json`. Pinned candidate/control cards and licenses remain in `../2026-08-30-reusable-runpod-core/provenance/`.
- Pinned PyTorch image, vLLM 0.11.0, Transformers 4.57.1, one A100-SXM4-80GB. Model load: **239.9 seconds / 56.9342 GiB**; total idle allocation after serving: 75,149 MiB including cache/runtime. Context configured to 8,192 tokens, not fully stress-tested.
- Five real direct-provider responses, five through the Windows wrapper, and a two-turn browser conversation. UI follow-up returned exactly **silver compass**. Direct model API rejects unauthenticated requests. See `provider-smoke.json`, `wrapper-smoke.json`, `windows-ready-health.json`, `ui-live-transcript.txt`, and `ui-live-recall.png`.
- Reviewed generated code actually passed its three assertions plus six integer edge cases. One isolated streaming probe measured **1.167 seconds to first content / 18.71 completion tokens per total second**. These are smoke observations, not full benchmarks or wrapper streaming support.
- **27 offline tests and wrapper build passed.** One existing Starlette TestClient deprecation warning remains. Model artifacts, runtime versions, executed bootstrap and screenshots are saved locally.

## Paid-resource closeout

The user accepted supervision and explicit shutdown instead of an unavailable RunPod platform timer. Approval was for one Pod, at most $1.60/hour, at most two hours; no replacement authorization.

Pod `r2c0u02vforaqe` cost $1.59/hour. Creation attempt began 22:48:35 UTC; it was explicitly terminated and confirmed absent at **23:11:49 UTC on 2026-08-30**, far before its 00:48:35 UTC deadline. Live inventory then returned `[]`. See `termination.json`. Approximate compute cost: **$0.62**, estimated from elapsed time and listed rate, not an invoice; storage charges are separate.

Network volume **`v53gj9flzs`, 300 GB, EUR-IS-1 remains present**. Existing Studio/staging data remained 152,739,906,680 bytes; the separate `veronica-core/` namespace uses 71,067,951,503 bytes. The watchdog, SSH tunnel and temporary Windows keep-awake process exited. The local wrapper remains running and honestly reports model offline.

## Reusable startup and next handoff

Use `docs/STARTING-PROCEDURE.md` and `.agents/skills/veronica-runpod-core/SKILL.md`. The one-shot controller requires fresh scoped approval, fixes its deadline before creation, arms a local backup, checks price/placement, and never rents a replacement automatically. The local backup is not a cloud guarantee. This run's authorization is consumed.

The current reusable profile adds an explicit 300 GB allowance check and `config/runpod-runtime-0.11.0.txt` constraints derived from this run. The original executed bootstrap/profile remain preserved here; the added replay safeguards have offline coverage, not a second paid deployment test.

Next small segment: build unambiguous capability/action-truthfulness tests, preserve the observed failures, and compare Candidate A with its official control and Candidate B only after fresh compute authorization. UI polish: update the historical welcome notice and automatic scrolling. Do not tune weights, enable tools, or expand Studio merely because first chat worked. A dedicated read-only model mount and restart qualification remain open.

Keep active source/configuration/tests and this evidence in place. Archive superseded handoff documents through the existing Copilot SessionStart hook, not by deleting evidence. All project work remains uncommitted; review before any broad commit.
