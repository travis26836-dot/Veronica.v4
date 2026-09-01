"""Offline checks for paid-resource gates and model integrity."""
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_script("runpod_core")
bootstrap = load_script("prepare_runpod_model")
with patch.dict(sys.modules, {"runpod_core": core}):
    supervised = load_script("supervised_runpod")


@pytest.mark.parametrize("hourly,minutes", [(float("nan"), 120), (float("inf"), 120), (-1, 120), (1.6, 0), (1.6, 1441)])
def test_rejects_unbounded_or_invalid_spending(hourly, minutes):
    with pytest.raises(ValueError):
        core.validate_limits(hourly, minutes)


def test_legacy_timer_flag_does_not_authorize_creation():
    profile = core.profile_at(core.DEFAULT_PROFILE)
    def fake_cli(*args):
        if args == ("network-volume", "get", "v53gj9flzs"):
            return json.dumps({"id": "v53gj9flzs", "dataCenterId": "EUR-IS-1", "size": 300})
        if args == ("gpu", "list", "--include-unavailable"):
            return json.dumps([{"gpuId": profile["pod"]["gpuTypeId"], "securePricePerHr": 1.59, "dataCenterAvailability": [{"dataCenterId": "EUR-IS-1", "stockStatus": "Low"}]}])
        if args == ("pod", "list", "--all"):
            return "[]"
        if args == ("ssh", "list-keys"):
            return '{"keys":[{"name":"test"}]}'
        if args == ("pod", "create", "--help"):
            return "--terminate-after"
        if args == ("version",):
            return "test-version"
        raise AssertionError(f"Unexpected/mutating command: {args}")
    with patch.object(core, "cli", fake_cli):
        result = core.preflight(profile, 1.6, 120)
        assert not result["safeToCreate"]
        assert any("termination" in item for item in result["blockers"])
        assert core.preflight(profile, 1.6, 120, supervised=True)["safeToCreate"]
        assert not core.preflight(profile, 1.5, 120, supervised=True)["safeToCreate"]
        with patch("sys.argv", ["runpod_core.py", "start", "--max-hourly-usd", "1.60", "--duration-minutes", "120"]):
            with pytest.raises(RuntimeError, match="No Pod created"):
                core.main()


def test_duration_selection_defaults_to_one_hour_and_offers_custom_window():
    profile = core.profile_at(core.DEFAULT_PROFILE)
    output = []
    assert core.choose_duration(profile, input_func=lambda _: "", output_func=output.append) == 60
    answers = iter(["4", "3.5"])
    assert core.choose_duration(profile, input_func=lambda _: next(answers), output_func=output.append) == 210
    assert any("1 hour (default)" in line for line in output)


def test_duration_policy_requires_one_two_three_hour_presets():
    profile = core.read_json(core.DEFAULT_PROFILE)
    profile["safety"]["presetDurationMinutes"] = [60, 90, 180]
    with pytest.raises(ValueError, match="exactly one, two, and three"):
        core.duration_policy(profile)


def approval_for(profile, run):
    return {"runId": run.name, "maxHourlyUsd": 1.6, "durationMinutes": 120,
            "resourceCount": 1, "shutdownMode": "supervised-with-local-backup",
            "authorizedAtUtc": datetime.now(timezone.utc).isoformat(),
            "modelRevision": profile["model"]["revision"], "networkVolumeId": profile["pod"]["networkVolumeId"],
            "gpuTypeId": profile["pod"]["gpuTypeId"]}


def test_supervised_approval_is_current_scoped_and_one_shot(tmp_path):
    profile = core.profile_at(core.DEFAULT_PROFILE)
    approval = approval_for(profile, tmp_path)
    supervised.validate_approval(approval, profile, tmp_path)
    with pytest.raises(ValueError, match="current"):
        supervised.validate_approval(approval, profile, tmp_path, datetime.now(timezone.utc) + timedelta(hours=3))
    for field, value in [("resourceCount", 2), ("shutdownMode", "automatic"), ("modelRevision", "wrong"), ("gpuTypeId", "different")]:
        with pytest.raises(ValueError):
            supervised.validate_approval({**approval, field: value}, profile, tmp_path)
    (tmp_path / "supervised-state.json").write_text("{}")
    with pytest.raises(ValueError, match="already used"):
        supervised.validate_approval(approval, profile, tmp_path)


def test_termination_never_selects_unrelated_or_mismatched_pod():
    state = {"podName": "veronica-core-owned", "podId": "owned123"}
    with patch.object(core, "cli", return_value=json.dumps([{"id": "other", "name": "veronica-core-other"}])):
        assert supervised.owned_pods(state) == []
    with patch.object(core, "cli", return_value=json.dumps([{"id": "other", "name": state["podName"]}])):
        with pytest.raises(RuntimeError, match="does not match"):
            supervised.owned_pods(state)
    with patch.object(core, "cli", return_value=json.dumps([{"id": state["podId"], "name": "renamed"}])):
        with pytest.raises(RuntimeError, match="renamed"):
            supervised.owned_pods(state)


def test_watchdog_uses_fixed_deadline_and_verifies_absence(tmp_path):
    supervised.write(tmp_path / "supervised-state.json", {"podName": "veronica-core-owned", "podId": "abc123",
        "backupShutdownAtUtc": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()})
    responses = [json.dumps([{"id": "abc123", "name": "veronica-core-owned"}]), "", "[]"]
    with patch.object(core, "cli", side_effect=responses) as cli:
        supervised.watchdog(tmp_path)
    assert ("pod", "delete", "abc123") in [call.args for call in cli.call_args_list]
    assert core.read_json(tmp_path / "termination.json")["confirmedAbsent"]


def test_content_corruption_fails_even_when_size_matches(tmp_path):
    original = b"verified weights"
    target = tmp_path / "model.safetensors"
    target.write_bytes(original)
    manifest = {"files": [{"path": target.name, "bytes": len(original), "sha256": hashlib.sha256(original).hexdigest(), "gitBlob": "unused"}]}
    assert bootstrap.verify_files(tmp_path, manifest)[0]["sha256"] == hashlib.sha256(original).hexdigest()
    target.write_bytes(b"X" * len(original))
    with pytest.raises(ValueError, match="Checksum mismatch"):
        bootstrap.verify_files(tmp_path, manifest)


@pytest.mark.parametrize("public_port", [True, False])
def test_profile_cannot_expose_development_inference_publicly(tmp_path, public_port):
    profile = core.read_json(core.DEFAULT_PROFILE)
    if public_port:
        profile["pod"]["ports"].append("8000/http")
    else:
        profile["runtime"]["host"] = "0.0.0.0"
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile))
    with pytest.raises(ValueError, match="SSH only"):
        core.profile_at(path)


def test_artifact_path_cannot_escape_staging(tmp_path):
    with pytest.raises(ValueError, match="Unsafe artifact"):
        bootstrap.validated_path(tmp_path, "../model.safetensors")


def test_non_lfs_metadata_uses_git_blob_hash(tmp_path):
    content = b'{"model_type":"qwen3_moe"}'
    (tmp_path / "config.json").write_bytes(content)
    git_blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
    manifest = {"files": [{"path": "config.json", "bytes": len(content), "sha256": None, "gitBlob": git_blob}]}
    assert len(bootstrap.verify_files(tmp_path, manifest)) == 1


def test_only_reviewed_vllm_parser_arguments_are_accepted():
    assert bootstrap.validated_server_arguments({"serverArguments": [
        "--enable-auto-tool-choice", "--tool-call-parser", "hermes"
    ]}) == ["--enable-auto-tool-choice", "--tool-call-parser", "hermes"]
    assert bootstrap.validated_server_arguments({"serverArguments": [
        "--reasoning-parser", "qwen3", "--tool-call-parser", "qwen3_coder"
    ]}) == ["--reasoning-parser", "qwen3", "--tool-call-parser", "qwen3_coder"]
    for arguments in (["--served-model-name", "fake"], ["--tool-call-parser", "evil"],
                      ["--reasoning-parser"], ["--enable-auto-tool-choice", "--enable-auto-tool-choice"]):
        with pytest.raises(ValueError):
            bootstrap.validated_server_arguments({"serverArguments": arguments})
