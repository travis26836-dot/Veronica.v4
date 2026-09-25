"""Installed-foundation baseline protocol tests; no inference or paid compute."""
import json

from veronica_core import qualification as q


def test_foundation_baseline_protocol_has_one_foundation_and_two_required_tracks():
    result = q.validate_protocol()
    assert result["protocol_ready"] is True
    assert result["registered_foundations"] == 1
    assert result["baseline_tracks"] == 2
    assert result["required_foundation_track_runs"] == 2
    assert result["pinned_card_and_license_files"] == 2
    assert result["paid_compute_started"] is False
    assert result["foundation_qualified"] is False


def test_baseline_cannot_pass_with_missing_runs_or_supplemental_evidence(tmp_path):
    inputs = tmp_path / "foundation-baseline-inputs.json"
    inputs.write_text(json.dumps({"protocolId": "foundation-baseline-v1", "runs": []}), encoding="utf-8")
    result = q.audit_baseline_evidence(inputs)
    assert result["baseline_status"] == "hold"
    assert result["foundation_qualified"] is False
    assert any("Missing required foundation-track runs" in issue for issue in result["issues"])
    assert any("Missing supplemental evidence group" in issue for issue in result["issues"])


def test_required_matrix_includes_only_the_installed_foundation_tracks():
    protocol = q.read_json(q.DEFAULT_PROTOCOL)
    registry = q.read_json(q.ROOT / protocol["modelRegistry"])
    foundation = q._foundation(registry)
    matrix = q.required_matrix(protocol, foundation["id"])
    assert matrix == {
        ("foundation-baseline", "neutral-deterministic"),
        ("foundation-baseline", "neutral-sampled"),
    }


def test_json_supplemental_status_other_than_collected_pass_is_an_issue(tmp_path):
    report = tmp_path / "executable-code-report.json"
    report.write_text(json.dumps({"status": "isolation_unverified"}), encoding="utf-8")
    issues = q._supplemental_status_issues("executableCodeReports", report, "runs/x/executable-code-report.json")
    assert issues
    assert "isolation_unverified" in issues[0]
    report.write_text(json.dumps({"status": "collected_pass"}), encoding="utf-8")
    assert q._supplemental_status_issues("executableCodeReports", report, "runs/x/executable-code-report.json") == []
    skipped = tmp_path / "long-context-report.json"
    skipped.write_text(json.dumps({"status": "not_collected"}), encoding="utf-8")
    assert q._supplemental_status_issues("longContextReports", skipped, "runs/x/long-context-report.json")
    manifest = tmp_path / "artifact-manifest.json"
    manifest.write_text(json.dumps({"files": []}), encoding="utf-8")
    assert q._supplemental_status_issues("artifactManifests", manifest, "runs/x/artifact-manifest.json") == []
    note = tmp_path / "human-adjudication.md"
    note.write_text("# pending\n", encoding="utf-8")
    assert q._supplemental_status_issues("humanAdjudication", note, "runs/x/human-adjudication.md") == []
