"""Offline installed-foundation baseline protocol and evidence auditor.

This module never starts a model, spends money, downloads weights, or qualifies a
foundation automatically.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
from typing import Any

from .evaluation import fingerprint, read_json, read_jsonl, validate_suite


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = ROOT / "config" / "foundation-baseline-qualification.json"
JSON_STATUS_GROUPS = ("executableCodeReports", "longContextReports", "nativeToolReports")


def _supplemental_status_issues(name: str, path: Path, label: str) -> list[str]:
    if name not in JSON_STATUS_GROUPS or path.suffix.lower() != ".json":
        return []
    try:
        payload = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return [f"Unreadable supplemental JSON: {label}"]
    if isinstance(payload, dict) and "status" in payload and payload["status"] != "collected_pass":
        return [f"Supplemental {name} status is {payload['status']}, not collected_pass: {label}"]
    return []


def _project_path(value: str, root: Path = ROOT) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes project root: {value}")
    return path


def _foundation(registry: dict) -> dict:
    foundation = registry.get("foundation")
    if not isinstance(foundation, dict):
        raise ValueError("Model registry requires one foundation record")
    if foundation.get("id") != registry.get("installedFoundationId"):
        raise ValueError("Installed foundation id does not match the foundation record")
    return foundation


def required_matrix(protocol: dict, foundation_id: str) -> set[tuple[str, str]]:
    tracks = protocol.get("tracks", [])
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("Protocol requires at least one baseline track")
    return {(foundation_id, track["id"]) for track in tracks}


def validate_protocol(protocol_path: Path = DEFAULT_PROTOCOL, root: Path = ROOT) -> dict:
    protocol = read_json(protocol_path)
    registry_path = _project_path(protocol.get("modelRegistry", ""), root)
    registry = read_json(registry_path)
    issues: list[str] = []

    if protocol.get("schemaVersion") != 2 or not protocol.get("protocolId"):
        issues.append("Protocol requires schemaVersion 2 and protocolId")
    if protocol.get("status") != "frozen_before_live_runs":
        issues.append("Protocol must be frozen before collecting baseline outputs")
    if registry.get("selectionStatus") != "benchmark_required":
        issues.append("Registry must remain benchmark_required until a signed qualification decision exists")
    try:
        foundation = _foundation(registry)
    except ValueError as exc:
        foundation = {}
        issues.append(str(exc))
    foundation_id = foundation.get("id")
    if protocol.get("foundationId") != foundation_id:
        issues.append("Protocol foundationId does not match the installed foundation")

    suite_spec = protocol.get("suite", {})
    suite_path = _project_path(suite_spec.get("path", ""), root)
    try:
        suite = read_json(suite_path)
        validate_suite(suite)
        actual_calls = sum(len(case["turns"]) for case in suite["cases"])
        if fingerprint(suite_path) != suite_spec.get("sha256"):
            issues.append("Frozen suite SHA-256 does not match the current file")
        if len(suite["cases"]) != suite_spec.get("caseCount"):
            issues.append("Frozen suite case count does not match")
        if actual_calls != suite_spec.get("completionCallsPerRepeat"):
            issues.append("Frozen suite completion-call count does not match")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        issues.append(f"Suite validation failed: {type(exc).__name__}")
        suite = {}

    snapshot_files = 0
    profile: dict[str, Any] = {}
    snapshot_value = foundation.get("provenanceSnapshot")
    if not snapshot_value:
        issues.append("Installed foundation has no provenance snapshot path")
    else:
        snapshot = _project_path(snapshot_value, root)
        for filename in ("README.md", "LICENSE"):
            path = snapshot / filename
            if not path.is_file():
                issues.append(f"Installed foundation is missing pinned {filename}")
            else:
                snapshot_files += 1
        license_path = snapshot / "LICENSE"
        if license_path.is_file():
            license_text = license_path.read_text(encoding="utf-8-sig", errors="replace")
            if "Apache License" not in license_text or "Version 2.0" not in license_text:
                issues.append("Installed foundation license snapshot is not recognizable as Apache-2.0")

    profile_value = foundation.get("runpodProfile")
    if not profile_value:
        issues.append("Installed foundation has no RunPod baseline profile")
    else:
        try:
            profile = read_json(_project_path(profile_value, root))
            model = profile.get("model", {})
            if model.get("repository") != foundation.get("repository") or model.get("revision") != foundation.get("revision"):
                issues.append("RunPod baseline profile identity does not match the registry")
            for key in ("licenseDeclared", "architecture", "weightFormat", "quantization", "weightsModified"):
                if model.get(key) != foundation.get(key):
                    issues.append(f"RunPod baseline profile {key} does not match installed-foundation provenance")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            issues.append(f"Installed foundation RunPod profile is unreadable: {type(exc).__name__}")

    runtime = protocol.get("baselineRuntime", {})
    for key in ("gpuType", "vllmVersion", "transformersVersion", "dtype", "maxModelLen", "surface"):
        if runtime.get(key) in (None, ""):
            issues.append(f"Baseline runtime is missing {key}")
    if runtime.get("surface") != "direct" or runtime.get("wrapperPersona") is not False:
        issues.append("Foundation baseline must use the direct, persona-free surface")
    if runtime.get("servedModelAlias") != registry.get("publicAlias"):
        issues.append("Baseline runtime does not serve the configured public alias")
    if profile:
        profile_runtime, pod, safety = profile.get("runtime", {}), profile.get("pod", {}), profile.get("safety", {})
        matched = {
            "vllmVersion": runtime.get("vllmVersion"),
            "transformersVersion": runtime.get("transformersVersion"),
            "dtype": runtime.get("dtype"),
            "maxModelLen": runtime.get("maxModelLen"),
            "maxNumSeqs": runtime.get("maxNumSeqs"),
        }
        for key, value in matched.items():
            if profile_runtime.get(key) != value:
                issues.append(f"Baseline profile {key} differs from the frozen runtime")
        if pod.get("gpuTypeId") != runtime.get("gpuType") or pod.get("gpuCount") != runtime.get("gpuCount"):
            issues.append("Baseline profile GPU differs from the frozen runtime")
        if safety.get("maximumHourlyUsd") != runtime.get("maximumHourlyUsd"):
            issues.append("Baseline profile spending ceiling differs from the frozen runtime")
        if profile_runtime.get("serverArguments") != protocol.get("serverArguments"):
            issues.append("Baseline profile server arguments differ from the frozen protocol")

    try:
        matrix = required_matrix(protocol, str(foundation_id))
    except (ValueError, KeyError, TypeError) as exc:
        issues.append(str(exc))
        matrix = set()
    case_ids = {case["id"] for case in suite.get("cases", [])}
    calls_by_id = {case["id"]: len(case["turns"]) for case in suite.get("cases", [])}
    seen_tracks: set[str] = set()
    for track in protocol.get("tracks", []):
        track_id = track.get("id")
        if not track_id or track_id in seen_tracks:
            issues.append("Baseline tracks require unique nonempty ids")
        seen_tracks.add(track_id)
        selected = track.get("caseIds")
        selected_ids = case_ids if selected == "all" else set(selected or [])
        if not selected_ids or selected_ids - case_ids:
            issues.append(f"Track {track_id} has missing or unknown case ids")
            continue
        calls = sum(calls_by_id[case_id] for case_id in selected_ids)
        if calls != track.get("completionCallsPerRepeat"):
            issues.append(f"Track {track_id} completion-call count does not match its selected cases")

    return {
        "protocol_id": protocol.get("protocolId"),
        "protocol_ready": not issues,
        "issues": issues,
        "registered_foundations": 1 if foundation else 0,
        "baseline_tracks": len(protocol.get("tracks", [])),
        "required_foundation_track_runs": len(matrix),
        "pinned_card_and_license_files": snapshot_files,
        "suite_sha256": suite_spec.get("sha256"),
        "paid_compute_started": False,
        "foundation_qualified": False,
    }


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction + 0.5)))
    return round(ordered[index], 3)


def _audit_run(protocol: dict, foundation: dict, track: dict, item: dict, root: Path) -> dict:
    issues: list[str] = []
    run_dir = _project_path(item.get("runDir", ""), root)
    reviews_path = _project_path(item.get("reviews", ""), root)
    try:
        manifest = read_json(run_dir / "manifest.json")
        records = read_jsonl(run_dir / "results.jsonl")
        reviews = read_jsonl(reviews_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"eligible": False, "issues": [f"Unreadable run evidence: {type(exc).__name__}"]}

    suite = protocol["suite"]
    expected_calls = track["completionCallsPerRepeat"] * track["repeats"]
    expected_thinking = "enabled" if track["enableThinking"] else "disabled"
    expected = {
        "suite_sha256": suite["sha256"],
        "surface": protocol["baselineRuntime"]["surface"],
        "mode": track["mode"],
        "temperature": track["temperature"],
        "top_p": track["topP"],
        "thinking": expected_thinking,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            issues.append(f"Manifest {key} differs from protocol")
    identity = manifest.get("identity", {})
    if identity.get("repository") != foundation.get("repository") or identity.get("revision") != foundation.get("revision"):
        issues.append("Manifest model identity does not match the pinned installed foundation")
    plan = manifest.get("plan", {})
    if plan.get("completion_calls") != expected_calls or plan.get("repeats") != track["repeats"]:
        issues.append("Manifest call/repeat plan differs from protocol")
    if plan.get("max_tokens_per_call") != track["maxTokens"]:
        issues.append("Manifest max tokens differs from protocol")
    if track.get("caseIds") == "all":
        frozen_suite = read_json(_project_path(protocol["suite"]["path"], root))
        expected_case_ids = {case.get("id") for case in frozen_suite.get("cases", [])}
    else:
        expected_case_ids = set(track.get("caseIds", []))
    if set(plan.get("case_ids", [])) != expected_case_ids:
        issues.append("Manifest case selection differs from protocol")
    if manifest.get("collection_status") != "complete" or len(records) != expected_calls:
        issues.append("Run is incomplete or has a mismatched sample count")

    record_ids = [row.get("sample_id") for row in records]
    if len(record_ids) != len(set(record_ids)):
        issues.append("Run contains duplicate sample ids")
    errors = sum(row.get("status") != "response" for row in records)
    auto_failures = sum(
        any(not check.get("passed") for check in row.get("automatic_checks", []))
        for row in records if row.get("status") == "response"
    )
    if errors:
        issues.append(f"Run contains {errors} inference errors")
    if auto_failures:
        issues.append(f"Run contains {auto_failures} automatic-check failures")

    review_by_id = {}
    for review in reviews:
        sample_id = review.get("sample_id")
        if sample_id in review_by_id:
            issues.append("Reviews contain duplicate sample ids")
        review_by_id[sample_id] = review
    missing_reviews = set(record_ids) - set(review_by_id)
    unknown_reviews = set(review_by_id) - set(record_ids)
    if missing_reviews or unknown_reviews:
        issues.append("Review ids do not exactly match collected sample ids")
    human_scores, critical = [], 0
    for sample_id in record_ids:
        review = review_by_id.get(sample_id, {})
        if review.get("reviewer_type") != "human" or type(review.get("score")) is not int:
            issues.append(f"{sample_id} lacks a completed human review")
            continue
        human_scores.append(review["score"])
        critical += int(review.get("critical_failure") is True)
    below = sum(score < protocol["developmentGate"]["minimumHumanScorePerTurn"] for score in human_scores)
    if critical:
        issues.append(f"Run has {critical} human-confirmed critical failures")
    if below:
        issues.append(f"Run has {below} human scores below the development gate")

    elapsed = [float(row["elapsed_seconds"]) for row in records if isinstance(row.get("elapsed_seconds"), (int, float))]
    categories = Counter(row.get("category") for row in records)
    return {
        "eligible": not issues,
        "issues": issues,
        "samples": len(records),
        "errors": errors,
        "automatic_failures": auto_failures,
        "human_reviewed": len(human_scores),
        "human_below_gate": below,
        "critical_failures": critical,
        "human_mean_score": round(statistics.mean(human_scores), 3) if human_scores else None,
        "latency_median_seconds": round(statistics.median(elapsed), 3) if elapsed else None,
        "latency_p95_seconds": _percentile(elapsed, 0.95),
        "categories": dict(categories),
    }


def audit_baseline_evidence(inputs_path: Path, protocol_path: Path = DEFAULT_PROTOCOL, root: Path = ROOT) -> dict:
    protocol_check = validate_protocol(protocol_path, root)
    protocol = read_json(protocol_path)
    registry = read_json(_project_path(protocol["modelRegistry"], root))
    foundation = _foundation(registry)
    tracks = {track["id"]: track for track in protocol["tracks"]}
    inputs = read_json(inputs_path)
    issues = list(protocol_check["issues"])
    if inputs.get("protocolId") != protocol.get("protocolId"):
        issues.append("Baseline inputs do not name the frozen protocol")
    rows = inputs.get("runs", [])
    provided: dict[tuple[str, str], dict] = {}
    for item in rows:
        key = (item.get("modelId"), item.get("trackId"))
        if key in provided:
            issues.append(f"Duplicate baseline run: {key}")
        provided[key] = item
    expected = required_matrix(protocol, foundation["id"])
    if set(provided) != expected:
        missing = sorted(expected - set(provided))
        unexpected = sorted(set(provided) - expected)
        if missing:
            issues.append(f"Missing required foundation-track runs: {missing}")
        if unexpected:
            issues.append(f"Unexpected foundation-track runs: {unexpected}")

    audits = {}
    for key in sorted(expected & set(provided)):
        _, track_id = key
        audit = _audit_run(protocol, foundation, tracks[track_id], provided[key], root)
        audits[f"{foundation['id']}/{track_id}"] = audit
        issues.extend(f"{foundation['id']}/{track_id}: {issue}" for issue in audit["issues"])

    supplemental = inputs.get("supplementalEvidence", {})
    for name in ("artifactManifests", "runtimeAttestations", "executableCodeReports", "longContextReports", "nativeToolReports", "humanAdjudication"):
        values = supplemental.get(name)
        if not isinstance(values, list) or not values:
            issues.append(f"Missing supplemental evidence group: {name}")
            continue
        for value in values:
            try:
                path = _project_path(value, root)
                if not path.is_file():
                    issues.append(f"Missing supplemental evidence file: {value}")
                    continue
                issues.extend(_supplemental_status_issues(name, path, value))
            except ValueError as exc:
                issues.append(str(exc))

    return {
        "protocol_id": protocol.get("protocolId"),
        "baseline_status": "ready_for_signed_decision" if not issues else "hold",
        "issues": issues,
        "run_audits": audits,
        "foundation_qualified": False,
        "selection_automatic": False,
        "limits": "A complete audit makes baseline evidence ready for a signed human decision; this tool never selects or qualifies a foundation itself.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    protocol = commands.add_parser("protocol")
    protocol.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    baseline = commands.add_parser("baseline")
    baseline.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    baseline.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_protocol(args.protocol) if args.command == "protocol" else audit_baseline_evidence(args.inputs, args.protocol)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if (args.command == "protocol" and not result["protocol_ready"]) or (args.command == "baseline" and result["baseline_status"] != "ready_for_signed_decision"):
            raise SystemExit(1)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Foundation baseline audit stopped: {exc}\n")


if __name__ == "__main__":
    main()
