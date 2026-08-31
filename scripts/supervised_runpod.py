"""One-shot supervised Pod controller. The local watchdog is NOT a cloud timer.

Run under WSL, whose RunPod credentials and SSH key remain outside the project.
Never retries creation. Receipt, fixed deadline, and exact ownership survive turns.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import runpod_core as core


def now():
    return datetime.now(timezone.utc)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def state_at(run):
    return core.read_json(run / "supervised-state.json")


def validate_approval(approval, profile, run, instant=None):
    instant = instant or now()
    safety = core.validate_profile_safety(profile)
    core.validate_limits(approval.get("maxHourlyUsd"), approval.get("durationMinutes"),
                         maximum_minutes=core.duration_policy(profile)["maximum"],
                         maximum_hourly_usd=safety["maximumHourlyUsd"])
    if type(approval.get("resourceCount")) is not int or approval["resourceCount"] != 1 or approval.get("shutdownMode") != "supervised-with-local-backup":
        raise ValueError("An explicit one-Pod supervised authorization is required")
    if approval.get("runId") != run.name or approval.get("modelRevision") != profile["model"]["revision"]:
        raise ValueError("Authorization must identify this run and model revision")
    if approval.get("networkVolumeId") != profile["pod"]["networkVolumeId"] or approval.get("gpuTypeId") != profile["pod"]["gpuTypeId"]:
        raise ValueError("Authorization must identify this volume and GPU")
    try:
        issued = datetime.fromisoformat(approval["authorizedAtUtc"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Authorization must have a valid timezone-aware timestamp") from error
    if issued.tzinfo is None:
        raise ValueError("Authorization timestamp must include a timezone")
    if not timedelta(0) <= instant - issued <= timedelta(hours=2):
        raise ValueError("Authorization is not current; obtain new user authorization")
    if (run / "supervised-state.json").exists():
        raise ValueError("This authorization/run was already used; never retry creation")


def owned_pods(state):
    inventory = json.loads(core.cli("pod", "list", "--all"))
    by_id = [p for p in inventory if state.get("podId") and p.get("id") == state["podId"]]
    if by_id and by_id[0].get("name") != state["podName"]:
        raise RuntimeError("Owned Pod was renamed; absence is not confirmed")
    matches = [p for p in inventory if p.get("name") == state["podName"]]
    if len(matches) > 1:
        raise RuntimeError("Ambiguous Pod ownership: manual inspection required")
    if matches and state.get("podId") and matches[0]["id"] != state["podId"]:
        raise RuntimeError("Pod ID does not match the saved owned resource")
    return matches


def terminate(run):
    state = state_at(run)
    matches = owned_pods(state)
    pod_id = matches[0]["id"] if matches else state.get("podId")
    if not matches and state.get("creationAttempted") and not pod_id:
        # An API request can be accepted after its local client times out. An
        # empty listing alone cannot close that unresolved creation attempt.
        raise RuntimeError("Pod creation outcome is unresolved; keep supervising. Termination is NOT confirmed")
    if matches:
        if not state.get("podId"):
            state["podId"] = pod_id
            write(run / "supervised-state.json", state)
        try:
            core.cli("pod", "delete", pod_id)
        except RuntimeError:
            # REST deletion can succeed while the CLI rejects an empty 204 response.
            pass
    if owned_pods(state):
        raise RuntimeError("Pod still present; termination NOT confirmed")
    write(run / "termination.json", {"confirmedAtUtc": now().isoformat(), "podId": pod_id,
          "podName": state["podName"], "confirmedAbsent": True, "networkVolumeRetained": True})
    print(f"Confirmed Pod {pod_id or state['podName']} absent; persistent volume retained.", flush=True)


def watchdog(run):
    initial = state_at(run)
    # Read deadline once. Subsequent state updates cannot extend it.
    shutdown_at = datetime.fromisoformat(initial["backupShutdownAtUtc"])
    write(run / "watchdog-ready.json", {"pid": os.getpid(), "shutdownAtUtc": shutdown_at.isoformat(), "platformTimer": False})
    while True:
        write(run / "watchdog-heartbeat.json", {"atUtc": now().isoformat(), "pid": os.getpid()})
        receipt = run / "termination.json"
        if receipt.exists() and core.read_json(receipt).get("confirmedAbsent"):
            return
        cancelled = run / "startup-cancelled.json"
        if cancelled.exists():
            cancellation = core.read_json(cancelled)
            current = state_at(run)
            if (cancellation.get("runId") == run.name and cancellation.get("creationAttempted") is False
                    and current.get("creationAttempted") is False):
                return
        if now() >= shutdown_at:
            try:
                terminate(run)
                return
            except Exception as error:
                print(f"Shutdown not yet confirmed: {type(error).__name__}: {error}", flush=True)
        time.sleep(5)


@contextmanager
def start_lock(path=None):
    """Serialize local STARTs; the OS releases this lock even on process failure."""
    import fcntl
    path = path or Path.home() / ".local/state/veronica/start.lock"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another Veronica START is in progress; no additional Pod created") from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def require_closed_previous_runs(run):
    # Live inventory can lag behind a create request. Local unresolved records
    # block a second rental even when the API temporarily lists nothing.
    for path in (core.ROOT / "runs").glob("*/supervised-state.json"):
        if path.parent.resolve() == run.resolve():
            continue
        state = core.read_json(path)
        if not state.get("creationAttempted"):
            continue
        receipt_path = path.parent / "termination.json"
        receipt = core.read_json(receipt_path) if receipt_path.exists() else {}
        closed = (receipt.get("confirmedAbsent") is True and receipt.get("podName") == state.get("podName")
                  and bool(state.get("podId")) and receipt.get("podId") == state["podId"])
        if not closed:
            raise RuntimeError(f"Earlier run {path.parent.name} has no confirmed closeout; reconcile it before another START")


def start(profile, run, approval_file, ssh_key):
    if os.name == "nt":
        raise ValueError("Run this controller under WSL so its credentials and watchdog share one environment")
    with start_lock():
        require_closed_previous_runs(run)
        _start_locked(profile, run, approval_file, ssh_key)


def _start_locked(profile, run, approval_file, ssh_key):
    approval = core.read_json(approval_file)
    validate_approval(approval, profile, run)
    if (run / "startup-cancelled.json").exists():
        raise ValueError("This startup was cancelled; use a fresh current request and run")
    if not ssh_key.is_file() or not ssh_key.with_suffix(ssh_key.suffix + ".pub").is_file():
        raise ValueError("Registered SSH private/public key pair required")
    result = core.preflight(profile, approval["maxHourlyUsd"], approval["durationMinutes"], supervised=True)
    write(run / "preflight.json", result)
    print(json.dumps(result, indent=2), flush=True)
    if not result["safeToCreate"]:
        raise RuntimeError("No Pod created: resolve preflight blockers")
    manifest = core.read_json(run / "expected-model-manifest.json")
    if (manifest["repository"], manifest["revision"]) != (profile["model"]["repository"], profile["model"]["revision"]):
        raise ValueError("Pinned provenance manifest required before paid creation")
    if (run / "startup-cancelled.json").exists():
        raise RuntimeError("Startup cancelled during preflight; no Pod created")
    started = now()
    deadline = started + timedelta(minutes=approval["durationMinutes"])
    state = {"runId": run.name, "podName": profile["pod"]["namePrefix"] + started.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(4),
             "createdAttemptAtUtc": started.isoformat(), "deadlineUtc": deadline.isoformat(),
             # Begin deletion at the owner-selected interval. Completion remains
             # best-effort local supervision, not a platform-enforced timer.
             "backupShutdownAtUtc": deadline.isoformat(),
             "maxHourlyUsd": approval["maxHourlyUsd"], "sshKey": str(ssh_key), "podId": None,
             "platformTimer": False, "creationAttempted": False}
    write(run / "profile.json", profile)
    write(run / "supervised-state.json", state)
    with (run / "watchdog.log").open("ab") as log:
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "watchdog", "--run-dir", str(run)],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    for _ in range(50):
        if (run / "watchdog-ready.json").exists():
            break
        if child.poll() is not None:
            raise RuntimeError("Local watchdog failed; no Pod created")
        time.sleep(.1)
    else:
        raise RuntimeError("Local watchdog did not acknowledge; no Pod created")
    pod = profile["pod"]
    public_key = ssh_key.with_suffix(ssh_key.suffix + ".pub").read_text().strip()
    args = ["pod", "create", "--name", state["podName"], "--image", pod["image"],
            "--gpu-id", pod["gpuTypeId"], "--gpu-count", "1", "--cloud-type", pod["cloudType"],
            "--data-center-ids", pod["dataCenterId"], "--network-volume-id", pod["networkVolumeId"],
            "--container-disk-in-gb", str(pod["containerDiskInGb"]), "--volume-mount-path", pod["volumeMountPath"],
            "--ports", ",".join(pod["ports"]), "--min-cuda-version", "12.8", "--ssh", "--env", json.dumps({"PUBLIC_KEY": public_key})]
    if (run / "startup-cancelled.json").exists():
        raise RuntimeError("Startup cancelled before creation; no Pod created")
    if now() >= deadline:
        raise RuntimeError("The approved deadline arrived before creation; no Pod created")
    state["creationAttempted"] = True
    write(run / "supervised-state.json", state)
    try:
        created = json.loads(core.cli(*args))
        state["podId"] = created["id"]
        write(run / "supervised-state.json", state)
        if now() >= datetime.fromisoformat(state["backupShutdownAtUtc"]) or (run / "termination.json").exists():
            raise RuntimeError("Startup exceeded the supervised window; terminate without setup")
        # Never store raw Pod output: it can contain environment secrets.
        details = json.loads(core.cli("pod", "get", state["podId"]))
        price = details.get("costPerHr")
        if not core.price_within_limit(price, approval["maxHourlyUsd"]):
            raise RuntimeError("Actual Pod price was not verified within the authorized ceiling")
        state["actualHourlyUsd"] = price
        write(run / "supervised-state.json", state)
        print(json.dumps(state, indent=2))
    except Exception:
        # On uncertain creation, resolve the unique name and clean it up, never retry.
        for _ in range(3):
            matches = owned_pods(state)
            if matches:
                state["podId"] = matches[0]["id"]
                write(run / "supervised-state.json", state)
                terminate(run)
                break
            time.sleep(3)
        raise


def connection(run):
    state = state_at(run)
    if not state.get("podId") or (run / "termination.json").exists():
        raise RuntimeError("No active owned Pod")
    info = json.loads(core.cli("ssh", "info", state["podId"]))
    # CLI schema is checked live before bootstrap.
    ip, port = info.get("ip"), info.get("port")
    if not ip or not port:
        raise RuntimeError("Pod SSH endpoint not ready")
    return ["ssh", "-i", state["sshKey"], "-p", str(port), "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
            "-o", "StrictHostKeyChecking=accept-new", "-o", "UserKnownHostsFile=" + str(Path.home() / ".ssh/known_hosts_veronica_runpod"),
            f"root@{ip}"]


def ssh(run, command, data=None, timeout=60):
    result = subprocess.run([*connection(run), command], input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-3000:])
    return result.stdout


def remote_dir(run):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", run.name):
        raise ValueError("Unsafe remote run name")
    return "/workspace/veronica-core/runs/" + run.name


def bootstrap(run):
    if (run / "bootstrap-start.json").exists():
        raise RuntimeError("Bootstrap already started; inspect logs instead of launching twice")
    private_dir = Path.home() / ".local/state/veronica" / run.name
    private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    private_file = private_dir / "upstream.json"
    if not private_file.exists():
        private_file.write_text(json.dumps({"apiKey": secrets.token_urlsafe(32)}))
        private_file.chmod(0o600)
    files = {"prepare_runpod_model.py": core.ROOT / "scripts/prepare_runpod_model.py",
             "profile.json": run / "profile.json", "expected-model-manifest.json": run / "expected-model-manifest.json",
             "upstream-private.json": private_file}
    profile = core.read_json(run / "profile.json")
    if constraints_name := profile["runtime"].get("constraintsFile"):
        constraints = (core.ROOT / constraints_name).resolve()
        if not constraints.is_relative_to(core.ROOT / "config"):
            raise ValueError("Runtime constraints must be in project config/")
        files["runtime-constraints.txt"] = constraints
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as archive:
        for name, path in files.items():
            content = path.read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(content), 0o600
            archive.addfile(info, io.BytesIO(content))
    dest = remote_dir(run)
    ssh(run, f"umask 077; mkdir -p {shlex.quote(dest)} && tar -xf - -C {shlex.quote(dest)}", buf.getvalue())
    cmd = ["python3", "-u", dest + "/prepare_runpod_model.py", "--profile", dest + "/profile.json",
           "--manifest", dest + "/expected-model-manifest.json", "--evidence-dir", dest,
           "--key-file", dest + "/upstream-private.json", "--serve"]
    if constraints_name:
        cmd.extend(["--runtime-constraints", dest + "/runtime-constraints.txt"])
    output = ssh(run, f"setsid {shlex.join(cmd)} >{shlex.quote(dest + '/bootstrap.log')} 2>&1 </dev/null & echo $!")
    write(run / "bootstrap-start.json", {"atUtc": now().isoformat(), "remotePid": output.decode().strip(), "remoteDirectory": dest, "privateKeyFile": str(private_file)})
    print("Detached model bootstrap started. Logs and validated artifacts remain on the persistent volume.")


def ready(run):
    """Bounded authenticated readiness probe; not proof of generated inference."""
    state = state_at(run)
    if not state.get("podId") or (run / "termination.json").exists():
        raise RuntimeError("No active owned Pod")
    if now() >= datetime.fromisoformat(state["deadlineUtc"]):
        raise RuntimeError("The approved run deadline has arrived; terminate this Pod")
    heartbeat = core.read_json(run / "watchdog-heartbeat.json")
    age = now() - datetime.fromisoformat(heartbeat["atUtc"])
    if not timedelta(0) <= age <= timedelta(seconds=45):
        raise RuntimeError("Local watchdog heartbeat is stale; readiness cannot be confirmed")
    profile = core.profile_at(run / "profile.json")
    private = core.read_json(run / "bootstrap-start.json")["privateKeyFile"]
    key = core.read_json(private)["apiKey"]
    port = profile["runtime"]["localTunnelPort"]
    request = Request(f"http://127.0.0.1:{port}/v1/models", headers={"Authorization": "Bearer " + key})
    result = {"checkedAtUtc": now().isoformat(), "ready": False,
              "inferenceVerified": False, "platformDeadlineEnforced": False}
    try:
        with urlopen(request, timeout=5) as response:
            models = json.loads(response.read())
    except HTTPError as error:
        if error.code not in (429, 502, 503, 504):
            raise RuntimeError(f"Model readiness failed with HTTP {error.code}") from None
        result["waitingReason"] = "Model server is loading or temporarily unavailable"
    except (URLError, TimeoutError, ConnectionError):
        result["waitingReason"] = "Model server has not answered over the SSH tunnel"
    else:
        if not isinstance(models, dict) or not isinstance(models.get("data"), list):
            raise RuntimeError("Unexpected model-list response")
        if not any(isinstance(model, dict) and model.get("id") == profile["publicAlias"] for model in models["data"]):
            raise RuntimeError("Model server did not advertise the Veronica alias")
        result["ready"] = True
        result["publicAlias"] = profile["publicAlias"]
    write(run / "provider-ready.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return result["ready"]


def benchmark(run):
    profile = core.read_json(run / "profile.json")
    key = core.read_json(core.read_json(run / "bootstrap-start.json")["privateKeyFile"])["apiKey"]
    payload = {"model": "Veronica", "messages": [{"role": "user", "content": "In about 100 words, explain how a lighthouse helps ships navigate."}],
               "max_tokens": 160, "temperature": 0, "stream": True, "stream_options": {"include_usage": True}}
    request = Request(f"http://127.0.0.1:{profile['runtime']['localTunnelPort']}/v1/chat/completions",
                      data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    started, first, content, usage = time.monotonic(), None, "", {}
    with urlopen(request, timeout=180) as response:
        for line in response:
            if not line.startswith(b"data: ") or line.strip() == b"data: [DONE]":
                continue
            event = json.loads(line[6:])
            delta = (event.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
            if delta:
                first = first if first is not None else time.monotonic() - started
                content += delta
            usage = event.get("usage") or usage
    elapsed = time.monotonic() - started
    if not content or first is None:
        raise RuntimeError("Streaming benchmark produced no actual text")
    result = {"atUtc": now().isoformat(), "request": payload, "responseText": content,
              "timeToFirstContentSeconds": round(first, 3), "totalSeconds": round(elapsed, 3), "usage": usage,
              "completionTokensPerTotalSecond": round(usage.get("completion_tokens", 0) / elapsed, 2),
              "note": "Single-request observed provider timing over SSH; not a formal throughput benchmark or wrapper streaming support."}
    write(run / "provider-timing.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in {"request", "responseText"}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["watchdog", "status", "inspect", "bootstrap", "logs", "tunnel", "ready", "evidence", "verify", "benchmark", "terminate"])
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--wrapper", action="store_true")
    args = parser.parse_args()
    run = core.evidence_directory(args.run_dir)
    state = state_at(run)
    if args.command == "watchdog":
        watchdog(run)
    elif args.command == "terminate":
        terminate(run)
    elif args.command == "status":
        pods = owned_pods(state)
        details = json.loads(core.cli("pod", "get", pods[0]["id"])) if pods else {}
        safe = {k: details.get(k) for k in ("id", "name", "desiredStatus", "runtimeStatus", "costPerHr", "publicIp", "portMappings")}
        safe["deadlineUtc"] = state["deadlineUtc"]
        safe["watchdog"] = core.read_json(run / "watchdog-heartbeat.json")
        write(run / "latest-status.json", safe)
        print(json.dumps(safe, indent=2))
    elif args.command == "inspect":
        result = ssh(run, "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader; findmnt -T /workspace; df -h /workspace; find /workspace -maxdepth 3 -type d -not -path '*/.*' | head -80; command -v uv; python3 --version")
        (run / "volume-inspection.txt").write_bytes(result)
        print(result.decode())
    elif args.command == "bootstrap":
        bootstrap(run)
    elif args.command == "ready":
        raise SystemExit(0 if ready(run) else 2)
    elif args.command == "logs":
        result = ssh(run, "tail -60 " + shlex.quote(remote_dir(run) + "/bootstrap.log"))
        print(result.decode(errors="replace"))
    elif args.command == "tunnel":
        profile = core.read_json(run / "profile.json")
        forwarding = f"127.0.0.1:{profile['runtime']['localTunnelPort']}:127.0.0.1:{profile['runtime']['port']}"
        conn = connection(run)
        command = conn[:-1] + ["-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=30", "-N", "-L", forwarding, conn[-1]]
        with (run / "tunnel.log").open("ab") as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        time.sleep(2)
        if child.poll() is not None:
            raise RuntimeError("SSH tunnel failed; inspect tunnel.log")
        write(run / "tunnel.json", {"pid": child.pid, "forwarding": forwarding, "atUtc": now().isoformat()})
        print("SSH tunnel ready on loopback port " + str(profile["runtime"]["localTunnelPort"]))
    elif args.command == "evidence":
        for name in ("validated-model-manifest.json", "runtime-packages.txt", "gpu.txt", "server-command.json"):
            (run / name).write_bytes(ssh(run, "cat " + shlex.quote(remote_dir(run) + "/" + name)))
        profile = core.read_json(run / "profile.json")
        actual = core.read_json(run / "validated-model-manifest.json")
        if actual["revision"] != profile["model"]["revision"] or actual["repository"] != profile["model"]["repository"]:
            raise RuntimeError("Remote model identity does not match the pinned profile")
        fingerprints = {name: hashlib.sha256((run / name).read_bytes()).hexdigest() for name in
                        ("profile.json", "expected-model-manifest.json", "validated-model-manifest.json", "runtime-packages.txt", "server-command.json")}
        actual_bootstrap = ssh(run, "cat " + shlex.quote(remote_dir(run) + "/prepare_runpod_model.py"))
        (run / "executed-bootstrap.py").write_bytes(actual_bootstrap)
        fingerprints["executed-bootstrap.py"] = hashlib.sha256(actual_bootstrap).hexdigest()
        private = core.read_json(run / "bootstrap-start.json")["privateKeyFile"]
        key = core.read_json(private)["apiKey"]
        log = ssh(run, "cat " + shlex.quote(remote_dir(run) + "/bootstrap.log")).decode(errors="replace").replace(key, "[REDACTED]")
        (run / "bootstrap-log.txt").write_text(log)
        write(run / "configuration-fingerprint.json", {"capturedAtUtc": now().isoformat(), "sha256": fingerprints,
              "modelFileCount": len(actual["files"]), "validatedModelBytes": sum(f["bytes"] for f in actual["files"])})
        print("Saved actual model hashes, runtime versions, GPU, and serving command locally.")
    elif args.command == "benchmark":
        benchmark(run)
    elif args.command == "verify":
        private = core.read_json(run / "bootstrap-start.json")["privateKeyFile"]
        os.environ["VERONICA_UPSTREAM_API_KEY"] = core.read_json(private)["apiKey"]
        profile = core.read_json(run / "profile.json")
        core.verify(profile, f"http://127.0.0.1:{8010 if args.wrapper else profile['runtime']['localTunnelPort']}/v1", run, args.wrapper)


if __name__ == "__main__":
    main()
