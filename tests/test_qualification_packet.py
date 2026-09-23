"""Offline CP4 packet contract tests; no inference or paid compute."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

from veronica_core import qualification_packet as p


def _copy_fixture(src_root: Path, dst_root: Path, relative_paths: list[str]) -> None:
    for relative in relative_paths:
        source = src_root / relative
        destination = dst_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def _complete_packet(tmp_path: Path) -> dict:
    cp2_paths = [
        "runs/2026-09-22-cp2-context-packet/decision.md",
        "config/t2-context.json",
        "runs/2026-09-22-cp2-context-packet/metadata.json",
        "runs/2026-09-22-cp2-context-packet/probes.jsonl",
        "runs/2026-09-22-cp2-context-packet/report.json",
        "runs/2026-09-22-cp2-context-packet/validation.json",
    ]
    cp3_paths = [
        "runs/2026-09-22-cp3-evaluator-integrity/decision.md",
        "runs/2026-09-22-cp3-evaluator-integrity/docker-attestation.json",
        "runs/2026-09-22-cp3-evaluator-integrity/tests-offline.txt",
        "runs/2026-09-22-cp3-evaluator-integrity/tests-docker.txt",
        "runs/2026-09-22-cp3-evaluator-integrity/container-inventory.txt",
    ]
    _copy_fixture(p.ROOT, tmp_path, cp2_paths + cp3_paths)

    def ref(relative: str, kind: str | None = None) -> dict:
        path = tmp_path / relative
        value = {"path": relative, "sha256": p.file_hash(path)}
        if kind:
            value["kind"] = kind
        return value

    cp2_wrapper = {
        "checkpoint": "actual-token-context-packet",
        "status": "complete",
        "decision": ref(cp2_paths[0]),
        "artifacts": [
            ref(cp2_paths[1], "config"),
            ref(cp2_paths[2], "metadata"),
            ref(cp2_paths[3], "probes"),
            ref(cp2_paths[4], "report"),
            ref(cp2_paths[5], "validation"),
        ],
    }
    cp3_wrapper = {
        "checkpoint": "evaluator-integrity",
        "status": "complete",
        "decision": ref(cp3_paths[0]),
        "artifacts": [
            ref(cp3_paths[1], "attestation"),
            ref(cp3_paths[2], "tests-offline"),
            ref(cp3_paths[3], "tests-docker"),
            ref(cp3_paths[4], "inventory"),
        ],
    }
    for name, payload in (("cp2.json", cp2_wrapper), ("cp3.json", cp3_wrapper)):
        (tmp_path / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    packet = p.build_packet()
    packet["dependencies"] = {
        "CP2": p._dependency("CP2", "actual-token-context-packet", {"path": "cp2.json"}, tmp_path),
        "CP3": p._dependency("CP3", "evaluator-integrity", {"path": "cp3.json"}, tmp_path),
    }
    packet["packetSha256"] = p.packet_hash(packet)
    return packet


def test_current_packet_is_structurally_valid_but_waits_for_cp2_and_cp3():
    packet = p.build_packet()
    report = p.validate_packet(packet)
    assert report["valid"] is True
    assert report["ready"] is False
    assert report["status"] == "hold"
    assert report["dependencies"] == {"CP2": False, "CP3": False}
    assert report["paidComputeStarted"] is False
    assert report["foundationQualified"] is False


def test_real_cp2_and_cp3_artifacts_make_a_ready_packet_when_transitively_hashed(tmp_path):
    report = p.validate_packet(_complete_packet(tmp_path), root=tmp_path, verify_frozen_inputs=False)
    assert report["valid"] is True
    assert report["ready"] is True
    assert report["dependencies"] == {"CP2": True, "CP3": True}


def test_transitive_artifact_mutation_blocks_readiness(tmp_path):
    packet = _complete_packet(tmp_path)
    report_path = tmp_path / "runs/2026-09-22-cp2-context-packet/report.json"
    report_path.write_text(report_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    report = p.validate_packet(packet, root=tmp_path, verify_frozen_inputs=False)
    assert report["valid"] is False
    assert report["ready"] is False
    assert any("CP2 artifact report evidence hash does not match" in issue for issue in report["issues"])


def test_historical_complete_only_wrappers_are_rejected_without_rewriting_history():
    historical = p.q.read_json(p.ROOT / "runs/2026-09-23-t2-readiness-review/t2-readiness-packet.json")
    report = p.validate_packet(historical)
    assert report["valid"] is False
    assert report["ready"] is False
    assert any("complete-only wrapper rejected" in issue for issue in report["issues"])


def test_packet_rejects_tampering_and_false_qualification_claims():
    packet = p.build_packet()
    packet["foundationQualified"] = True
    report = p.validate_packet(packet)
    assert report["valid"] is False
    assert any("foundation qualification" in issue for issue in report["issues"])


def test_packet_sampling_and_case_manifest_are_explicit_and_frozen():
    packet = p.build_packet()
    assert packet["protocol"]["protocolId"] == "t2-untouched-foundation-v2"
    assert packet["suite"]["caseCount"] == 60
    assert len(packet["cases"]["caseIds"]) == 60
    assert {track["id"] for track in packet["sampling"]} == {
        "neutral-deterministic", "neutral-sampled", "native-thinking"
    }
    assert packet["runtime"]["maxModelLen"] == 32768
    assert packet["thresholds"]["maximumCriticalFailures"] == 0
    assert packet["modelMatrix"]["requiredRuns"]


def test_packet_hash_changes_when_any_frozen_field_changes():
    packet = p.build_packet()
    original = packet["packetSha256"]
    packet["thresholds"]["minimumHumanScorePerTurn"] = 4
    assert p.packet_hash(packet) != original
    report = p.validate_packet(packet)
    assert report["valid"] is False
    assert any("SHA-256" in issue for issue in report["issues"])
