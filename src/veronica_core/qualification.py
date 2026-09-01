"""Offline T2 protocol and evidence auditor. It never starts models or selects one."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
from typing import Any

from .evaluation import fingerprint, read_json, read_jsonl, validate_suite


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = ROOT / "config" / "t2-qualification.json"


def _project_path(value: str, root: Path = ROOT) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes project root: {value}")
    return path


def _models(registry: dict) -> dict[str, dict]:
    rows = registry.get("candidates", []) + registry.get("controls", [])
    result = {row.get("id"): row for row in rows if isinstance(row, dict)}
    if len(result) != len(rows) or None in result:
        raise ValueError("Model registry contains missing or duplicate ids")
    return result


def required_matrix(protocol: dict, model_ids: set[str]) -> set[tuple[str, str]]:
    expected = set()
    for track in protocol.get("tracks", []):
        required = track.get("requiredModels")
        ids = model_ids if required == "all" else set(required or [])
        unknown = ids - model_ids
        if unknown:
            raise ValueError(f"Track {track.get('id')} references unknown models: {sorted(unknown)}")
        expected.update((model_id, track["id"]) for model_id in ids)
    return expected


def validate_protocol(protocol_path: Path = DEFAULT_PROTOCOL, root: Path = ROOT) -> dict:
    protocol = read_json(protocol_path)
    registry_path = _project_path(protocol.get("modelRegistry", ""), root)
    registry = read_json(registry_path)
    models = _models(registry)
    issues: list[str] = []

    if protocol.get("schemaVersion") != 1 or not protocol.get("protocolId"):
        issues.append("Protocol requires schemaVersion 1 and protocolId")
    if protocol.get("status") != "frozen_before_live_runs":
        issues.append("Protocol must be frozen before collecting comparison outputs")
    if registry.get("selectionStatus") != "benchmark_required":
        issues.append("Registry must remain benchmark_required until a signed T2 decision exists")

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

    pair_members = set()
    for pair in protocol.get("pairs", []):
        candidate_id, control_id = pair.get("candidateId"), pair.get("controlId")
        candidate, control = models.get(candidate_id), models.get(control_id)
        if not candidate or not control:
            issues.append(f"Pair references missing model: {candidate_id}/{control_id}")
            continue
        pair_members.update((candidate_id, control_id))
        if candidate.get("matchingControlId") != control_id:
            issues.append(f"Candidate {candidate_id} does not point to {control_id}")
        if control.get("controlsCandidateId") != candidate_id:
            issues.append(f"Control {control_id} does not point to {candidate_id}")
    if pair_members != set(models):
        issues.append("Every registered candidate and control must appear in exactly one comparison pair")

    snapshot_files = 0
    profiles = {}
    for model_id, model in models.items():
        snapshot_value = model.get("provenanceSnapshot")
        if not snapshot_value:
            issues.append(f"{model_id} has no provenance snapshot path")
            continue
        snapshot = _project_path(snapshot_value, root)
        for filename in ("README.md", "LICENSE"):
            path = snapshot / filename
            if not path.is_file():
                issues.append(f"{model_id} is missing pinned {filename}")
            else:
                snapshot_files += 1
        license_path = snapshot / "LICENSE"
        if license_path.is_file():
            license_text = license_path.read_text(encoding="utf-8-sig", errors="replace")
            if "Apache License" not in license_text or "Version 2.0" not in license_text:
                issues.append(f"{model_id} license snapshot is not recognizable as Apache-2.0")

        profile_value = model.get("runpodProfile")
        if not profile_value:
            issues.append(f"{model_id} has no RunPod qualification profile")
            continue
        try:
            profile = read_json(_project_path(profile_value, root))
            profiles[model_id] = profile
            if profile.get("model", {}).get("repository") != model.get("repository") or profile.get("model", {}).get("revision") != model.get("revision"):
                issues.append(f"{model_id} RunPod profile identity does not match the registry")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            issues.append(f"{model_id} RunPod profile is unreadable: {type(exc).__name__}")

    runtime = protocol.get("matchedRuntime", {})
    for key in ("gpuType", "vllmVersion", "transformersVersion", "dtype", "maxModelLen", "surface"):
        if runtime.get(key) in (None, ""):
            issues.append(f"Matched runtime is missing {key}")
    if runtime.get("surface") != "direct" or runtime.get("wrapperPersona") is not False:
        issues.append("Untouched foundation comparison must use the direct, persona-free surface")
    for model_id, profile in profiles.items():
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
                issues.append(f"{model_id} profile {key} differs from the matched runtime")
        if pod.get("gpuTypeId") != runtime.get("gpuType") or pod.get("gpuCount") != runtime.get("gpuCount"):
            issues.append(f"{model_id} profile GPU differs from the matched runtime")
        if safety.get("maximumHourlyUsd") != runtime.get("maximumHourlyUsd"):
            issues.append(f"{model_id} profile spending ceiling differs from the matched runtime")
    for pair in protocol.get("pairs", []):
        expected_args = pair.get("serverArguments", [])
        for model_id in (pair.get("candidateId"), pair.get("controlId")):
            if model_id in profiles and profiles[model_id].get("runtime", {}).get("serverArguments") != expected_args:
                issues.append(f"{model_id} parser arguments differ from its matched control family")
    try:
        matrix = required_matrix(protocol, set(models))
    except (ValueError, KeyError, TypeError) as exc:
        issues.append(str(exc))
        matrix = set()
    case_ids = {case["id"] for case in suite.get("cases", [])} if "suite" in locals() else set()
    calls_by_id = {case["id"]: len(case["turns"]) for case in suite.get("cases", [])} if "suite" in locals() else {}
    for track in protocol.get("tracks", []):
        selected = track.get("caseIds")
        selected_ids = case_ids if selected == "all" else set(selected or [])
        if not selected_ids or selected_ids - case_ids:
            issues.append(f"Track {track.get('id')} has missing or unknown case ids")
            continue
        calls = sum(calls_by_id[case_id] for case_id in selected_ids)
        if calls != track.get("completionCallsPerRepeat"):
            issues.append(f"Track {track.get('id')} completion-call count does not match its selected cases")

    return {
        "protocol_id": protocol.get("protocolId"),
        "protocol_ready": not issues,
        "issues": issues,
        "registered_models": len(models),
        "candidate_control_pairs": len(protocol.get("pairs", [])),
        "required_model_track_runs": len(matrix),
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


def _audit_run(protocol: dict, model: dict, track: dict, item: dict, root: Path) -> dict:
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
        "surface": protocol["matchedRuntime"]["surface"],
        "mode": track["mode"],
        "temperature": track["temperature"],
        "top_p": track["topP"],
        "thinking": expected_thinking,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            issues.append(f"Manifest {key} differs from protocol")
    identity = manifest.get("identity", {})
    if identity.get("repository") != model.get("repository") or identity.get("revision") != model.get("revision"):
        issues.append("Manifest model identity does not match the pinned registry entry")
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
        "sample_ids": record_ids,
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


def compare_evidence(inputs_path: Path, protocol_path: Path = DEFAULT_PROTOCOL, root: Path = ROOT) -> dict:
    protocol_check = validate_protocol(protocol_path, root)
    protocol = read_json(protocol_path)
    registry = read_json(_project_path(protocol["modelRegistry"], root))
    models = _models(registry)
    tracks = {track["id"]: track for track in protocol["tracks"]}
    inputs = read_json(inputs_path)
    issues = list(protocol_check["issues"])
    if inputs.get("protocolId") != protocol.get("protocolId"):
        issues.append("Comparison inputs do not name the frozen protocol")
    rows = inputs.get("runs", [])
    provided: dict[tuple[str, str], dict] = {}
    for item in rows:
        key = (item.get("modelId"), item.get("trackId"))
        if key in provided:
            issues.append(f"Duplicate comparison run: {key}")
        provided[key] = item
    expected = required_matrix(protocol, set(models))
    if set(provided) != expected:
        missing = sorted(expected - set(provided))
        unexpected = sorted(set(provided) - expected)
        if missing:
            issues.append(f"Missing required model-track runs: {missing}")
        if unexpected:
            issues.append(f"Unexpected model-track runs: {unexpected}")

    audits = {}
    for key in sorted(expected & set(provided)):
        model_id, track_id = key
        audit = _audit_run(protocol, models[model_id], tracks[track_id], provided[key], root)
        audits[f"{model_id}/{track_id}"] = {k: v for k, v in audit.items() if k != "sample_ids"}
        issues.extend(f"{model_id}/{track_id}: {issue}" for issue in audit["issues"])

    for pair in protocol["pairs"]:
        for track_id, track in tracks.items():
            members = set(models) if track["requiredModels"] == "all" else set(track["requiredModels"])
            candidate_key = (pair["candidateId"], track_id)
            control_key = (pair["controlId"], track_id)
            if pair["candidateId"] not in members or pair["controlId"] not in members:
                continue
            if candidate_key in provided and control_key in provided:
                candidate = _audit_run(protocol, models[candidate_key[0]], track, provided[candidate_key], root)
                control = _audit_run(protocol, models[control_key[0]], track, provided[control_key], root)
                if candidate.get("sample_ids") != control.get("sample_ids"):
                    issues.append(f"{pair['family']}/{track_id}: candidate and control sample ids are not paired")

    supplemental = inputs.get("supplementalEvidence", {})
    for name in ("artifactManifests", "runtimeAttestations", "executableCodeReports", "longContextReports", "nativeToolReports", "humanAdjudication"):
        values = supplemental.get(name)
        if not isinstance(values, list) or not values:
            issues.append(f"Missing supplemental evidence group: {name}")
            continue
        for value in values:
            try:
                if not _project_path(value, root).is_file():
                    issues.append(f"Missing supplemental evidence file: {value}")
            except ValueError as exc:
                issues.append(str(exc))

    return {
        "protocol_id": protocol.get("protocolId"),
        "comparison_status": "ready_for_signed_selection" if not issues else "hold",
        "issues": issues,
        "run_audits": audits,
        "foundation_qualified": False,
        "selection_automatic": False,
        "limits": "A complete audit makes evidence ready for a signed human decision; this tool never selects or qualifies a foundation itself.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    protocol = commands.add_parser("protocol")
    protocol.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    compare = commands.add_parser("compare")
    compare.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    compare.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_protocol(args.protocol) if args.command == "protocol" else compare_evidence(args.inputs, args.protocol)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if (args.command == "protocol" and not result["protocol_ready"]) or (args.command == "compare" and result["comparison_status"] != "ready_for_signed_selection"):
            raise SystemExit(1)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Qualification audit stopped: {exc}\n")


if __name__ == "__main__":
    main()
