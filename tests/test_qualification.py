"""T2 protocol and comparison refusal tests; no inference or paid compute."""
import json

from veronica_core import qualification as q


def test_owner_selected_t2_protocol_excludes_retired_candidate_b():
    result = q.validate_protocol()
    assert result["protocol_ready"] is True
    assert result["registered_models"] == 2
    assert result["candidate_control_pairs"] == 1
    assert result["required_model_track_runs"] == 4
    assert result["pinned_card_and_license_files"] == 4
    assert result["paid_compute_started"] is False
    assert result["foundation_qualified"] is False


def test_owner_selected_status_does_not_qualify_foundation():
    result = q.validate_protocol()
    assert result["protocol_ready"] is True
    assert result["foundation_qualified"] is False


def test_comparison_cannot_pass_with_missing_runs_or_supplemental_evidence(tmp_path):
    inputs = tmp_path / "comparison-inputs.json"
    inputs.write_text(json.dumps({"protocolId": "t2-untouched-foundation-v3", "runs": []}), encoding="utf-8")
    result = q.compare_evidence(inputs)
    assert result["comparison_status"] == "hold"
    assert result["foundation_qualified"] is False
    assert any("Missing required model-track runs" in issue for issue in result["issues"])
    assert any("Missing supplemental evidence group" in issue for issue in result["issues"])


def test_required_matrix_contains_only_active_models_and_frozen_tracks():
    protocol = q.read_json(q.DEFAULT_PROTOCOL)
    registry = q.read_json(q.ROOT / protocol["modelRegistry"])
    model_ids = set(q._models(registry))
    matrix = q.required_matrix(protocol, model_ids)
    assert model_ids == {
        "qwen3-30b-a3b-2507-abliterated",
        "qwen3-30b-a3b-2507-control",
    }
    assert len(matrix) == 4
    assert all("qwen3.8-27b" not in model_id for model_id, _ in matrix)
    assert {track for _, track in matrix} == {"neutral-deterministic", "neutral-sampled"}


def test_comparison_template_matches_active_protocol_matrix():
    protocol = q.read_json(q.DEFAULT_PROTOCOL)
    registry = q.read_json(q.ROOT / protocol["modelRegistry"])
    template = q.read_json(q.ROOT / "config/t2-comparison-inputs.template.json")
    actual = {(run["modelId"], run["trackId"]) for run in template["runs"]}

    assert template["protocolId"] == protocol["protocolId"]
    assert actual == q.required_matrix(protocol, set(q._models(registry)))
    assert all("qwen3.8-27b" not in model_id for model_id, _ in actual)


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
