"""Reusable RunPod preflight, provenance capture, and real-inference verification.

No credentials or spending approval live in the reusable profile. Native timers
are unavailable; creation requires explicit per-run supervised authorization.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from http.client import RemoteDisconnected
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "config/runpod-core.json"
VERONICA_POD_PREFIXES = ("veronica-core-", "veronica-t2-")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def fetch(url, payload=None, key=None):
    headers = {"User-Agent": "VeronicaCore/0.1", "Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urlopen(request, timeout=180) as response:
        return response.read()


# A single dropped SSH tunnel packet on a real-world (often home) network
# connection should not throw away an entire authorized, paid Pod. Only retry
# transient connection-level failures; a real HTTP error status (auth
# rejection, 4xx/5xx) is not retried here because it is not a network blip.
TRANSIENT_CONNECTION_ERRORS = (RemoteDisconnected, ConnectionResetError, ConnectionAbortedError, TimeoutError, URLError)


def fetch_with_retries(url, payload=None, key=None, attempts=3, backoff_seconds=3):
    last_error = None
    for attempt in range(attempts):
        try:
            return fetch(url, payload=payload, key=key)
        except HTTPError:
            # A real HTTP status (auth rejection, 4xx/5xx) is not a network
            # blip; HTTPError is a URLError subclass, so it must be checked
            # first and re-raised immediately, not retried.
            raise
        except TRANSIENT_CONNECTION_ERRORS as error:
            last_error = error
            if attempt + 1 < attempts:
                print(f"Transient connection error ({type(error).__name__}); retrying in {backoff_seconds}s "
                      f"(attempt {attempt + 2}/{attempts})", flush=True)
                time.sleep(backoff_seconds)
    raise last_error


def cli(*args):
    executable = shutil.which("runpodctl") or str(Path.home() / ".local/bin/runpodctl")
    command = [executable, *args]
    if os.name == "nt":
        # No nested shell or secret interpolation. WSL owns RunPod authentication.
        command = ["wsl.exe", "-e", "bash", "-lc", 'exec runpodctl "$@"', "veronica-runpod", *args]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "RunPod command failed")
    return result.stdout


def profile_at(path):
    profile = read_json(path)
    model, pod = profile["model"], profile["pod"]
    if profile["publicAlias"] != "Veronica":
        raise ValueError("Public alias must remain Veronica")
    for field in ("revision", "controlRevision"):
        if not re.fullmatch(r"[0-9a-f]{40}", model[field]):
            raise ValueError(f"{field} must be an immutable 40-character commit")
    if not re.fullmatch(r"[\w./-]+@sha256:[0-9a-f]{64}", pod["image"]):
        raise ValueError("Container image must use an immutable SHA-256 digest")
    if pod.get("namePrefix") not in VERONICA_POD_PREFIXES:
        raise ValueError("Pod name prefix must identify an approved Veronica workflow")
    directory = PurePosixPath(model["directory"])
    if ".." in directory.parts or not directory.is_relative_to("/workspace/veronica-core/models"):
        raise ValueError("Model directory must be inside /workspace/veronica-core/models")
    validate_profile_safety(profile)
    if pod["ports"] != ["22/tcp"] or profile["runtime"]["host"] != "127.0.0.1":
        raise ValueError("This development runtime must expose SSH only and serve on Pod loopback")
    return profile


def validate_profile_safety(profile):
    """Validate saved resource policy before any inventory or paid operation."""
    pod, safety = profile["pod"], profile["safety"]
    if type(pod.get("gpuCount")) is not int or pod["gpuCount"] != 1:
        raise ValueError("This first-chat workflow supports exactly one GPU")
    if pod.get("gpuTypeId") != "NVIDIA A100-SXM4-80GB":
        raise ValueError("This startup profile is restricted to one NVIDIA A100-SXM4-80GB")
    maximum = safety.get("maximumHourlyUsd")
    if isinstance(maximum, bool) or not isinstance(maximum, (int, float, Decimal)) or not math.isfinite(maximum) or maximum <= 0:
        raise ValueError("The saved hourly spending ceiling must be finite and positive")
    if safety.get("requirePerRunApproval") is not True or safety.get("allowAutomaticReplacementPod") is not False:
        raise ValueError("Every new Pod requires fresh approval and automatic replacement must remain disabled")
    if safety.get("defaultShutdownMode") != "supervised-with-local-backup":
        raise ValueError("The configured shutdown mode must remain supervised-with-local-backup")
    for fallback in pod.get("gpuFallbacks", []):
        if not isinstance(fallback.get("gpuTypeId"), str) or not fallback["gpuTypeId"]:
            raise ValueError("Each GPU fallback requires a non-empty gpuTypeId")
        if fallback.get("cloudType") not in ("SECURE", "COMMUNITY"):
            raise ValueError("Each GPU fallback cloudType must be SECURE or COMMUNITY")
        if type(fallback.get("minMemoryGb")) is not int or fallback["minMemoryGb"] < 80:
            raise ValueError("Each GPU fallback must require at least 80 GB VRAM to match the primary GPU class")
        cap = fallback.get("maxHourlyUsd")
        if isinstance(cap, bool) or not isinstance(cap, (int, float, Decimal)) or not math.isfinite(cap) or cap <= 0 or cap > maximum:
            raise ValueError("Each GPU fallback's own price cap must be finite, positive, and within the saved ceiling")
    return safety


def evidence_directory(value):
    path = Path(value).resolve()
    if not path.is_relative_to((ROOT / "runs").resolve()) or path == ROOT / "runs":
        raise ValueError("Evidence must go in a named run directory under this project's runs/")
    return path


def prepare(profile, output):
    output = evidence_directory(output)
    if (output / "expected-model-manifest.json").exists():
        raise ValueError("This run already has a manifest; preserve it and use a new run directory")
    model = profile["model"]
    for label, repo, revision in (
        ("candidate", model["repository"], model["revision"]),
        ("control", model["controlRepository"], model["controlRevision"]),
    ):
        url = f"https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true"
        metadata = json.loads(fetch(url))
        if metadata["sha"] != revision:
            raise ValueError("Hub returned a different revision")
        destination = output / "provenance" / label
        destination.mkdir(parents=True, exist_ok=True)
        save_json(destination / "hub-metadata.json", metadata)
        for filename in ("README.md", "LICENSE", "config.json"):
            content = fetch(f"https://huggingface.co/{repo}/resolve/{revision}/{filename}")
            (destination / filename).write_bytes(content)
        if label == "candidate":
            manifest = []
            for file in metadata["siblings"]:
                name = file["rfilename"]
                if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
                    raise ValueError("Unsafe Hub filename")
                manifest.append({"path": name, "bytes": file["size"], "sha256": file.get("lfs", {}).get("sha256"), "gitBlob": file["blobId"]})
            save_json(output / "expected-model-manifest.json", {
                "repository": repo, "revision": revision, "files": manifest,
                "expectedBytes": sum(f["bytes"] for f in manifest),
            })
    save_json(output / "profile.json", profile)
    print(f"Saved pinned model cards, licenses, configuration, and expected hashes: {output}")


def duration_policy(profile):
    safety = profile["safety"]
    presets = safety.get("presetDurationMinutes")
    default = safety.get("defaultDurationMinutes")
    maximum = safety.get("maximumCustomDurationMinutes")
    if presets != [60, 120, 180]:
        raise ValueError("Duration presets must be exactly one, two, and three hours")
    if default != presets[0] or default != 60:
        raise ValueError("The default RunPod duration must remain exactly one hour")
    if not isinstance(maximum, int) or maximum < presets[-1]:
        raise ValueError("Custom duration maximum must include the three-hour preset")
    return {"default": default, "presets": presets, "maximum": maximum}


def validate_limits(hourly, minutes, *, maximum_minutes=1440, maximum_hourly_usd=None):
    if isinstance(hourly, bool) or not isinstance(hourly, (int, float, Decimal)) or not math.isfinite(hourly) or hourly <= 0:
        raise ValueError("Supply a finite, positive per-run hourly spending ceiling")
    if maximum_hourly_usd is not None and hourly > maximum_hourly_usd:
        raise ValueError(f"Per-run hourly approval exceeds the saved ${maximum_hourly_usd:g}/hour ceiling")
    if type(minutes) is not int or not 1 <= minutes <= maximum_minutes:
        raise ValueError(f"Supply a duration of 1–{maximum_minutes} minutes for this development workflow")


def price_within_limit(value, maximum):
    """Treat missing, malformed, nonpositive and nonfinite provider prices as unsafe."""
    if value is None or isinstance(value, bool):
        return False
    try:
        price = Decimal(str(value))
        ceiling = Decimal(str(maximum))
        return price.is_finite() and ceiling.is_finite() and Decimal(0) < price <= ceiling
    except (InvalidOperation, ValueError):
        return False


def choose_duration(profile, input_func=input, output_func=print):
    """Ask for the fixed shutdown window; this never creates a paid resource."""
    policy = duration_policy(profile)
    one, two, three = policy["presets"]
    output_func("Choose the RunPod termination window before any paid startup:")
    output_func(f"  1. {one // 60} hour (default)")
    output_func(f"  2. {two // 60} hours")
    output_func(f"  3. {three // 60} hours")
    output_func("  4. Custom number of hours (up to 24)")
    while True:
        choice = input_func("Selection [1]: ").strip() or "1"
        if choice in {"1", "2", "3"}:
            return policy["presets"][int(choice) - 1]
        if choice == "4":
            try:
                hours = Decimal(input_func("Hours: ").strip())
                minutes_decimal = hours * 60
                if not hours.is_finite() or hours <= 0 or minutes_decimal != minutes_decimal.to_integral_value():
                    raise InvalidOperation
                minutes = int(minutes_decimal)
                validate_limits(1, minutes, maximum_minutes=policy["maximum"])
                return minutes
            except (InvalidOperation, ValueError):
                output_func("Enter a positive number of hours, in whole-minute increments, up to 24 hours.")
                continue
        output_func("Choose 1, 2, 3, or 4.")


def preflight(profile, hourly, minutes, *, supervised=False):
    safety = validate_profile_safety(profile)
    validate_limits(hourly, minutes, maximum_minutes=duration_policy(profile)["maximum"],
                    maximum_hourly_usd=safety["maximumHourlyUsd"])
    pod = profile["pod"]
    # Successful inventory calls establish authentication without printing account info.
    volumes = json.loads(cli("network-volume", "get", pod["networkVolumeId"]))
    gpus = json.loads(cli("gpu", "list", "--include-unavailable"))
    pods = json.loads(cli("pod", "list", "--all"))
    keys = json.loads(cli("ssh", "list-keys"))
    blockers = []
    if volumes.get("dataCenterId") != pod["dataCenterId"]:
        blockers.append("Network volume and requested GPU data center do not match")
    if pod.get("networkVolumeSizeGb") and volumes.get("size") != pod["networkVolumeSizeGb"]:
        blockers.append("Persistent-volume allowance changed; review the profile before downloading")
    # Try the primary GPU first, then ordered fallbacks, each within its own price cap.
    candidates = [{"gpuTypeId": pod["gpuTypeId"], "cloudType": pod["cloudType"], "maxHourlyUsd": hourly, "isPrimary": True}]
    candidates += [{**fallback, "isPrimary": False} for fallback in pod.get("gpuFallbacks", [])]
    considered = []
    selected = None
    for candidate in candidates:
        gpu = next((g for g in gpus if g.get("gpuId") == candidate["gpuTypeId"]), {})
        dc = next((d for d in gpu.get("dataCenterAvailability", []) if d.get("dataCenterId") == pod["dataCenterId"]), {})
        price_field = "securePricePerHr" if candidate["cloudType"] == "SECURE" else "communityPricePerHr"
        price = gpu.get(price_field)
        stock = str(dc.get("stockStatus", "none")).lower()
        has_stock = bool(dc) and stock != "none"
        price_ok = price_within_limit(price, candidate["maxHourlyUsd"])
        entry = {"gpuTypeId": candidate["gpuTypeId"], "cloudType": candidate["cloudType"], "isPrimary": candidate["isPrimary"],
                  "stock": dc.get("stockStatus"), "priceUsd": price, "priceCapUsd": candidate["maxHourlyUsd"],
                  "hasStock": has_stock, "priceOk": price_ok, "selected": False}
        if candidate.get("reliabilityNote"):
            entry["reliabilityNote"] = candidate["reliabilityNote"]
        if selected is None and has_stock and price_ok:
            entry["selected"] = True
            selected = {**candidate, "listedHourlyUsd": price, "stock": dc.get("stockStatus")}
        considered.append(entry)
    # A fallback selection is informational (surfaced via usedFallbackGpu/reliabilityNote
    # below), not a blocker: it still satisfies stock and its own approved price cap.
    if selected is None:
        blockers.append("Requested GPU is unavailable in the volume data center, and no configured fallback GPU has stock within its price cap")
    if any(p.get("name", "").startswith(VERONICA_POD_PREFIXES) for p in pods):
        blockers.append("A Veronica Pod already exists; inspect it instead of creating another")
    if not keys.get("keys"):
        blockers.append("No registered SSH key")
    create_help = cli("pod", "create", "--help")
    # Presence alone was not proof: old versions advertised a timer that never fired.
    if not supervised and (profile["safety"]["terminationGuard"] != "verified-platform-timer" or "--terminate-after" not in create_help):
        blockers.append("Automatic termination is unverified/unavailable (runpodctl#330); paid creation is blocked")
    result = {
        "checkedAtUtc": datetime.now(timezone.utc).isoformat(),
        "cliVersion": cli("version").strip(), "volumeId": volumes["id"],
        "volumeSizeGb": volumes.get("size"),
        "dataCenterId": pod["dataCenterId"], "requestedGpuTypeId": pod["gpuTypeId"],
        "gpu": selected["gpuTypeId"] if selected else pod["gpuTypeId"],
        "gpuTypeId": selected["gpuTypeId"] if selected else pod["gpuTypeId"],
        "cloudType": selected["cloudType"] if selected else pod["cloudType"],
        "usedFallbackGpu": bool(selected and not selected["isPrimary"]),
        "consideredGpus": considered,
        "listedHourlyUsd": selected["listedHourlyUsd"] if selected else None,
        "stock": selected["stock"] if selected else "none",
        "requestedLimitUsd": hourly, "savedMaximumHourlyUsd": safety["maximumHourlyUsd"],
        "gpuCount": pod["gpuCount"], "requestedDurationMinutes": minutes,
        "approvalIsReusable": False, "podCount": len(pods), "blockers": blockers,
        "shutdownMode": "supervised-with-local-backup" if supervised else "platform-timer-required",
        "platformDeadlineEnforced": False,
        "safeToCreate": not blockers,
    }
    if selected and not selected["isPrimary"]:
        result["reliabilityNote"] = next((c.get("reliabilityNote") for c in candidates if c["gpuTypeId"] == selected["gpuTypeId"]), None)
    return result


def verify(profile, base_url, output, wrapper=False):
    # The pinned development runtime is intentionally reachable only over loopback/SSH.
    if not re.fullmatch(r"http://(127\.0\.0\.1|localhost):[0-9]+/v1", base_url):
        raise ValueError("Use a loopback URL: the local wrapper or the authenticated SSH tunnel")
    output = evidence_directory(output)
    key = os.environ.get("VERONICA_UPSTREAM_API_KEY")
    results = {"baseUrl": base_url, "tests": [], "modelIdentityRequiresPodEvidence": True,
               "automatedChecks": "Nonempty text and recall substring presence only; semantic correctness and action-truthfulness require manual review."}
    if not wrapper:
        if not key:
            raise ValueError("The direct provider smoke test requires this run's upstream key")
        try:
            fetch_with_retries(base_url + "/models")
        except HTTPError as error:
            if error.code not in (401, 403):
                raise
            results["unauthenticatedModelsStatus"] = error.code
        else:
            raise RuntimeError("Direct model endpoint accepted an unauthenticated request")
    models = json.loads(fetch_with_retries(base_url + "/models", key=key))
    results["advertisedModels"] = models
    if not any(m.get("id") == profile["publicAlias"] for m in models.get("data", [])):
        raise RuntimeError("Expected Veronica model alias was not advertised")
    turns = [{"role": "user", "content": "Hello Veronica. My name is Raine. For this conversation remember the phrase copper lantern. Briefly introduce yourself."}]
    cases = [
        ("introduction", "chat", None),
        ("conversation-context", "chat", "What is my name, and what exact two-word phrase did I ask you to remember?"),
        ("creative", "creative", "Write a four-sentence scene in which a lighthouse keeper discovers a star in a jar."),
        ("coding", "coding", "Write a Python is_even(n) function and three assert examples. Do not use external libraries."),
        ("reasoning", "deep-reasoning", "A box has 3 red and 2 blue balls. Two are drawn without replacement. What is the probability both are red? Give the fraction and a brief explanation."),
    ]
    try:
        for name, mode, prompt in cases:
            if prompt is not None:
                turns.append({"role": "user", "content": prompt})
            payload = {"model": profile["publicAlias"], "messages": list(turns), "max_tokens": 384, "temperature": 0.4, "stream": False}
            if wrapper:
                payload["veronica_mode"] = mode
            start = time.monotonic()
            response = json.loads(fetch_with_retries(base_url + "/chat/completions", payload, key))
            content = response["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("No actual assistant text was generated")
            passed = name != "conversation-context" or ("raine" in content.lower() and "copper lantern" in content.lower())
            results["tests"].append({"name": name, "seconds": round(time.monotonic()-start, 3), "request": payload, "response": response, "basicCheckPassed": passed})
            turns.append({"role": "assistant", "content": content})
            save_json(output / ("wrapper-smoke.json" if wrapper else "provider-smoke.json"), results)
            print(f"{name}: generated {len(content)} characters in {results['tests'][-1]['seconds']}s", flush=True)
        results["basicSmokePassed"] = all(t["basicCheckPassed"] for t in results["tests"])
        results["capabilityQualification"] = "pending; writing/code/reasoning require separate review"
    finally:
        save_json(output / ("wrapper-smoke.json" if wrapper else "provider-smoke.json"), results)
    if not results["basicSmokePassed"]:
        raise RuntimeError("Context recall check failed; inspect saved response")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "preflight", "select-duration", "start", "verify", "terminate"])
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--run-dir")
    parser.add_argument("--max-hourly-usd", type=float)
    parser.add_argument("--duration-minutes", type=int)
    parser.add_argument("--base-url", default="http://127.0.0.1:18000/v1")
    parser.add_argument("--wrapper", action="store_true")
    parser.add_argument("--pod-id")
    parser.add_argument("--supervised", action="store_true")
    parser.add_argument("--approval-file")
    parser.add_argument("--ssh-key")
    args = parser.parse_args()
    profile = profile_at(args.profile)
    if args.command in {"prepare", "verify"} and not args.run_dir:
        parser.error("--run-dir is required")
    if args.command == "prepare":
        prepare(profile, args.run_dir)
    elif args.command == "select-duration":
        minutes = choose_duration(profile)
        print(json.dumps({"durationMinutes": minutes, "durationHours": minutes / 60,
                          "defaultDurationMinutes": duration_policy(profile)["default"],
                          "note": "No Pod was created. A fresh approval remains required."}, indent=2))
    elif args.command in {"preflight", "start"}:
        if args.command == "start" and args.supervised:
            if not args.run_dir or not args.approval_file or not args.ssh_key:
                parser.error("Supervised start requires --run-dir, --approval-file, and --ssh-key")
            from supervised_runpod import start
            start(profile, evidence_directory(args.run_dir), Path(args.approval_file), Path(args.ssh_key))
            return
        result = preflight(profile, args.max_hourly_usd, args.duration_minutes, supervised=args.supervised)
        if args.run_dir:
            dest = evidence_directory(args.run_dir) / f"preflight-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
            save_json(dest, result)
        print(json.dumps(result, indent=2))
        if args.command == "start":
            # Fail closed even if someone flips a profile field. A new deployment
            # adapter must be reviewed and tested when timer enforcement is available.
            raise RuntimeError("No Pod created: deployment awaits a verified termination mechanism. See docs/STARTING-PROCEDURE.md")
    elif args.command == "verify":
        verify(profile, args.base_url, args.run_dir, args.wrapper)
    elif args.command == "terminate":
        if not args.pod_id or not re.fullmatch(r"[a-z0-9]+", args.pod_id):
            parser.error("An exact --pod-id is required")
        pod = json.loads(cli("pod", "get", args.pod_id))
        if not pod.get("name", "").startswith(profile["pod"]["namePrefix"]):
            raise ValueError("Pod is not identified as this workflow's resource")
        cli("pod", "delete", args.pod_id)
        remaining = json.loads(cli("pod", "list", "--all"))
        if any(p["id"] == args.pod_id for p in remaining):
            raise RuntimeError("Termination not confirmed; inspect the Pod")
        print(f"Confirmed Pod {args.pod_id} is absent. Network volume retained.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
