#!/usr/bin/env bash
# Explicit cleanup helper for a Veronica development Pod. Network volumes are preserved.
set -euo pipefail

pod_id="${1:?Usage: scripts/terminate-runpod-pod.sh <pod-id>}"
command -v runpodctl >/dev/null || { printf 'ERROR: runpodctl is not installed.\n' >&2; exit 1; }
runpodctl pod get "$pod_id"
runpodctl pod delete "$pod_id"
printf 'Termination requested for Pod %s. The attached network volume was not deleted.\n' "$pod_id"
