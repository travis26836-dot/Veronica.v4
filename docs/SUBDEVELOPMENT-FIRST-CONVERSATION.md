# First Conversation sub-development

**Goal:** a first real, multi-turn chat with Veronica.v4 through the `Veronica` alias. This focused execution list does not replace `TODO.md`.

## File closeout rule

- Completed or superseded TODO snapshots go in `docs/COMPLETED/` with their replacement and proof link.
- Obsolete plans or unused non-source material go in `ARCHIVE/` with a short reason. Never archive active source, configuration, tests, or run evidence merely because a task is complete.
- Execution evidence remains in `runs/<date>-<purpose>/`; no item is checked without its evidence path.

## Segment 1 — chat surface

- [x] Port the approved v2 visual shell: cosmic background, Veronica mark, typefaces, three-column layout, and responsive behavior. Proof: `runs/2026-08-30-ui-layout-port/decision.md`.
- [x] Replace legacy API assumptions with the v4 chat and health contract only. Proof: `runs/2026-08-30-ui-layout-port/decision.md`.
- [x] Keep real-time UI status honest: live health polling, actual request activity, clock, and no simulated tool/model events. Proof: `runs/2026-08-30-ui-layout-port/decision.md`.
- [x] Verify JavaScript syntax, static assets, wrapper tests, and desktop/narrow viewport behavior. Proof: `runs/2026-08-30-ui-layout-port/decision.md`.

**Checkpoint 1:** `runs/2026-08-30-ui-layout-port/decision.md` records the port scope, tests, and v2 donor location.

## Segment 2 — model artifact gate

- [x] Save full card/license snapshots for Candidate A and its official control at pinned revisions. Proof: `runs/2026-08-30-reusable-runpod-core/provenance/`. Remote integrity is now verified in the supervised run's actual manifest.
- [x] Inspect existing Candidate A files on the persistent volume; reuse a complete matching copy or resume/download the pinned revision during an approved, bounded setup run. Proof: `runs/2026-08-30-supervised-first-chat/storage-preflight.json` and `validated-model-manifest.json`.
- [x] Keep incomplete transfer files under `.uploading`; promote only after manifest validation. Proof: `runs/2026-08-30-supervised-first-chat/validated-model-manifest.json` and executed bootstrap snapshot.
- [ ] Configure a dedicated read-only model mount. The validated directory is recorded in `runs/2026-08-30-supervised-first-chat/validated-model-manifest.json`; this run served unchanged weights from the writable persistent volume.

**Checkpoint 2:** a dated storage-manifest run proves the complete candidate is intact. Do not assume the copy is already on the volume. A bounded setup Pod may precede this checkpoint, but serving must follow validated hashes.

## Segment 3 — bounded model server

**Run closed:** the owner accepted supervision and explicit shutdown. One $1.59/hour Pod served real responses and was terminated at 23:11:49 UTC. Volume retained. See `runs/2026-08-30-supervised-first-chat/decision.md`. The local backup was not a platform timer; future runs need fresh authorization.

- [x] Pin a compatible PyTorch container digest and vLLM package/runtime versions. Proof: the supervised run's `profile.json` and `runtime-packages.txt`.
- [x] Approve a maximum hourly price and UTC termination deadline for one supervised development run. Proof: `runs/2026-08-30-supervised-first-chat/approval.json` and `supervised-state.json`; no platform timer claim.
- [x] Smoke-test the reusable profile/bootstrap with an 80 GB GPU, private upstream key, approved supervision, and confirmed explicit termination. Proof: the supervised run's `decision.md`; no platform timer or production qualification claim.
- [x] Create one Pod, then verify `/v1/models` through the SSH tunnel before treating it as ready. Proof: the supervised run's `provider-smoke.json` and actual model manifest.

**Checkpoint 3:** `First Pulse` evidence includes Pod id, model revision, image digest, GPU, start command, endpoint check, and shutdown plan.

## Segment 4 — Veronica speaks

- [x] Point the local wrapper at the verified Pod endpoint without changing its public `Veronica` alias. Proof: `runs/2026-08-30-supervised-first-chat/decision.md`.
- [x] Verify `/api/health`, `/v1/models`, and one non-streaming completion from Windows localhost. Proof: that run's health and wrapper response records.
- [x] Run and save a multi-turn Chat conversation plus Creative, Coding, and Deep Reasoning smoke tasks. Proof: that run's API/UI records. **The reasoning response was inconsistent; running the test is not a quality pass.**
- [x] Capture API output, screenshots, timings, configuration fingerprint, and clean Pod termination. Proof: that run's evidence and `termination.json`.

**Checkpoint 4:** `Veronica Speaks` is earned only after real response evidence exists. Model selection and tuning remain pending.

Achieved 2026-08-30 for real chat transport/UI. Next: unambiguous recall tests, reasoning consistency and unsupported-action claims; see the run's `manual-review.md`. UI polish should update the historical welcome notice and scroll the latest reply into view. Full model qualification is not passed.

## Segment 5 — studio boundary, after core chat

- [ ] Inspect the shared volume and reserve separate `veronica-core/` and `studio/` paths.

Inspection is complete: existing Studio remains under `/workspace/runpod-slim/ComfyUI` and staging paths; text artifacts use `/workspace/veronica-core`. Do not move Studio files simply to rename its namespace. Dedicated Studio reconfiguration remains pending.
- [ ] Reconfigure the old ComfyUI work for a dedicated Studio worker; do not fold it into the core model Pod.
- [ ] Integrate it later as a permissioned Studio Director tool with returned job evidence.

**Checkpoint 5:** the Studio is optional and core text chat remains independently usable.
