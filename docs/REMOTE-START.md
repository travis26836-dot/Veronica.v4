# Remote Veronica start

The **Veronica remote start** workflow provides a mobile/cloud entry point while
reusing the existing RunPod profile and supervised controller. It does not
create a second model deployment.

## Setup

Configure a protected GitHub environment named `veronica-remote-start` with
required reviewers. Add these repository or environment secrets:

- `RUNPOD_API_KEY`
- `VERONICA_SSH_PRIVATE_KEY`
- `VERONICA_SSH_PUBLIC_KEY`

The public key must already be registered with RunPod and correspond to the
private key. Do not put either key in workflow inputs or committed files.
The selected runner must also provide the pinned `runpodctl` CLI on `PATH`;
the workflow fails closed when it is absent rather than downloading an
unverified executable. Use a durable, private Linux runner labelled
`veronica-runpod`; a short-lived hosted runner cannot provide the controller's
shutdown supervision.

## Operations

Run **Actions → Veronica remote start → Run workflow**:

- `plan`: validates the requested duration and performs the existing
  no-creation preflight.
- `start`: enter exactly `START_VERONICA`, approve the protected environment,
  and start one supervised Pod.
- `stop`: provide the exact `run_id` to terminate only that owned Pod.

The workflow uploads run evidence for 14 days and reports the run directory in
the job log. A plan never creates paid compute.

## Important limitation

RunPod's termination flag is not a verified platform timer. Remote startup
therefore uses the existing local-backup supervision model; the GitHub runner
must remain alive and reachable for termination to be requested and confirmed.
This workflow must not claim guaranteed automatic shutdown. If the runner is
interrupted, dispatch `stop` after inspecting the evidence and reconcile the
exact run before any new start.

No public model ingress or unauthenticated mobile chat is provided. The current
remote boundary is workflow control, logs, and evidence artifacts. A future
chat relay needs independent authentication, authorization, and a durable
shutdown design.
