# Veronica RunPod starting procedure

## Say "Start Veronica"

In Codex or Copilot, **"Start Veronica"**, **"launch Veronica"**, or **"boot Veronica"** invokes the `veronica-runpod-core` skill and its checked launcher. No manual Pod deployment is needed. This is an agent command, not a microphone listener or a new PowerShell `start` alias.

Owner-configured defaults (2026-08-30):

| Setting | START behavior |
| --- | --- |
| Duration | Ask **"How long would you like the pod to run? Default: 1 hour."**; **60 minutes** for default selection, or an explicit duration up to 24 hours |
| Compute | **One NVIDIA A100-SXM4-80GB**, one Pod; no automatic substitutions or replacements |
| Hourly ceiling | **$1.75/hour maximum**; check the live offer and actual Pod rate |
| Persistent storage | Existing **300 GB volume `v53gj9flzs` in `EUR-IS-1`**, mounted at `/workspace`; preserve it on shutdown |
| Model | Pinned Candidate A from `config/runpod-core.json`, reused and hash-checked on the volume |
| Shutdown | Supervised local watchdog; keep this Windows computer awake and connected until confirmed termination |
| Chat | Local `http://127.0.0.1:8010`, reaching the Pod model privately through an SSH tunnel |

The selected window starts before Pod creation and includes provisioning, validation, and model loading. It is not a promise of one full hour of chat after loading. Persistent storage charges are separate from the GPU hourly ceiling. Sleep prevention cannot guarantee connectivity or shutdown during a computer/network failure.

An explicit current **"Start Veronica"** request under these settings supplies authorization for **that one run**. Ask the single duration question and wait for the answer unless the start request already supplies the duration. "Default", "usual", or Enter in the terminal picker means 60 minutes; silence in chat is not permission to launch. Announce the selected scope and record the request in a new one-use approval file. Do not repeat the spending-limit or supervision questions. A configuration discussion, a request for a dry run, or an old approval file does not authorize deployment. Other questions are only needed for an out-of-scope change or unclear intent. Today's configuration work did not authorize a paid deployment.

The launcher validates inputs and local ports, saves pinned provenance, arms sleep prevention and the watchdog, creates once, inspects storage, bootstraps the model, and establishes SSH forwarding. It then starts the chat wrapper and saves `startup-ui-ready.json` **before waiting for model loading or response tests**. The agent opens chat immediately at that checkpoint while the launcher continues in a monitored session. UI availability is not inference proof; the status refreshes automatically and real replies begin when the model server is ready. Direct and wrapper response checks continue in the background and produce `startup-ready.json` on success. This order follows the owner's explicit correction during `runs/2026-08-31T034034Z-start-veronica/`.

If an old local wrapper holds port 8010, identify it and restart only a confirmed wrapper belonging to this project before launching; never kill an unrelated listener. A startup failure after creation triggers owned-Pod termination and requires confirmed absence.

For an offline preview (no network calls, files created, or spending):

```powershell
.\scripts\start-veronica.ps1 -PlanOnly
.\scripts\start-veronica.ps1 -PlanOnly -DurationMinutes 120
```

After recording a real current request, the agent invokes:

```powershell
.\scripts\start-veronica.ps1 -RunDir <absolute-new-run-directory> -ApprovalFile <absolute-approval-file>
```

Pass the same `-DurationMinutes` and/or lower `-MaxHourlyUsd` override to the launcher and approval record. The launcher refuses missing, stale, used, mismatched, or over-ceiling approval. A fresh record contains:

```json
{
  "runId": "<new-run-directory-name>",
  "authorizedAtUtc": "<actual-current-authorization-time-with-timezone>",
  "maxHourlyUsd": 1.75,
  "durationMinutes": 60,
  "resourceCount": 1,
  "gpuTypeId": "NVIDIA A100-SXM4-80GB",
  "networkVolumeId": "v53gj9flzs",
  "modelRevision": "e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f",
  "shutdownMode": "supervised-with-local-backup"
}
```

Read identifiers from the current profile when creating the record. These placeholders are documentation, not an executable approval. Keep a short note of the real user request alongside it; never fabricate or refresh an old authorization timestamp.

**"Stop Veronica"** or **"Shut down Veronica"** terminates only the owned Pod, confirms it is absent, and leaves the model volume intact. The agent reports readiness in commentary so testing can proceed while it remains engaged until confirmed shutdown. The local backup requests termination at the fixed deadline; it is not a cloud guarantee. Repeating START never silently extends a run or rents a replacement.

## Current status

The phrase-triggered START launcher completed a real paid cold restart on 2026-08-31; the owner subsequently requested STOP and exact Pod absence was confirmed at 04:40:57 UTC, with persistent storage retained. See `runs/2026-08-31T034034Z-start-veronica/decision.md`. The owner then required the UI to open before tests finish; that revised order passed offline checks and awaits its next authorized cold start. That run used an early UI on port 8011 without interrupting the original launcher's port 8010 checks; its model is now offline. Historical configuration-only evidence remains in `runs/2026-08-30-start-command/decision.md`.

The reusable startup worked: Candidate A produced real API and UI responses, and the Pod was terminated at 23:11:49 UTC on 2026-08-30. The persistent volume remains. See `runs/2026-08-30-supervised-first-chat/decision.md`. Model-quality qualification is still open because the run exposed inconsistent math and unsupported execution claims.

On 2026-08-30, RunPod CLI was updated from 2.9.0 to 2.12.0. The official [removal report](https://github.com/runpod/runpodctl/pull/330) confirms that `--stop-after` and `--terminate-after` never enforced shutdown: the backend accepted them and continued billing. [Restoration PR 331](https://github.com/runpod/runpodctl/pull/331) depends on a backend fix. Old instructions claiming these flags protect a run are superseded.

The owner initially required automatic termination, then accepted **supervision and explicit shutdown** after the missing platform guarantee was explained. The historical first-chat authorization covered one Pod, at most $1.60/hour, at most two hours, and is consumed. The later START configuration above sets one hour by default, a $1.75/hour ceiling, and the accepted awake/connected supervision arrangement. New runs still need a current actual start request; configuration alone never creates a Pod.

## Reusable configuration

- `config/runpod-core.json`: pinned candidate/control revisions, image digest, GPU, existing network volume, runtime, and termination guard. No keys or spending authorization.
- `scripts/start-veronica.ps1`: Windows entrypoint for an offline plan or a complete, explicitly authorized startup using the existing controllers.
- `.agents/skills/veronica-runpod-core/SKILL.md`: project guidance for Codex and Copilot.
- `scripts/runpod_core.py`: provenance capture, live preflight, default fail-closed startup, explicitly authorized supervised startup, and real API smoke tests.
- `scripts/supervised_runpod.py`: one-shot creation, exact Pod ownership, fixed deadline/local backup, SSH setup, tunnel, evidence capture, and confirmed termination. Run under WSL, where RunPod credentials and the SSH key reside.
- `scripts/keep-supervised-run-awake.ps1`: temporary Windows idle-sleep prevention with a readiness/heartbeat record, retained until matching confirmed termination or safe pre-creation cancellation. No hard-coded 130-minute expiry. Manual shutdown, disconnection, and hardware failures remain possible.
- `scripts/prepare_runpod_model.py`: on-Pod model reuse/download, complete hash validation, staging promotion, and optional serving.

The pinned PyTorch image and vLLM 0.11.0 were exercised with PyTorch 2.8/CUDA 12.8. Observed dependency versions are constrained by `config/runpod-runtime-0.11.0.txt`. This old development runtime is **not approved for public deployment**. Expose SSH only; serve on Pod loopback and use an SSH tunnel. Volume `v53gj9flzs` remains in `EUR-IS-1`; preserve Studio files. Its network mount reports shared-cluster free space, so the bootstrap also considers the actual 300 GB allowance.

## 1. Prepare and preflight without paid compute

Ask **"How long would you like the pod to run? Default: 1 hour."** when a start request does not already include its duration. Use **one hour for default selection**, and wait for the answer before paid creation. The terminal picker supports **1 hour (default)**, **2 hours**, **3 hours**, or **custom hours**; Enter chooses one hour. It only returns a duration and cannot create a Pod:

```bash
python3 scripts/runpod_core.py select-duration
```

Custom duration is limited to 24 hours, and every run needs current start authorization within the saved hourly ceiling. The watchdog begins its termination request at the exact selected deadline (one hour by default); it is supervised local enforcement, not a verified RunPod platform timer, so actual deletion can complete moments later or fail if the supervising computer is unavailable.

From the project root in WSL (or using the project's Python on Windows):

```bash
python3 scripts/runpod_core.py prepare --run-dir runs/<new-run>
python3 scripts/runpod_core.py preflight --run-dir runs/<new-run> --max-hourly-usd 1.75 --duration-minutes 60
```

Preparation saves candidate/control cards, licenses, configs, and Hub-expected sizes/hashes without downloading weights locally. Review provenance/license records. These expected hashes do not prove remote files are intact.

Default preflight checks placement, current price/stock, SSH registration, duplicates, and timer capability. An old timer flag alone proves nothing. The legacy non-supervised `runpod_core.py start` refuses creation. The new START launcher uses the supervised path, which validates a fresh, scoped approval file, reruns live preflight with the accepted shutdown arrangement, arms its local backup before creation, checks the actual Pod price, and never retries creation automatically.

## 2. Supervised startup with fresh authorization

Record the user's current authorization in the new run's `approval.json`: run ID, authorization timestamp, maximum hourly USD, duration minutes, one-resource count, exact GPU/volume/model revision, and `shutdownMode: supervised-with-local-backup`. This file records a conversation approval; writing it does not grant authority. Never reuse a consumed run. Start the Windows keep-awake helper hidden, then from the project root in WSL:

```bash
python3 scripts/runpod_core.py start --supervised --run-dir runs/<new-run> --approval-file runs/<new-run>/approval.json --ssh-key /home/dubs/.ssh/id_ed25519_runpod_noirworks
python3 scripts/supervised_runpod.py status --run-dir runs/<new-run>
python3 scripts/supervised_runpod.py inspect --run-dir runs/<new-run>
```

Inspect the volume first and configure any existing copy location in the profile. The script verifies a configured existing copy before reuse; an invalid copy is never overwritten. Otherwise it resumes/downloads the pinned revision into `.uploading-<revision>`, verifies every size/hash, and atomically promotes the directory. Interrupted downloads remain resumable.

After inspecting storage, run `python3 scripts/supervised_runpod.py bootstrap --run-dir runs/<new-run>`. It transfers the preparation script, profile, manifest and a private upstream-key file over SSH, then launches detached preparation/serving. The key is generated in WSL private state, not committed source, command arguments or evidence. Use the controller's `logs` command for progress. Runtime packages, GPU details and non-secret server command are recorded. The bootstrap script itself does not provide a billing timer.

## 3. Prove actual inference

Use the controller's `tunnel` command to forward local `127.0.0.1:18000` over SSH to Pod `127.0.0.1:8000`. Do not expose public model ingress. Its `verify` command loads the private key without putting it in command arguments:

```bash
python3 scripts/supervised_runpod.py verify --run-dir runs/<run>
```

This requires an advertised Veronica alias and actual generated text, checks multi-turn recall, and saves writing/coding/reasoning outputs with elapsed times. Inspect the responses: a smoke pass is not full capability qualification.

From Windows PowerShell, run `scripts/start-supervised-wrapper.ps1 -RunDir <absolute-run-directory>` in a separate process. It reads this run's private credential from WSL and supplies it only to the wrapper process, without changing `.env`. Agents launching it in the background must use `Start-Process -WindowStyle Hidden` with logs under the run directory. Verify tunnel reachability from Windows, then run the wrapper smoke test with the Windows project interpreter:

```bash
.venv\Scripts\python.exe scripts/runpod_core.py verify --base-url http://127.0.0.1:8010/v1 --wrapper --run-dir runs/<run>
```

Open `http://127.0.0.1:8010` as soon as the wrapper listens, without waiting for response tests. Verify a UI conversation once the model can answer; do not interrupt the owner's active chat to insert test messages. An observed owner exchange is valid UI evidence. Use the controller's `evidence` command to save remote hash/runtime evidence locally before shutdown.

## 4. Close the paid run

```bash
python3 scripts/supervised_runpod.py terminate --run-dir runs/<run>
```

Termination checks the exact saved Pod ID and unique name, deletes only that Pod, and confirms absence from inventory. It never deletes the network volume. A termination receipt also releases the local watchdog and keep-awake helper. Record final resource state and the next checkpoint. Never infer shutdown from a timer setting or a process exit; do not end a supervised turn with paid compute running.

