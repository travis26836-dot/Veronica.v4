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
