"""Offline CP4 packet contract tests; no inference or paid compute."""
from __future__ import annotations

from veronica_core import qualification_packet as p


def test_current_packet_is_structurally_valid_but_waits_for_cp2_and_cp3():
    packet = p.build_packet()
    report = p.validate_packet(packet)
    assert report["valid"] is True
    assert report["ready"] is False
    assert report["status"] == "hold"
    assert report["dependencies"] == {"CP2": False, "CP3": False}
    assert report["paidComputeStarted"] is False
    assert report["foundationQualified"] is False


def test_complete_dependencies_make_a_ready_packet_when_hashes_are_valid(tmp_path):
    # Use an immutable repository artifact as a local hash fixture.  The
    # packet contract checks path containment and bytes; real CP2/CP3 evidence
    # is supplied only by their completed checkpoint runs.
    evidence = "runs/2026-09-22-cp1-schema-gate/decision.md"
    packet = p.build_packet(
        cp2={"status": "complete", "path": evidence},
        cp3={"status": "complete", "path": evidence},
    )
    report = p.validate_packet(packet)
    assert report["valid"] is True
    assert report["ready"] is True


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
