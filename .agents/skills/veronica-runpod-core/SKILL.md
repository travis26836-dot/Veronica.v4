---
name: veronica-runpod-core
description: Start Veronica when the user says "Start Veronica", "launch Veronica", or "boot Veronica"; prepare, verify, test, or shut down Veronica.v4's RunPod text core on its existing persistent model volume. Excludes Studio and unrelated RunPod workloads.
---

# Veronica RunPod core

Find the project root by locating `config/runpod-core.json` above this skill. The installed skill is a junction to this project's `.agents/skills/veronica-runpod-core`; resolve it if necessary. Canonical project: `C:\Users\raine\DEVELOPMENT\Projects\Veronica.v4`. Read `AGENTS.md`, `docs/SOURCE-OF-TRUTH.md`, `docs/STARTING-PROCEDURE.md`, `TODO.md`, and the latest run decision before acting.

The executable contract is `config/runpod-core.json`, `scripts/start-veronica.ps1`, and the existing Python controllers. Keep deployment choices in the profile, not a second cloud template. Prefer the checked launcher for the complete startup; use the installed RunPod skills/CLI or available MCP tools for read-only diagnostics. Never bypass the approval, ownership, or price checks through a direct MCP create call.

## START and STOP requests

An actual current request such as **"Start Veronica"** starts the configured workflow. It means a new Pod attached to existing storage, model startup, an SSH tunnel, and the local chat UI while loading and real inference checks continue. The model stays on the Pod. This is an agent skill, not a background microphone listener or a replacement for PowerShell's `start` alias.

The owner selected **one hour by default**, **one A100 80 GB**, **at most $1.75/hour**, and **supervision from this awake, connected computer**. Read the profile to get these values. At each START, ask exactly one question when the request does not already specify a duration: **"How long would you like the pod to run? Default: 1 hour."** Wait for the answer; "default", "usual", an empty interactive selection, or equivalent chooses 60 minutes. Do not treat silence as authorization to launch. Do not ask again about the saved spending ceiling or accepted supervision. Explicit durations may use one, two, three, or custom hours within the profile's 24-hour maximum; the window includes provisioning and loading, not just chat time. Storage charges remain separate.

1. Resolve the single duration question above, then run `scripts/start-veronica.ps1 -PlanOnly` with the chosen duration or lower price cap. Read-only preparation may happen while waiting for the answer; no paid creation. This preview is offline and creates nothing. Briefly announce the selected duration, ceiling, and supervised shutdown.
2. A fresh explicit request to **start** under the agreed limits supplies current per-run authorization. Record that real request in a new `runs/<UTC-date-time>-start-veronica/approval.json` using the fields in `docs/STARTING-PROCEDURE.md`. Configuration, planning, quoted commands, questions about startup, an old approval file, or a saved profile are not authorization to create a Pod. Never fabricate an approval. A scope change or unclear intent needs a concise question; a clear start request within the saved settings does not need repeated approval.
3. Run `scripts/start-veronica.ps1 -RunDir <absolute-run-directory> -ApprovalFile <absolute-approval-file>` with the same explicit overrides. Keep the launcher running in a monitored session; do not wait for its final result before opening the UI. It validates approval/local ports, prepares provenance, arms sleep prevention/watchdog, creates once, checks storage, bootstraps, tunnels, then starts the wrapper and saves `startup-ui-ready.json`. Model loading and generated-response checks continue, followed by `startup-ready.json` only after verification. Use `-PlanOnly` for configuration/testing requests; do not rent a test Pod to validate this skill.
4. As soon as `startup-ui-ready.json` exists, open `http://127.0.0.1:8010` and tell the owner the UI is available, with model loading/checks still pending. This is the owner's explicit UI-first preference from the 2026-08-31 startup; do not hold the interface behind inference tests. The UI automatically refreshes provider status; replies require the model server to finish loading, but background tests must not gate access. Report the fixed deadline and evidence path. Verify an actual UI exchange without disrupting the owner's conversation; an observed owner exchange counts. Report successful direct/wrapper checks separately. Do not terminate immediately after smoke tests unless requested or startup fails.
5. Remain engaged during the supervised run. Use bounded checks of Pod status, watchdog heartbeat, keep-awake state, and deadline; no busy polling or repeated unchanged updates. At the deadline or **"Stop Veronica"/"Shut down Veronica"**, capture available evidence and run `supervised_runpod.py terminate --run-dir <this-run>` under WSL. Confirm the exact Pod is absent before finishing the supervised turn. Never delete the network volume or extend a deadline silently.

If a Veronica Pod already exists, inspect its exact ownership and remaining authorization; do not create another or silently reset its deadline. If local port 8010 or the tunnel port is occupied, identify the process before replacing anything. A verified stale wrapper from this exact project may be restarted for the new run; never kill an unrelated listener. Startup failure after creation must terminate the owned Pod and confirm absence; uncertain creation is reconciled, never retried automatically.

## Runtime boundary

- Keep the public alias `Veronica`; the candidate is provisional and its weights stay unchanged.
- Store model artifacts under `/workspace/veronica-core/` on the profile's existing network volume. Preserve Studio and donor files. Inspect existing copies before downloading; use the exact pinned revision, resumable `.uploading-<revision>` storage, and full hash verification before promotion.
- Keep credentials out of the profile, skill, command-line arguments, and evidence. Use the local RunPod credential store, SSH agent/key, and a separate upstream API key supplied through the process environment.
- The development vLLM runtime is pinned for PyTorch compatibility, not security-qualified for public deployment. Expose SSH only; serve on Pod loopback and reach it over an SSH tunnel. Do not turn on public vLLM ingress.

## Paid runs

Each new Pod needs current user authorization covering an hourly ceiling, duration/deadline, and resource count. A previous approval or saved profile does not authorize another run. Do not create a replacement Pod automatically.

`python3 scripts/runpod_core.py select-duration` is the terminal duration picker: one, two, three, or custom hours; Enter selects one hour. In agent chat, use the single plain-language question above, not a repeated configuration interview. A duration choice outside a current start request is not spending authorization.

Run the read-only preflight with the approved limits. RunPod's `--terminate-after` never enforced a deadline and was removed in CLI 2.12.0 (official issue: https://github.com/runpod/runpodctl/pull/330). Default startup remains blocked without a verified platform timer. Do not downgrade the CLI or flip the safety field.

The launcher uses the explicitly supervised controller path; the older default `runpod_core.py start` remains blocked without a verified platform timer. The owner accepted the awake/connected-computer constraint for this START workflow. Preserve this limitation in the brief startup summary: a local backup cannot enforce shutdown if the computer sleeps, disconnects, or fails. The watchdog fixes the deadline before creation and never automatically creates a replacement. The keep-awake helper prevents idle sleep until a matching confirmed termination or a safe pre-creation cancellation, rather than expiring on an unrelated fixed timer. It does not guarantee connectivity. Stay engaged; terminate and confirm absence before ending the run. A saved approval is evidence, not reusable spending authority.

## Checkpoints

1. Use `prepare --run-dir runs/<new-run>` to save pinned candidate/control cards, licenses, expected artifact hashes, and the profile. Review the provenance before advancing; metadata alone does not validate remote files.
2. After a safely bounded Pod exists, run `prepare_runpod_model.py` on it with the profile and expected manifest. Save the resulting actual hash manifest and runtime versions locally under the run before stopping.
3. Validate `/v1/models` and an actual generated completion through the SSH tunnel, then through the local wrapper. Use `verify` and `verify --wrapper`, with distinct evidence output names. Inspect saved responses. Mock tests, server health, and file download are not inference proof; smoke tests are not full capability qualification.
4. Terminate the exact owned Pod, confirm it is absent from live inventory, and preserve the network volume. Reconcile TODOs and write a decision; archive superseded documentation only after proof is retained in `runs/`.

Report briefly: actual model state, evidence path, next checkpoint, and paid-resource state. Never claim automatic termination was armed without evidence.
