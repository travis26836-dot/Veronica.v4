"""T2 protocol and comparison refusal tests; no inference or paid compute."""
import json

from veronica_core import qualification as q


def test_current_t2_protocol_has_two_complete_pairs_and_ten_required_runs():
    result = q.validate_protocol()
    assert result["protocol_ready"] is True
    assert result["registered_models"] == 4
    assert result["candidate_control_pairs"] == 2
    assert result["required_model_track_runs"] == 10
    assert result["pinned_card_and_license_files"] == 8
    assert result["paid_compute_started"] is False
    assert result["foundation_qualified"] is False


def test_comparison_cannot_pass_with_missing_runs_or_supplemental_evidence(tmp_path):
    inputs = tmp_path / "comparison-inputs.json"
    inputs.write_text(json.dumps({"protocolId": "t2-untouched-foundation-v1", "runs": []}), encoding="utf-8")
    result = q.compare_evidence(inputs)
    assert result["comparison_status"] == "hold"
    assert result["foundation_qualified"] is False
    assert any("Missing required model-track runs" in issue for issue in result["issues"])
    assert any("Missing supplemental evidence group" in issue for issue in result["issues"])


def test_required_matrix_does_not_pretend_non_thinking_candidate_has_native_thinking():
    protocol = q.read_json(q.DEFAULT_PROTOCOL)
    registry = q.read_json(q.ROOT / protocol["modelRegistry"])
    model_ids = set(q._models(registry))
    matrix = q.required_matrix(protocol, model_ids)
    assert ("qwen3-30b-a3b-2507-abliterated", "native-thinking") not in matrix
    assert ("qwen3-30b-a3b-2507-control", "native-thinking") not in matrix
    assert ("qwen3.8-27b-abliterated", "native-thinking") in matrix
    assert ("qwen3.8-27b-control", "native-thinking") in matrix


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
