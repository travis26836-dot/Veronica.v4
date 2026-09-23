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
from typing import Any, Mapping

from . import qualification as q

ROOT = q.ROOT
PACKET_SCHEMA_VERSION = 1
PACKET_ID = "t2-untouched-foundation-v2-readiness"
DEPENDENCY_STATUSES = {"pending", "complete", "blocked"}
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
    value = dict(value or {})
    status = value.get("status", "pending")
    if status not in DEPENDENCY_STATUSES:
        raise ValueError(f"{name} dependency has unsupported status: {status}")
    evidence_path = value.get("path")
    evidence_hash = value.get("sha256")
    if evidence_path:
        path = _project_path(str(evidence_path), root)
        if not path.is_file():
            raise ValueError(f"{name} dependency evidence does not exist: {evidence_path}")
        actual = file_hash(path)
        if evidence_hash and evidence_hash != actual:
            raise ValueError(f"{name} dependency evidence hash does not match: {evidence_path}")
        evidence_hash = actual
        evidence_path = _relative(path, root)
    elif status == "complete":
        raise ValueError(f"{name} cannot be complete without evidence path")
    return {
        "checkpoint": checkpoint,
        "status": status,
        "evidence": {"path": evidence_path, "sha256": evidence_hash},
        "requiredForReady": True,
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


def _validate_dependency(name: str, value: Any, root: Path, issues: list[str]) -> bool:
    if not isinstance(value, dict):
        issues.append(f"Dependency {name} must be an object")
        return False
    if value.get("requiredForReady") is not True:
        issues.append(f"Dependency {name} must remain required for CP4 readiness")
    status = value.get("status")
    if status not in DEPENDENCY_STATUSES:
        issues.append(f"Dependency {name} has invalid status")
        return False
    evidence = value.get("evidence")
    if not isinstance(evidence, dict):
        issues.append(f"Dependency {name} requires evidence metadata")
        return False
    path_value, expected_hash = evidence.get("path"), evidence.get("sha256")
    if status == "complete":
        if not isinstance(path_value, str) or not isinstance(expected_hash, str):
            issues.append(f"Dependency {name} complete status requires path and SHA-256")
            return False
        try:
            path = _project_path(path_value, root)
            if not path.is_file():
                issues.append(f"Dependency {name} evidence file is missing")
                return False
            if file_hash(path) != expected_hash:
                issues.append(f"Dependency {name} evidence hash does not match")
                return False
        except (OSError, ValueError) as exc:
            issues.append(f"Dependency {name} evidence is invalid: {exc}")
            return False
        return True
    if path_value is not None or expected_hash is not None:
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
        name: _validate_dependency(name, dependencies.get(name), root, issues)
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
