# Decision: 2026-09-06 START attempt — two real bugs fixed, live creation hit a stock race

## Request

Owner: "Let's attempt to start Veronica again — if it fails this time, we will need to fix the runpod
skill and starting procedure." Duration confirmed via `ask_user`: 1 hour (default).

## What happened

1. **First attempt** (`runs/2026-09-06T064841Z-start-veronica/`): `scripts/start-veronica.ps1` failed
   immediately with "The local wrapper environment is missing" — `.venv` had never been built. Ran
   `scripts/build.ps1` (140 tests passed, package built). Retried; failed with "Run START with
   PowerShell 7 (pwsh)" because the retry used `powershell.exe` (5.1) instead of `pwsh` (7). Retried
   with `pwsh`; failed with a `FileNotFoundError` reading the approval file.
2. **Root cause of the `FileNotFoundError`**: `scripts/start-veronica.ps1` used
   `(Resolve-Path -LiteralPath $ApprovalFile).Path`. This project's working directory is a
   `\\wsl.localhost\Ubuntu\...` UNC path. On a UNC path, PowerShell's `PathInfo.Path` returns a
   *provider-qualified* string (`Microsoft.PowerShell.Core\FileSystem::\\wsl.localhost\...`), which is
   not a valid filesystem path and breaks every downstream Python/WSL call that receives it. **Fix**:
   use `.ProviderPath` instead, which returns the plain UNC path on both UNC and ordinary local
   working directories. Verified by reproducing the bug directly in PowerShell before and after the fix.
3. After the path fix, preflight ran a real live check against RunPod and correctly reported the
   primary A100-SXM4-80GB at **zero stock** in `EUR-IS-1` (the model volume's data center) and safely
   refused to create anything (`safeToCreate: false`, no Pod, no charge). Confirmed via
   `runs/2026-09-06T064841Z-start-veronica/preflight.json` and `startup-cancelled.json`.
4. Owner asked for a **fallback plan**: since the persistent model volume is region-locked to
   `EUR-IS-1`, the fix cannot be "try another data center" — it must be "try another GPU class in the
   same data center for the same single Pod." Live inventory in `EUR-IS-1` showed no Secure Cloud GPU
   matches the A100's ~80 GB VRAM class within the $1.75/hour ceiling; the closest match (RTX PRO 6000
   Blackwell, 96 GB) only fits the ceiling on **Community Cloud** ($1.69/hour), a different reliability
   tier (host-preemptible, no Secure Cloud guarantees). Owner explicitly accepted this trade-off.
5. **Fix**: added `pod.gpuFallbacks` to `config/runpod-core.json` (RTX PRO 6000 Blackwell Server, then
   Workstation Edition, both Community Cloud, ≤$1.69/hour each). `scripts/runpod_core.py`'s
   `preflight()` now checks the primary GPU first, then each fallback in order, and selects the first
   with live stock within its own price cap; the result carries `gpuTypeId`, `cloudType`,
   `usedFallbackGpu`, and a `reliabilityNote`. `scripts/supervised_runpod.py` creates the Pod using
   whichever GPU/cloud type preflight actually selected, and prints/records the reliability warning
   when a fallback is used. Verified with a simulated fallback scenario (A100 forced to `none` stock)
   and with two new regression tests in `tests/test_runpod_safety.py`
   (`test_preflight_falls_back_to_approved_gpu_when_primary_has_no_stock`,
   `test_preflight_blocks_when_primary_and_all_fallbacks_have_no_stock`). Full existing suite
   (`tests/test_supervised_start.py`, `tests/test_runpod_safety.py`, `tests/test_runpod_core.py`)
   still passes (146 passed, 1 skipped after the additions).
6. **Live retry** (this run, `runs/2026-09-06T071247Z-start-veronica/`): preflight correctly selected
   the fallback (`NVIDIA RTX PRO 6000 Blackwell Server Edition`, Community Cloud,
   `usedFallbackGpu: true`, reliability note recorded — see `preflight.json`). Actual `pod create` call
   failed with a genuine live RunPod race: `graphql error: There are no longer any instances available
   with the requested specifications. Please refresh and try again.` Stock changed between the
   preflight check and the creation call seconds later — a real external timing condition, not a code
   defect. `supervised-state.json` recorded `podId: null`, `creationAttempted: true`.
7. **Third bug found and fixed while closing out this run**: `supervised_runpod.py`'s `terminate()`
   treated *any* creation failure without a recovered `podId` as "unresolved," forcing indefinite
   supervision — even though the code had already retried `owned_pods()` (a live inventory check by
   the run's unique Pod name) three times and found nothing, and even though the CLI's error was a
   synchronous, definitive rejection (not an ambiguous client-side timeout where the API might have
   accepted the request server-side). **Fix**: distinguish `subprocess.TimeoutExpired` (genuinely
   ambiguous — keep the conservative "unresolved" behavior) from any other exception raised by a
   completed CLI call (a definitive API response). When the retries still find nothing and the
   failure was definitive, record `creationDefinitivelyRejected: true` on the state file;
   `terminate()` now accepts this as confirmed absence (after one more live check) instead of blocking
   forever. Verified with two new regression tests
   (`test_ambiguous_creation_timeout_without_pod_id_stays_unresolved`,
   `test_definitively_rejected_creation_confirms_absence`) and by applying the fix live to this exact
   run: `terminate` printed `Confirmed Pod veronica-core-20260906-072232-b01ba084 absent; persistent
   volume retained.`, wrote `termination.json` with `confirmedAbsent: true`, the local watchdog
   (WSL pid 42743) exited on its own, and the keep-awake helper released automatically.

## Final state

- **No Pod was ever created.** No charges incurred. Confirmed via `termination.json` and two
  independent live `runpodctl pod list --all` checks returning `[]`.
- The persistent model volume `v53gj9flzs` (`EUR-IS-1`) is untouched.
- All local helper processes (watchdog, keep-awake) exited cleanly; nothing is left running.
- Three real defects fixed and regression-tested:
  1. UNC-path `Resolve-Path.Path` vs `.ProviderPath` bug in `start-veronica.ps1`.
  2. No GPU fallback when the primary A100 has no live stock in the volume's data center.
  3. `terminate()` could not resolve a definitively-rejected creation attempt, leaving a run stuck in
     "unresolved" supervision indefinitely even after live checks proved absence.

## Next step

The starting procedure itself is now fixed and verified end-to-end (path resolution, PowerShell 7
requirement, GPU fallback selection and Pod creation, and termination/cleanup on a genuine creation
failure). The remaining blocker for an actual successful chat session is **live RunPod capacity**,
which fluctuates independent of this code. A fresh actual "Start Veronica" request is required for
any further attempt; this decision record and its approval are not reusable.
