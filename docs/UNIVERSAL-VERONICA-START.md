# Universal Veronica Start Procedure

## Goal

Every supported agent uses the same request and the same command:

> **Start Veronica for 1 hour**

or, at the terminal:

```bash
uv run veronica-start --authorize-start --duration-minutes 60 \
  --requested-by <agent-name> \
  --authorization-context "Owner requested Start Veronica for one hour."
```

The agent-facing wording is universal. The cloud lifecycle remains centralized on **one approved Windows controller host** so a start always has the same private SSH key, local UI, keep-awake helper, watchdog, evidence records, and exact-termination procedure.

## What the universal command does

`veronica-start` is a small router, not a second Pod launcher.

| Where it runs | Result |
| --- | --- |
| The named Windows controller | Calls `scripts/start-veronica-universal.ps1`, which creates a fresh one-use approval and invokes the existing checked `scripts/start-veronica.ps1` workflow. |
| Codex, Copilot, Hermes, Manus, or another non-controller host | Dispatches the protected **Start Veronica** GitHub Actions workflow to the controller host. |
| No online controller | Fails closed with **no Runpod API mutation** and no Pod creation. |

The command always receives a current owner authorization from the conversation that invokes it. It does not reuse a prior approval record. A planning-only preview remains available:

```bash
uv run veronica-start --plan
```

This preview does not call Runpod, create an approval, dispatch GitHub Actions, or create a Pod.

## The one control-plane architecture

```text
Any approved agent
  "Start Veronica for 1 hour"
            |
            v
  veronica-start (same Python command everywhere)
            |
            +-- Windows controller host --> checked launcher --> one supervised Runpod Pod
            |
            +-- Other host --> protected GitHub dispatch --> Windows controller host
                                                     |
                                                     v
                                           local UI: http://127.0.0.1:8010
```

The Windows controller is an execution boundary, not a second agent. It is where the existing approved workflow runs because that workflow needs Windows PowerShell 7, WSL, the private SSH key, the local wrapper/UI, and a continuously running local watchdog. The project-pinned Runpod MCP remains useful for inventory and general administration, but it is **not** the Veronica deployment adapter.

## One-time controller activation

The repository currently has **no registered self-hosted controller runner**, so remote dispatch intentionally fails closed until this is completed. On the actual Windows + WSL machine that already has the working Veronica prerequisites:

1. In GitHub, open **Settings → Actions → Runners → New self-hosted runner** for this repository.
2. Follow GitHub’s Windows instructions in an elevated PowerShell session. GitHub recommends `C:\actions-runner` when installing as a service.
3. Add the custom runner label **`veronica-controller`**. The workflow requires all four labels:
   - `self-hosted`
   - `windows`
   - `x64`
   - `veronica-controller`
4. Keep the runner service online **under the same Windows account that owns the Veronica WSL distribution**. Do not use `LocalSystem` unless that account has the same WSL distribution, `runpodctl` credential store, and `/home/dubs/.ssh/id_ed25519_runpod_noirworks` key pair. The workflow refuses to continue if the runner service account cannot access those prerequisites.
5. In the repository’s Actions settings, create the **`veronica-paid-start`** environment and require the owner as an approver. This protects remote paid starts even if a GitHub credential can dispatch workflows.
6. Run `pwsh -NoProfile -File .\scripts\start-veronica.ps1 -PlanOnly` on that machine to verify its prerequisites without creating a Pod, then check that the runner appears **online** with all four labels.

> GitHub documents that self-hosted runners receive OS and architecture labels and can be targeted cumulatively by workflow labels. It also notes that Windows runner service installation needs an elevated shell. See [Using self-hosted runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow) and [Adding self-hosted runners](https://docs.github.com/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners).

This repository is currently public. The controller workflow is manual-dispatch
only and pinned to the repository's default branch by `veronica-start`; do not
add `pull_request`, `pull_request_target`, or untrusted-branch triggers to any
workflow that targets `veronica-controller`. GitHub warns that public-repository
self-hosted runners can execute dangerous fork-provided code if workflows allow
it. Keep the controller label exclusive to the owner machine and use the
protected environment above.

## Agent adapter contract

Agents do **not** need separate Runpod-specific starter scripts. Configure each agent’s project instruction or skill to follow this contract:

1. Recognize **Start Veronica**, **launch Veronica**, or **boot Veronica** as a request for the universal command.
2. Ask exactly one question only when no duration is supplied: **“How long would you like the pod to run? Default: 1 hour.”**
3. Treat a clear current request with a duration as the one-run authorization. Do not reuse an old approval or start a replacement Pod.
4. Invoke `uv run veronica-start` with the explicit duration, `--authorize-start`, the agent identity, and a short non-secret authorization context.
5. Report the dispatch or local-controller result. Do not claim UI readiness or model inference until the controller writes the corresponding run evidence.
6. For **Stop Veronica**, inspect the owned run and use the existing supervised termination controller; never delete the persistent network volume.

The same command works for Codex, Copilot, Hermes, Manus, and a human terminal because it depends on the repository and GitHub CLI—not on an agent-specific MCP installation.

## Paid-run guarantees that remain unchanged

The universal contract does **not** loosen any existing gate:

- Exactly one Pod per approved run; no automatic replacement.
- A fresh run directory and one-use approval record.
- Live preflight of price, GPU stock, volume placement, duplicate Pods, and SSH registration.
- The configured one-A100/80-GB-class GPU policy, duration, and **$1.75/hour maximum** from `config/runpod-core.json`.
- Private SSH-only model access and local wrapper/UI.
- A fixed supervised local shutdown deadline, explicit termination, and proof that the exact Pod is absent.
- Persistent model volume retained on shutdown.

The watchdog is still a local safeguard, not a verified Runpod platform timer. The controller machine must remain awake and connected until termination is confirmed.

## Manual fallback

If GitHub Actions is unavailable, run the same controller adapter directly **only on the designated Windows controller**:

```powershell
pwsh -NoProfile -File .\scripts\start-veronica-universal.ps1 `
  -DurationMinutes 60 `
  -RequestedBy "human" `
  -AuthorizationContext "Owner requested Start Veronica for one hour."
```

Do not run this adapter on a sandbox, a hosted Linux runner, or a machine missing the WSL credential/key/wrapper setup. It will fail closed rather than creating a raw Pod.

## Current validation status

- **Implemented and locally tested:** universal plan, explicit-authorization gate, runner-label selection, no-runner failure, and dispatch payload construction.
- **Protected plan-only verification:** the manual **Start Veronica** workflow accepts `plan_only: true`; it checks the controller path and runs `scripts/start-veronica.ps1 -PlanOnly` without creating an approval record, Runpod Pod, or run-evidence artifact.
- **Not yet live verified:** the controller’s protected plan-only workflow dispatch and a paid Windows controller launch. A paid run still requires a separate current owner authorization and protected-environment approval.
