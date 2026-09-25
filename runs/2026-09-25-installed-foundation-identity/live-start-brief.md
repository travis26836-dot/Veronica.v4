# Live baseline start brief

**Owner duration choice:** 1 hour (60 minutes), selected 2026-09-25.  
**Hourly ceiling:** $1.75  
**GPU:** one NVIDIA A100-SXM4-80GB in `EUR-IS-1`  
**Volume:** existing `v53gj9flzs`  
**Public alias:** `Veronica.v.4.1-30B-A3B-BF16`  
**Revision:** `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`  
**Shutdown:** supervised local watchdog; confirm exact Pod absence

This file is a start brief, not a reusable approval. A one-use `approval.json` must be written on the Windows/WSL machine at the moment of START, with a current `authorizedAtUtc`.

## Why this sandbox cannot START

The Manus sandbox for this session has:

- no RunPod CLI
- no RunPod API credential
- no SSH key
- no Windows `pwsh` launcher environment

The checked launcher is `scripts/start-veronica.ps1` plus WSL controllers. Do not create a Pod from the RunPod website or any MCP create tool.

## Do not START from `origin/main`

`origin/main` still advertises public alias `Veronica` and Candidate-era docs. START only after this identity branch is on the Windows worktree:

- branch: `docs/installed-foundation-identity`
- public alias must be `Veronica.v.4.1-30B-A3B-BF16`

## Spending guard

Owner and `docs/STARTING-PROCEDURE.md` require **$1.75/hour**. If `config/runpod-core.json` still shows `maximumHourlyUsd: 4.0` or an H100 fallback at $4, do **not** pass that file through as-is. Override `-MaxHourlyUsd 1.75` and refuse any offer above that ceiling.

Preferred live-baseline profile, once the identity branch is present: `config/runpod-foundation-baseline.json` (ceiling $1.75, no $4 fallback).

## START sequence on Windows/WSL

1. Keep the computer awake and connected.
2. Preview only:

```powershell
.\scripts\start-veronica.ps1 -PlanOnly -DurationMinutes 60 -MaxHourlyUsd 1.75
```

3. Write a **new** one-use approval with current UTC time, then:

```powershell
.\scripts\start-veronica.ps1 -RunDir <absolute-new-run-directory> -ApprovalFile <absolute-approval-file> -DurationMinutes 60 -MaxHourlyUsd 1.75
```

4. Open `http://127.0.0.1:8010` when `startup-ui-ready.json` exists. That is UI readiness, not qualification.
5. After the model is up, collect the frozen baseline tracks from `config/foundation-baseline-qualification.json`. Historical smoke chats are not a substitute.
6. At 60 minutes or on "Stop Veronica", terminate the owned Pod and confirm it is absent. Keep the network volume.

## Next core milestone after a successful START

Stage 4 live baseline: raw responses, automatic checks, runtime attestation, executable-code / native-tool / long-context / JSON evidence, and a signed hold/qualify/reject decision. Persona and training remain later.
