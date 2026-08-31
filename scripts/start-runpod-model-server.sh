#!/usr/bin/env bash
# Compatibility entrypoint: never use the old, unenforced --terminate-after flag.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/runpod_core.py" start "$@"
