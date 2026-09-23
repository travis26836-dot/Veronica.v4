"""Build and validate the frozen T2 qualification-readiness packet.

This module only prepares an offline, reproducible manifest.  It never starts
inference, provisions a Pod, selects a model, or changes the qualification
state.  CP2 and CP3 are explicit inputs: the packet remains on hold until both
checkpoint evidence records are complete and hashable.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from . import qualification as q

ROOT = q.ROOT
PACKET_SCHEMA_VERSION = 1
PACKET_ID = "t2-untouched-foundation-v2-readiness"
DEPENDENCY_STATUSES = {"pending", "complete", "blocked"}
DEPENDENCY_ARTIFACTS = {
    "CP2": {"config", "metadata", "probes", "report", "validation"},
    "CP3": {"attestation", "tests-offline", "tests-docker", "inventory"},
}
REQUIRED_TOP_LEVEL = {
    "schemaVersion",
    "packetId",
    "status",
    "protocol",
    "suite",
    "runtime",
    "thresholds",
    "cases",
    "sampling",
    "modelMatrix",
    "requiredEvidence",
    "dependencies",
    "paidComputeStarted",
    "foundationQualified",
    "packetSha256",
}


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def packet_hash(packet: Mapping[str, Any]) -> str:
    """Hash packet content without the self-referential packetSha256 field."""
    unsigned = deepcopy(dict(packet))
    unsigned["packetSha256"] = None
    return _hash_bytes(_canonical(unsigned))


def _project_path(value: str, root: Path) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes project root: {value}")
    return path


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _case_snapshot(protocol: dict[str, Any], root: Path) -> dict[str, Any]:
    suite_spec = protocol["suite"]
    suite_path = _project_path(suite_spec["path"], root)
    suite = q.read_json(suite_path)
    q.validate_suite(suite)
    cases = suite["cases"]
    return {
        "path": suite_spec["path"],
        "sha256": file_hash(suite_path),
        "suiteId": suite["suite_id"],
        "tier": suite_spec["tier"],
        "caseCount": len(cases),
        "completionCallsPerRepeat": sum(len(case["turns"]) for case in cases),
        "caseIds": [case["id"] for case in cases],
        "syntheticContextCasesExcluded": True,
    }


def _sampling_snapshot(protocol: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    models = q._models(registry)
    model_ids = set(models)
    result = []
    for track in protocol["tracks"]:
        required = track["requiredModels"]
        required_models = sorted(model_ids if required == "all" else set(required))
        result.append({
            "id": track["id"],
            "requiredModels": required_models,
            "mode": track["mode"],
            "enableThinking": track["enableThinking"],
            "caseIds": track["caseIds"],
            "completionCallsPerRepeat": track["completionCallsPerRepeat"],
            "repeats": track["repeats"],
            "temperature": track["temperature"],
            "topP": track["topP"],
            "seed": track["seed"],
            "maxTokens": track["maxTokens"],
        })
    return result


def _dependency(name: str, checkpoint: str, value: Mapping[str, Any] | None, root: Path) -> dict[str, Any]:
    """Normalize a wrapper while preserving its transitive evidence refs.

    A status-only wrapper is retained as an invalid complete dependency so the
    packet validator can explain why it is not ready.  It is never promoted by
    this builder merely because its status says ``complete``.
    """
    value = dict(value or {})
    wrapper_value = value.get("path")
    if not wrapper_value:
        return {
            "checkpoint": checkpoint,
            "status": "pending",
            "evidence": None,
            "requiredForReady": True,
        }
    wrapper_path = _project_path(str(wrapper_value), root)
    wrapper_ref = {"path": _relative(wrapper_path, root), "sha256": file_hash(wrapper_path)} if wrapper_path.is_file() else {
        "path": str(wrapper_value), "sha256": None
    }
    try:
        payload = q.read_json(wrapper_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "checkpoint": checkpoint,
            "status": "blocked",
            "evidence": {"wrapper": wrapper_ref},
            "requiredForReady": True,
            "validationIssues": [f"Unreadable {name} dependency wrapper: {type(exc).__name__}"],
        }
    status = payload.get("status", "pending")
    if status not in DEPENDENCY_STATUSES:
        status = "blocked"
        validation_issues = [f"{name} dependency wrapper has unsupported status"]
    else:
        validation_issues = []
    evidence = {"wrapper": wrapper_ref}
    if status == "complete":
        evidence["decision"] = payload.get("decision")
        evidence["artifacts"] = payload.get("artifacts")
        if payload.get("checkpoint") != checkpoint:
            validation_issues.append(f"{name} wrapper checkpoint does not match {checkpoint}")
    return {
        "checkpoint": checkpoint,
        "status": status,
        "evidence": evidence,
        "requiredForReady": True,
        **({"validationIssues": validation_issues} if validation_issues else {}),
    }


def build_packet(
    protocol_path: Path = q.DEFAULT_PROTOCOL,
    root: Path = ROOT,
    *,
    cp2: Mapping[str, Any] | None = None,
    cp3: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a packet from the frozen protocol and optional CP2/CP3 evidence."""
    root = root.resolve()
    protocol_path = protocol_path.resolve()
    protocol = q.read_json(protocol_path)
    protocol_check = q.validate_protocol(protocol_path, root)
    if not protocol_check["protocol_ready"]:
        raise ValueError("Cannot build packet from an invalid frozen protocol")
    registry = q.read_json(_project_path(protocol["modelRegistry"], root))
    model_ids = set(q._models(registry))
    packet: dict[str, Any] = {
        "schemaVersion": PACKET_SCHEMA_VERSION,
        "packetId": PACKET_ID,
        "status": "frozen_readiness_only",
        "protocol": {
            "path": _relative(protocol_path, root),
            "protocolId": protocol["protocolId"],
            "schemaVersion": protocol["schemaVersion"],
            "sha256": file_hash(protocol_path),
            "status": protocol["status"],
        },
        "suite": _case_snapshot(protocol, root),
        "runtime": deepcopy(protocol["matchedRuntime"]),
        "thresholds": deepcopy(protocol["developmentGate"]),
        "cases": {
            "source": protocol["suite"]["path"],
            "caseIds": _case_snapshot(protocol, root)["caseIds"],
            "caseCount": protocol["suite"]["caseCount"],
            "completionCallsPerRepeat": protocol["suite"]["completionCallsPerRepeat"],
            "holdout": False,
            "syntheticContextCasesExcluded": True,
        },
        "sampling": _sampling_snapshot(protocol, registry),
        "modelMatrix": {
            "models": sorted(model_ids),
            "requiredRuns": sorted([list(key) for key in q.required_matrix(protocol, model_ids)]),
            "candidateControlPairs": deepcopy(protocol["pairs"]),
        },
        "requiredEvidence": deepcopy(protocol["requiredEvidence"]),
        "dependencies": {
            "CP2": _dependency("CP2", "actual-token-context-packet", cp2, root),
            "CP3": _dependency("CP3", "evaluator-integrity", cp3, root),
        },
        "paidComputeStarted": False,
        "foundationQualified": False,
        "packetSha256": None,
    }
    packet["packetSha256"] = packet_hash(packet)
    return packet


def _read_ref(name: str, value: Any, root: Path, issues: list[str]) -> tuple[Path | None, Any]:
    if not isinstance(value, dict):
        issues.append(f"{name} requires a path and SHA-256")
        return None, None
    path_value, expected_hash = value.get("path"), value.get("sha256")
    if not isinstance(path_value, str) or not isinstance(expected_hash, str):
        issues.append(f"{name} requires a path and SHA-256")
        return None, None
    try:
        path = _project_path(path_value, root)
        if not path.is_file():
            issues.append(f"{name} evidence file is missing")
            return None, expected_hash
        actual_hash = file_hash(path)
        if actual_hash != expected_hash:
            issues.append(f"{name} evidence hash does not match")
            return None, expected_hash
        return path, expected_hash
    except (OSError, ValueError) as exc:
        issues.append(f"{name} evidence is invalid: {exc}")
        return None, expected_hash


def _artifact_map(name: str, evidence: dict[str, Any], root: Path, issues: list[str]) -> dict[str, Path]:
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list):
        issues.append(f"{name} complete dependency requires an artifacts list")
        return {}
    result: dict[str, Path] = {}
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict) or not isinstance(artifact.get("kind"), str):
            issues.append(f"{name} artifact {index} requires a kind")
            continue
        kind = artifact["kind"]
        if kind in result:
            issues.append(f"{name} contains duplicate artifact kind: {kind}")
            continue
        path, _ = _read_ref(f"{name} artifact {kind}", artifact, root, issues)
        if path is not None:
            result[kind] = path
    missing = DEPENDENCY_ARTIFACTS[name] - result.keys()
    if missing:
        issues.append(f"{name} missing required artifacts: {sorted(missing)}")
    return result


def _validate_cp2_artifacts(artifacts: dict[str, Path], suite_sha256: str | None, issues: list[str]) -> None:
    try:
        config = q.read_json(artifacts["config"])
        metadata = q.read_json(artifacts["metadata"])
        report = q.read_json(artifacts["report"])
        validation = q.read_json(artifacts["validation"])
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(f"CP2 artifact JSON is unreadable: {type(exc).__name__}")
        return
    if config.get("packet_id") != "t2-actual-token-context-v1" or config.get("in_frozen_suite") is not False:
        issues.append("CP2 config is not the actual-token context packet contract")
    if config.get("targets") != [8192, 16384, 32768] or config.get("positions") != ["begin", "mid", "end"]:
        issues.append("CP2 config does not freeze the nine required probes")
    if config.get("frozen_suite", {}).get("sha256") != suite_sha256:
        issues.append("CP2 config frozen-suite hash differs from the T2 packet")
    if metadata.get("packet_id") != "t2-actual-token-context-v1" or metadata.get("model_behavior_claim") is not False:
        issues.append("CP2 metadata does not prove packet-only behavior")
    runtime = metadata.get("runtime", {})
    if runtime.get("model_server_started") is not False or runtime.get("pod_started") is not False:
        issues.append("CP2 metadata claims model or Pod execution")
    required_report = {
        "kind": "actual_token_context_report",
        "status": "ready",
        "probe_count": 9,
        "expected_probe_count": 9,
        "all_probes_outside_frozen_suite": True,
        "primary_exact_targets": True,
        "model_behavior_claim": False,
        "model_retrieval_accuracy": None,
        "model_latency_collected": False,
        "truncation_is_reported_per_tokenizer": True,
    }
    for key, expected in required_report.items():
        if report.get(key) != expected:
            issues.append(f"CP2 report field {key} is not {expected!r}")
    if validation.get("valid") is not True or validation.get("model_behavior_claim") is not False:
        issues.append("CP2 validation report is not a valid packet-only result")
    try:
        probe_rows = [json.loads(line) for line in artifacts["probes"].read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(f"CP2 probes artifact is unreadable: {type(exc).__name__}")
        return
    if len(probe_rows) != 9 or any(row.get("in_frozen_suite") is not False for row in probe_rows):
        issues.append("CP2 probes artifact is not exactly nine synthetic out-of-suite probes")


def _validate_cp3_artifacts(artifacts: dict[str, Path], issues: list[str]) -> None:
    try:
        attestation = q.read_json(artifacts["attestation"])
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(f"CP3 attestation is unreadable: {type(exc).__name__}")
        return
    if attestation.get("verified") is not True or attestation.get("backend") != "docker":
        issues.append("CP3 attestation is not a verified Docker result")
    if attestation.get("foundation_qualified") is not False:
        issues.append("CP3 attestation cannot claim foundation qualification")
    checks = attestation.get("probe_checks", {})
    for key in ("network_blocked", "root_readonly", "docker_socket_absent"):
        if checks.get(key) is not True:
            issues.append(f"CP3 attestation probe {key} did not pass")
    for kind in ("tests-offline", "tests-docker"):
        try:
            text = artifacts[kind].read_text(encoding="utf-8-sig")
        except (KeyError, OSError) as exc:
            issues.append(f"CP3 {kind} artifact is unreadable: {type(exc).__name__}")
            continue
        if not re.search(r"\b\d+\s+passed\b", text) or re.search(r"\b\d+\s+failed\b", text):
            issues.append(f"CP3 {kind} artifact does not show a passing test result")
    try:
        inventory = artifacts["inventory"].read_text(encoding="utf-8-sig")
    except (KeyError, OSError) as exc:
        issues.append(f"CP3 inventory artifact is unreadable: {type(exc).__name__}")
    else:
        if "Result: no output" not in inventory or "no labeled evaluator containers remained" not in inventory:
            issues.append("CP3 inventory does not prove clean evaluator-container state")


def _validate_dependency(name: str, value: Any, root: Path, issues: list[str], suite_sha256: str | None) -> bool:
    start_issue_count = len(issues)
    if not isinstance(value, dict):
        issues.append(f"Dependency {name} must be an object")
        return False
    if value.get("requiredForReady") is not True:
        issues.append(f"Dependency {name} must remain required for CP4 readiness")
    status = value.get("status")
    if status not in DEPENDENCY_STATUSES:
        issues.append(f"Dependency {name} has invalid status")
        return False
    for issue in value.get("validationIssues", []):
        issues.append(str(issue))
    evidence = value.get("evidence")
    if status == "complete" and not isinstance(evidence, dict):
        issues.append(f"Dependency {name} complete status requires transitive evidence metadata")
        return False
    if status == "complete":
        if "wrapper" not in evidence or "decision" not in evidence or "artifacts" not in evidence:
            issues.append(f"Dependency {name} complete-only wrapper rejected; decision and artifact refs are required")
            return False
        wrapper_path, _ = _read_ref(f"{name} wrapper", evidence.get("wrapper"), root, issues)
        decision_path, _ = _read_ref(f"{name} decision", evidence.get("decision"), root, issues)
        if wrapper_path is None or decision_path is None:
            return False
        try:
            wrapper = q.read_json(wrapper_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{name} wrapper JSON is unreadable: {type(exc).__name__}")
            return False
        expected_checkpoint = value.get("checkpoint")
        if wrapper.get("status") != "complete" or wrapper.get("checkpoint") != expected_checkpoint:
            issues.append(f"{name} wrapper is not a matching complete checkpoint record")
        if wrapper.get("decision") != evidence.get("decision") or wrapper.get("artifacts") != evidence.get("artifacts"):
            issues.append(f"{name} packet refs differ from the hashed wrapper contents")
        decision_text = decision_path.read_text(encoding="utf-8-sig", errors="replace")
        if f"{name} " not in decision_text or "complete" not in decision_text.lower():
            issues.append(f"{name} decision artifact does not record completion")
        artifacts = _artifact_map(name, evidence, root, issues)
        if name == "CP2":
            _validate_cp2_artifacts(artifacts, suite_sha256, issues)
        else:
            _validate_cp3_artifacts(artifacts, issues)
        return len(issues) == start_issue_count
    if evidence is not None:
        issues.append(f"Dependency {name} pending/blocked status cannot carry evidence")
    return False


def validate_packet(
    packet: Mapping[str, Any],
    root: Path = ROOT,
    *,
    verify_frozen_inputs: bool = True,
) -> dict[str, Any]:
    """Validate a packet and report readiness without qualifying a model."""
    root = root.resolve()
    packet = dict(packet)
    issues: list[str] = []
    missing = REQUIRED_TOP_LEVEL - packet.keys()
    unexpected = set(packet) - REQUIRED_TOP_LEVEL
    if missing:
        issues.append(f"Missing packet fields: {sorted(missing)}")
    if unexpected:
        issues.append(f"Unexpected packet fields: {sorted(unexpected)}")
    if packet.get("schemaVersion") != PACKET_SCHEMA_VERSION or packet.get("packetId") != PACKET_ID:
        issues.append("Packet schemaVersion or packetId is not the frozen CP4 contract")
    if packet.get("status") != "frozen_readiness_only":
        issues.append("Packet status must be frozen_readiness_only")
    if packet.get("paidComputeStarted") is not False:
        issues.append("Readiness packet cannot claim paid compute")
    if packet.get("foundationQualified") is not False:
        issues.append("Readiness packet cannot claim foundation qualification")
    if packet.get("packetSha256") != packet_hash(packet):
        issues.append("Packet SHA-256 does not match its content")

    protocol = packet.get("protocol", {})
    suite = packet.get("suite", {})
    if verify_frozen_inputs:
        try:
            protocol_path = _project_path(protocol["path"], root)
            current_protocol = q.read_json(protocol_path)
            if file_hash(protocol_path) != protocol.get("sha256"):
                issues.append("Frozen protocol SHA-256 does not match the current file")
            if current_protocol.get("protocolId") != protocol.get("protocolId"):
                issues.append("Frozen protocol id does not match the packet")
            current_suite = _project_path(suite["path"], root)
            if file_hash(current_suite) != suite.get("sha256"):
                issues.append("Frozen suite SHA-256 does not match the current file")
            registry = q.read_json(_project_path(current_protocol["modelRegistry"], root))
            expected_suite = _case_snapshot(current_protocol, root)
            if suite != expected_suite:
                issues.append("Suite manifest differs from the frozen protocol")
            if packet.get("runtime") != current_protocol.get("matchedRuntime"):
                issues.append("Runtime manifest differs from the frozen protocol")
            if packet.get("thresholds") != current_protocol.get("developmentGate"):
                issues.append("Threshold manifest differs from the frozen protocol")
            if packet.get("requiredEvidence") != current_protocol.get("requiredEvidence"):
                issues.append("Required-evidence manifest differs from the frozen protocol")
            if packet.get("sampling") != _sampling_snapshot(current_protocol, registry):
                issues.append("Sampling manifest differs from the frozen protocol")
            model_ids = set(q._models(registry))
            expected_matrix = {
                "models": sorted(model_ids),
                "requiredRuns": sorted([list(key) for key in q.required_matrix(current_protocol, model_ids)]),
                "candidateControlPairs": current_protocol["pairs"],
            }
            if packet.get("modelMatrix") != expected_matrix:
                issues.append("Model matrix differs from the frozen protocol")
            expected_cases = {
                "source": current_protocol["suite"]["path"],
                "caseIds": expected_suite["caseIds"],
                "caseCount": expected_suite["caseCount"],
                "completionCallsPerRepeat": expected_suite["completionCallsPerRepeat"],
                "holdout": False,
                "syntheticContextCasesExcluded": True,
            }
            if packet.get("cases") != expected_cases:
                issues.append("Case manifest differs from the frozen protocol")
        except (KeyError, OSError, ValueError, TypeError) as exc:
            issues.append(f"Frozen protocol/suite inputs are invalid: {exc}")

    dependencies = packet.get("dependencies", {})
    dependency_results = {
        name: _validate_dependency(name, dependencies.get(name), root, issues, packet.get("suite", {}).get("sha256"))
        for name in ("CP2", "CP3")
    }
    ready = not issues and all(dependency_results.values())
    return {
        "packetId": packet.get("packetId"),
        "packetSha256": packet.get("packetSha256"),
        "valid": not issues,
        "ready": ready,
        "status": "ready" if ready else "hold",
        "issues": issues,
        "dependencies": dependency_results,
        "paidComputeStarted": False,
        "foundationQualified": False,
    }


def write_packet(path: Path, packet: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
