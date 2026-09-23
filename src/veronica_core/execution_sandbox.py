"""Local, bounded Docker execution for T2; never pulls images or starts a daemon.

The container sees source and arguments, never expected answers or host files.
Docker/its kernel remain trusted; this is not a proof against kernel exploits.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/execution-sandbox.json"
MEMORY = 256 * 1024 * 1024
PIDS = 32
OUTPUT_LIMIT = 1024 * 1024
INPUT_LIMIT = 256 * 1024

# No expected answers or pass/fail decisions exist in this worker. Its entire
# output is untrusted, strictly parsed and compared by the host below.
WORKER = r'''
import copy, json, sqlite3, sys
job = json.load(sys.stdin)
args = copy.deepcopy(job["args"])
before = copy.deepcopy(args)
conn = None
if job.get("setup"):
    setup = job["setup"]
    conn = sqlite3.connect(":memory:")
    conn.execute(setup["schema"])
    conn.executemany("INSERT INTO users (id, display_name) VALUES (?, ?)",
                     [(r["id"], r["display_name"]) for r in setup["rows"]])
    conn.commit()
scope = {"__name__": "candidate"}
try:
    exec(compile(job["source"], "candidate.py", "exec"), scope)
    fn = scope[job["function"]]
except BaseException as exc:
    result = {"phase": "load", "exception": type(exc).__name__}
else:
    try:
        value = fn(*([conn, *args] if job.get("inject_conn") else args))
        if hasattr(value, "fetchall") and callable(value.fetchall):
            value = value.fetchall()
        result = {"phase": "call", "value": value, "args_after": args}
    except BaseException as exc:
        result = {"phase": "call", "exception": type(exc).__name__, "args_after": args}
print(json.dumps(result, allow_nan=False))
'''

PROBE = r'''
import json, os, pathlib, socket
status = dict(line.split(":", 1) for line in pathlib.Path("/proc/self/status").read_text().splitlines() if ":" in line)
s = socket.socket(); s.settimeout(0.5)
try:
    s.connect(("1.1.1.1", 443)); network_blocked = False
except OSError:
    network_blocked = True
finally:
    s.close()
root_readonly = bool(os.statvfs("/").f_flag & os.ST_RDONLY)
root_write_blocked = False
try:
    pathlib.Path("/sandbox-probe").write_text("must fail")
except OSError:
    root_write_blocked = True
cg = pathlib.Path("/sys/fs/cgroup")
print(json.dumps({
    "network_blocked": network_blocked,
    "interfaces": sorted(p.name for p in pathlib.Path("/sys/class/net").iterdir()),
    "root_readonly": root_readonly, "root_write_blocked": root_write_blocked,
    "uid": os.getuid(), "pid": os.getpid(),
    "caps": int(status["CapEff"].strip(), 16),
    "no_new_privs": status["NoNewPrivs"].strip(),
    "seccomp": status["Seccomp"].strip(),
    "memory_max": (cg / "memory.max").read_text().strip(),
    "swap_max": (cg / "memory.swap.max").read_text().strip(),
    "pids_max": (cg / "pids.max").read_text().strip(),
    "cpu_max": (cg / "cpu.max").read_text().strip(),
    "docker_socket_absent": not pathlib.Path("/var/run/docker.sock").exists()
}))
'''


class SandboxError(RuntimeError):
    pass


def strict_json(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("nonfinite_json_number")
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite_json_number")
        return parsed
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite_float)


def equal(actual, expected) -> bool:
    # JSON booleans must never pass as integers, nor floats as integer counts.
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(equal(actual[k], expected[k]) for k in actual)
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(equal(a, b) for a, b in zip(actual, expected))
    return actual == expected


def score_observation(observation: dict, vector: dict) -> dict:
    row = {"id": vector["id"], "passed": False}
    if not isinstance(observation, dict) or observation.get("phase") != "call":
        return {**row, "error": "invalid_call_observation"}
    expected = vector["expect"]
    if "exception" in observation:
        allowed = {"phase", "exception", "args_after"}
        passed = (set(observation) == allowed and "raises" in expected
                  and isinstance(observation["exception"], str)
                  and observation["exception"] == expected["raises"])
    else:
        allowed = {"phase", "value", "args_after"}
        actual = observation.get("value")
        if "rows" in expected and isinstance(actual, list):
            actual = [[r["id"], r["display_name"]] if isinstance(r, dict) and set(r) == {"id", "display_name"} else r for r in actual]
        passed = set(observation) == allowed and "raises" not in expected and equal(actual, expected.get("equals", expected.get("rows")))
    if vector.get("assert_input_unchanged") and not equal(observation.get("args_after"), vector["args"]):
        passed = False
    return {**row, "passed": passed, "error": None if passed else "fixture_mismatch"}


def _docker(*args: str, timeout: float = 15) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, encoding="utf-8", timeout=timeout)


class DockerSandbox:
    def __init__(self, config_path: Path = DEFAULT_CONFIG):
        self.config = strict_json(Path(config_path).read_text(encoding="utf-8"))
        self.image = self.config.get("image", "")
        if not re.fullmatch(r"python@sha256:[0-9a-f]{64}", self.image):
            raise SandboxError("Pinned official Python image digest required")
        self.image_id = None
        self.attestation = None
        self.endpoint = None

    def _resolve_endpoint(self):
        endpoint = os.environ.get("DOCKER_HOST")
        if not endpoint or os.environ.get("DOCKER_CONTEXT"):
            result = _docker("context", "inspect", "--format", "{{.Endpoints.docker.Host}}")
            if result.returncode:
                raise SandboxError("docker_context_unavailable")
            endpoint = result.stdout.strip()
        if not endpoint or not endpoint.startswith(("unix:///", "npipe:////./pipe/")):
            raise SandboxError("remote_docker_endpoint_not_allowed")
        self.endpoint = endpoint

    def _environment(self):
        env = os.environ.copy()
        for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
            env.pop(key, None)
        return env

    def _command(self, *args):
        if not self.endpoint:
            raise SandboxError("local_endpoint_not_verified")
        return ["docker", "--host", self.endpoint, *args]

    def _call(self, *args, timeout=15):
        return subprocess.run(self._command(*args), env=self._environment(), capture_output=True,
                              text=True, encoding="utf-8", timeout=timeout)

    def _resolve_image(self):
        result = self._call("image", "inspect", self.image)
        if result.returncode:
            raise SandboxError("sandbox_image_or_daemon_unavailable")
        image = strict_json(result.stdout)[0]
        if image.get("Os") != "linux" or image.get("Config", {}).get("Volumes"):
            raise SandboxError("unsupported_image_configuration")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image.get("Id", "")):
            raise SandboxError("invalid_image_id")
        self.image_id = image["Id"]

    def _create_args(self, name: str, program: str) -> list[str]:
        return [
            "create", "--name", name, "--label", "veronica.execution-sandbox=1",
            "--pull", "never", "--network", "none", "--read-only",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true",
            "--pids-limit", str(PIDS), "--memory", str(MEMORY), "--memory-swap", str(MEMORY),
            "--cpus", "1", "--user", "65534:65534", "--ipc", "none",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16777216",
            "--workdir", "/tmp", "--no-healthcheck", "--log-driver", "none",
            "--ulimit", "nofile=64:64", "--ulimit", "core=0:0",
            "--entrypoint", "/usr/local/bin/python3", "-i", self.image_id,
            "-I", "-S", "-B", "-u", "-c", program,
        ]

    def _check_container(self, data: dict):
        host, config = data["HostConfig"], data["Config"]
        tests = [
            data.get("Image") == self.image_id, host.get("NetworkMode") == "none",
            host.get("ReadonlyRootfs") is True, host.get("Privileged") is False,
            host.get("CapDrop") == ["ALL"], not host.get("CapAdd"),
            "no-new-privileges=true" in (host.get("SecurityOpt") or []),
            not any("unconfined" in option for option in host.get("SecurityOpt") or []),
            host.get("PidsLimit") == PIDS, host.get("Memory") == MEMORY,
            host.get("MemorySwap") == MEMORY, host.get("NanoCpus") == 1_000_000_000,
            config.get("User") == "65534:65534", config.get("WorkingDir") == "/tmp",
            not host.get("Binds"), not host.get("Mounts"), not host.get("VolumesFrom"),
            not data.get("Mounts"), not host.get("Devices"), not host.get("DeviceRequests"),
            host.get("PidMode", "") in ("", "private"), host.get("IpcMode") == "none",
            host.get("RestartPolicy", {}).get("Name") in ("", "no"),
            host.get("LogConfig", {}).get("Type") == "none",
            set(host.get("Tmpfs") or {}) == {"/tmp"},
            config.get("Entrypoint") == ["/usr/local/bin/python3"],
        ]
        if not all(tests):
            raise SandboxError("container_policy_mismatch")

    def _execute(self, program: str, payload: dict, timeout: float) -> dict:
        if not self.image_id:
            raise SandboxError("image_not_resolved")
        if not math.isfinite(timeout) or not 0 < timeout <= 60:
            raise ValueError("timeout must be between 0 and 60 seconds")
        raw = json.dumps(payload, allow_nan=False).encode("utf-8")
        if len(raw) > INPUT_LIMIT:
            raise ValueError("sandbox_input_too_large")
        name = "veronica-eval-" + uuid.uuid4().hex
        outcome = {"ok": False, "error": "not_started", "cleanup_verified": False, "container": name}
        proc = None
        try:
            created = self._call(*self._create_args(name, program))
            if created.returncode:
                raise SandboxError("container_create_failed")
            inspected = self._call("inspect", name)
            if inspected.returncode:
                raise SandboxError("container_inspect_failed")
            self._check_container(strict_json(inspected.stdout)[0])
            with tempfile.TemporaryDirectory(prefix="veronica-sandbox-io-") as directory:
                path = Path(directory)
                (path / "input").write_bytes(raw)
                with (path / "input").open("rb") as stdin, (path / "output").open("wb") as stdout, (path / "error").open("wb") as stderr:
                    proc = subprocess.Popen(self._command("start", "--attach", "--interactive", name),
                                            env=self._environment(), stdin=stdin, stdout=stdout, stderr=stderr)
                    started = time.monotonic()
                    violation = None
                    while proc.poll() is None:
                        if sum((path / f).stat().st_size for f in ("output", "error")) > OUTPUT_LIMIT:
                            violation = "output_limit"
                            break
                        if time.monotonic() - started > timeout:
                            violation = "timeout"
                            break
                        time.sleep(0.02)
                    if violation:
                        outcome["error"] = violation
                    else:
                        with (path / "output").open("rb") as output_file:
                            data = output_file.read(OUTPUT_LIMIT + 1)
                        if len(data) > OUTPUT_LIMIT or (path / "error").stat().st_size > OUTPUT_LIMIT:
                            outcome["error"] = "output_limit"
                        elif proc.returncode:
                            outcome["error"] = "worker_failed"
                            with (path / "error").open("rb") as error_file:
                                outcome["worker_stderr"] = error_file.read(2048).decode("utf-8", errors="replace")
                        else:
                            try:
                                outcome.update(ok=True, error=None, observation=strict_json(data.decode("utf-8")))
                            except (ValueError, UnicodeError, RecursionError):
                                outcome["error"] = "invalid_worker_output"
                # Handles are closed before Windows removes temporary files.
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, SandboxError) as exc:
            outcome["error"] = str(exc) if isinstance(exc, SandboxError) else type(exc).__name__
        finally:
            if proc is not None and proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            # Exact randomly allocated name only; never prune unrelated resources.
            try:
                removed = self._call("rm", "--force", "--volumes", name)
                outcome["cleanup_verified"] = removed.returncode == 0 and name in removed.stdout
            except (OSError, subprocess.SubprocessError):
                outcome["cleanup_verified"] = False
            if not outcome["cleanup_verified"]:
                outcome.update(ok=False, error="cleanup_unverified")
        return outcome

    def verify(self) -> dict:
        self.attestation = {"verified": False, "backend": "docker", "image": self.image}
        try:
            self._resolve_endpoint()
            self.attestation["endpoint"] = self.endpoint
            self._resolve_image()
            result = self._execute(PROBE, {}, 10)
            obs = result.get("observation", {})
            quota, period = obs.get("cpu_max", "0 1").split()
            checks = [
                result["ok"], obs.get("network_blocked") is True,
                obs.get("interfaces") == ["lo"], obs.get("root_readonly") is True,
                obs.get("root_write_blocked") is True, obs.get("uid") == 65534,
                obs.get("pid") == 1, obs.get("caps") == 0, obs.get("no_new_privs") == "1",
                obs.get("seccomp") == "2", obs.get("memory_max") == str(MEMORY),
                obs.get("swap_max") == "0", obs.get("pids_max") == str(PIDS),
                int(quota) == int(period), obs.get("docker_socket_absent") is True,
            ]
            self.attestation.update(verified=all(checks), image_id=self.image_id, probe=result)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, SandboxError) as exc:
            self.attestation["error"] = str(exc) if isinstance(exc, SandboxError) else type(exc).__name__
        return copy.deepcopy(self.attestation)

    def run_fixture(self, source: str, fixture: dict, timeout: float = 8) -> dict:
        if not self.attestation or self.attestation.get("verified") is not True:
            return {"ok": False, "error": "isolation_unverified", "vectors": []}
        rows = []
        executions = []
        for vector in fixture["vectors"]:
            # Do not forward fixture IDs, expected values, or pass flags.
            payload = {"source": source, "function": fixture["function"], "args": vector["args"],
                       "setup": fixture.get("setup"), "inject_conn": bool(vector.get("inject_conn"))}
            outcome = self._execute(WORKER, payload, timeout)
            executions.append({k: outcome[k] for k in ("ok", "error", "cleanup_verified", "container")})
            row = score_observation(outcome["observation"], vector) if outcome["ok"] else {
                "id": vector["id"], "passed": False, "error": outcome["error"]}
            rows.append(row)
            if not outcome["cleanup_verified"]:
                self.attestation["verified"] = False
                break
        return {"ok": len(rows) == len(fixture["vectors"]) and all(e["ok"] for e in executions),
                "error": next((e["error"] for e in executions if not e["ok"]), None),
                "vectors": rows, "executions": executions,
                "source_sha256": hashlib.sha256(source.encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = DockerSandbox(args.config).verify()
    except (ValueError, OSError, SandboxError) as exc:
        result = {"verified": False, "error": str(exc)}
    result["foundation_qualified"] = False
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["verified"] else 2)


if __name__ == "__main__":
    main()
