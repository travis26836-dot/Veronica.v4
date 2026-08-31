# Copilot handoff — Veronica.v4

**Runtime update:** the RunPod sections below are historical and superseded by `docs/STARTING-PROCEDURE.md` and `runs/2026-08-30-reusable-runpod-core/decision.md`. The old auto-termination flags never worked; do not use the old launch configuration. Current reusable configuration: `config/runpod-core.json`.

**Restart boundary:** 2026-08-30 after verified UI port, before Candidate A artifact validation or any paid RunPod operation.

## Read first

1. `AGENTS.md`
2. `docs/SOURCE-OF-TRUTH.md`
3. `TODO.md`
4. `docs/SUBDEVELOPMENT-FIRST-CONVERSATION.md`
5. `runs/2026-08-30-candidate-provenance/decision.md`
6. `runs/2026-08-30-ui-layout-port/decision.md`
7. `docs/CODEX-CREDIT-CHECKPOINT.md`

## Current verified state

- Public model alias is always `Veronica`; model selection remains `benchmark_required`.
- Candidate A is the provisional first-chat target: `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` at `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`.
- Candidate B remains the capability challenger; do not call either model final or natively reasoning-qualified.
- The FastAPI wrapper provides `/`, `/api/health`, `/api/capabilities`, `/v1/models`, and non-streaming `/v1/chat/completions` on port 8010.
- The v2 visual UI was ported to `src/veronica_core/static/`: cosmic background, logo, fonts, responsive layout, real health polling, and real request activity. No legacy Studio/tool/workstation backend was copied.
- `scripts/build.ps1` passed: 13 tests, one known Starlette TestClient deprecation warning, and a wheel with SHA-256 `2E249DBFBDAF94A3F7754B974DF8925310E604ECB6575FF2048655D92E9D5E33`.
- The repository is on `main` and all current project content is uncommitted. Preserve it; do not use reset, clean, checkout-discard, or broad deletion.

## Infrastructure facts and limits

- A 300-GB RunPod volume exists: `v53gj9flzs` (`Veronica.v4_volume`) in `EUR-IS-1`.
- Do not assume Candidate A is present on that volume. Its copied location and file hashes are unverified.
- `config/runpod.env.example` and `scripts/start-runpod-model-server.sh` are guarded launch scaffolding, not launch authorization.
- Do not create a paid Pod without an explicit current maximum hourly price and UTC termination deadline from the owner.
- Candidate A is approximately 61 GB of LFS artifacts; an 80-GB-class GPU is the minimum investigation tier, not a proven serving configuration.

## Directed restart workflow

### Checkpoint A — integrity only, no paid GPU

Save Candidate A and control model card/license snapshots at pinned revisions. Locate the owner’s copied artifact storage without duplicating downloads. Record full filenames, byte counts, SHA-256 values, storage URI/path, and `.uploading` status. If the location cannot be safely discovered without paid compute, stop and ask the owner for the storage location rather than creating a Pod.

**Proof:** a new dated `runs/<date>-candidate-artifact-integrity/` record. Only then check the matching TODO items.

### Checkpoint B — approved, bounded first pulse

Ask for explicit cost ceiling and termination deadline if they are not present. Pin a vLLM image digest and select a compatible 80-GB-class GPU in the volume's data center. Configure the guarded `.env.runpod` locally without committing secrets. Start one auto-terminating Pod, verify `/v1/models` from outside the Pod, then save the measured runtime evidence.

**Proof:** `First Pulse` run record. A scheduled/running Pod alone is not proof.

### Checkpoint C — first Veronica conversation

Point the local wrapper at the verified endpoint, preserve the `Veronica` alias, verify `/api/health` and `/v1/models`, then capture one real multi-turn conversation and the three mode smoke tasks. Terminate the Pod and record evidence immediately after the bounded run.

**Proof:** `Veronica Speaks` run record. Do not claim model qualification or personality tuning.

## File discipline

- Active source: `src/`; tests: `tests/`; docs: `docs/`; evidence: `runs/`.
- Move completed/superseded TODO snapshots to `docs/COMPLETED/`; obsolete non-source material to `ARCHIVE/`. Keep active files and run evidence in place.
- Donors stay read-only. The permitted v2 UI port is already complete; do not import its old image/tool APIs into the v4 core.
