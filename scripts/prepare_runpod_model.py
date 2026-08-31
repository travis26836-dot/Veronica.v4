"""Run INSIDE a provisioned Pod: validate/resume model files, then optionally serve.

Requires a profile and expected manifest produced by runpod_core.py prepare.
Does not create Pods or provide a billing termination guard.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def validated_path(root, name):
    root = Path(root).resolve()
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError(f"Unsafe artifact path: {name}")
    return path


def verify_files(directory, manifest):
    records = []
    for expected in manifest["files"]:
        path = validated_path(directory, expected["path"])
        if not path.is_file() or path.stat().st_size != expected["bytes"]:
            raise ValueError(f"Missing/wrong-size file: {expected['path']}")
        sha256 = hashlib.sha256()
        blob = hashlib.sha1(f"blob {expected['bytes']}\0".encode())
        with path.open("rb") as source:
            while chunk := source.read(8 * 1024 * 1024):
                sha256.update(chunk)
                blob.update(chunk)
        if expected["sha256"]:
            valid = sha256.hexdigest() == expected["sha256"]
        else:
            valid = blob.hexdigest() == expected["gitBlob"]
        if not valid:
            raise ValueError(f"Checksum mismatch: {expected['path']}")
        records.append({"path": expected["path"], "bytes": expected["bytes"], "sha256": sha256.hexdigest()})
        print(f"VERIFIED {expected['path']}", flush=True)
    return records


def command(*args, env=None):
    subprocess.run(args, check=True, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--key-file", type=Path, help="Private JSON file containing apiKey; never logged")
    parser.add_argument("--runtime-constraints", type=Path)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text())
    manifest = json.loads(args.manifest.read_text())
    model, runtime = profile["model"], profile["runtime"]
    if (manifest["repository"], manifest["revision"]) != (model["repository"], model["revision"]):
        raise ValueError("Profile and expected manifest identify different models")
    canonical = Path(model["directory"])
    if not canonical.resolve().is_relative_to(Path("/workspace/veronica-core/models")):
        raise ValueError("Model storage escapes Veronica's volume namespace")
    if not Path("/workspace").is_mount():
        raise ValueError("/workspace must be the attached persistent volume")
    if args.key_file:
        os.environ["VERONICA_UPSTREAM_API_KEY"] = json.loads(args.key_file.read_text())["apiKey"]
    if args.serve and not os.environ.get("VERONICA_UPSTREAM_API_KEY"):
        raise ValueError("Set VERONICA_UPSTREAM_API_KEY in the Pod shell before --serve")
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"HF_HOME": "/workspace/veronica-core/hf-cache", "UV_CACHE_DIR": "/workspace/veronica-core/uv-cache", "HF_HUB_DOWNLOAD_TIMEOUT": "120"})
    candidates = [canonical, Path(model["existingCopyDirectory"])]
    existing = next((p for p in candidates if p.exists()), None)
    if existing is not None:
        # A bad existing copy is never silently overwritten or replaced by another download.
        records = verify_files(existing, manifest)
        selected = existing
    else:
        canonical.parent.mkdir(parents=True, exist_ok=True)
        staging = canonical.with_name(".uploading-" + model["revision"])
        staging.mkdir(exist_ok=True)
        if not staging.resolve().is_relative_to(canonical.parent.resolve()):
            raise ValueError("Staging directory escapes model storage")
        remaining = sum(max(0, f["bytes"] - (validated_path(staging, f["path"]).stat().st_size if validated_path(staging, f["path"]).is_file() else 0)) for f in manifest["files"])
        available = shutil.disk_usage(staging).free
        # RunPod's network mount can report the whole cluster's free space, not
        # the purchased allowance. Use the smaller, conservatively measured limit.
        if capacity_gb := profile["pod"].get("networkVolumeSizeGb"):
            used = int(subprocess.check_output(["du", "-sb", "/workspace"]).split()[0])
            available = min(available, int(capacity_gb * 10**9) - used)
            (args.evidence_dir / "storage-budget.json").write_text(json.dumps({"capacityGb": capacity_gb, "observedUsedBytes": used, "remainingDownloadBytes": remaining, "headroomBytes": 20 * 1024**3}, indent=2))
        if available < remaining + 20 * 1024**3:
            raise ValueError("Insufficient volume space for model and runtime headroom")
        # A separate CLI environment keeps modern hf independent of vLLM's SDK constraints.
        cli_env = Path("/workspace/veronica-core/hf-cli-" + runtime["hfCliVersion"])
        if not (cli_env / "bin/hf").exists():
            command("uv", "venv", "--python", "python3", str(cli_env), env=env)
            command("uv", "pip", "install", "--python", str(cli_env / "bin/python"), "huggingface-hub==" + runtime["hfCliVersion"], env=env)
        command(str(cli_env / "bin/hf"), "download", model["repository"], "--revision", model["revision"], "--local-dir", str(staging), "--max-workers", "4", env=env)
        records = verify_files(staging, manifest)
        # Same-filesystem atomic promotion; retain staging on download/hash failure.
        staging.rename(canonical)
        selected = canonical
    (args.evidence_dir / "validated-model-manifest.json").write_text(json.dumps({"repository": model["repository"], "revision": model["revision"], "directory": str(selected), "files": records}, indent=2) + "\n")
    if not args.serve:
        print(f"MODEL VERIFIED: {selected}")
        return
    runtime_env = Path("/workspace/veronica-core/runtime-vllm-" + runtime["vllmVersion"])
    if not (runtime_env / "bin/python").exists():
        command("uv", "venv", "--system-site-packages", "--python", "python3", str(runtime_env), env=env)
    constraints = ["--constraint", str(args.runtime_constraints)] if args.runtime_constraints else []
    command("uv", "pip", "install", "--python", str(runtime_env / "bin/python"), *constraints, "vllm==" + runtime["vllmVersion"], "transformers==" + runtime["transformersVersion"], env=env)
    frozen = subprocess.check_output(["uv", "pip", "freeze", "--python", str(runtime_env / "bin/python")], env=env)
    (args.evidence_dir / "runtime-packages.txt").write_bytes(frozen)
    gpu_info = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    (args.evidence_dir / "gpu.txt").write_bytes(gpu_info)
    env["VLLM_API_KEY"] = env.pop("VERONICA_UPSTREAM_API_KEY")
    env["HF_HUB_OFFLINE"] = "1"
    server = [str(runtime_env / "bin/python"), "-m", "vllm.entrypoints.openai.api_server", "--model", str(selected), "--served-model-name", profile["publicAlias"], "--host", runtime["host"], "--port", str(runtime["port"]), "--dtype", runtime["dtype"], "--max-model-len", str(runtime["maxModelLen"]), "--max-num-seqs", str(runtime["maxNumSeqs"]), "--gpu-memory-utilization", str(runtime["gpuMemoryUtilization"]), "--enforce-eager"]
    (args.evidence_dir / "server-command.json").write_text(json.dumps(server, indent=2) + "\n")
    # Run foreground under a supervisor/setsid chosen by the deployment controller.
    os.execve(server[0], server, env)


if __name__ == "__main__":
    main()
