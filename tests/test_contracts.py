"""Offline Establish-contract tests; no inference, downloads, or paid compute."""
import json
from pathlib import Path

import pytest

from veronica_core import contracts as c
from veronica_core.config import Settings


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def valid_module_manifest() -> dict:
    return {
        "schemaVersion": 1,
        "id": "general-assistant",
        "name": "General Assistant",
        "version": "0.0.0",
        "status": "planned",
        "publicAlias": "Veronica",
        "description": "Conversation, questions, planning, and summaries through the Veronica alias.",
        "capabilities": ["conversation", "questions", "planning", "summaries"],
        "tools": [],
        "knowledgeScope": "session",
        "adapter": None,
        "bindsToFoundationRepository": False,
        "removableWithoutCoreDamage": True,
        "tests": [],
    }


def test_canonical_registry_and_suite_match_schemas():
    result = c.validate_canonical_contracts()
    assert result["ok"] is True
    assert result["issues"] == []
    assert result["paidComputeStarted"] is False
    assert {row["schema"] for row in result["validated"] if row["role"] == "schema"} == set(c.SCHEMA_NAMES)


def test_run_record_status_enum_matches_workflow_states():
    schema = c.load_schema("run-record")
    assert schema["properties"]["status"]["enum"] == c.read_json(ROOT / "config/status-states.json")["states"]


def test_invalid_run_record_and_module_binding_are_rejected():
    with pytest.raises(c.SchemaError, match="missing required property"):
        c.validate_instance("run-record", {"schemaVersion": 1, "runId": "bad", "status": "completed"})
    manifest = valid_module_manifest()
    manifest["bindsToFoundationRepository"] = True
    with pytest.raises(c.SchemaError):
        c.validate_instance("module-manifest", manifest)
    manifest = valid_module_manifest()
    manifest["publicAlias"] = "Qwen3"
    with pytest.raises(c.SchemaError):
        c.validate_instance("module-manifest", manifest)
    c.validate_instance("module-manifest", valid_module_manifest())


def test_evaluation_schema_rejects_unknown_check_kind():
    suite = c.read_json(ROOT / "data/evals/veronica-core-v1.json")
    suite["cases"][0]["turns"][0]["checks"].append({"kind": "pretend_semantic_pass"})
    with pytest.raises(c.SchemaError):
        c.validate_instance("evaluation-case", suite)


def test_fingerprint_is_stable_and_omits_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("VERONICA_UPSTREAM_API_KEY", "super-secret-key")
    source = tmp_path / "profile.json"
    write_json(source, {
        "publicAlias": "Veronica",
        "apiKey": "super-secret-key",
        "runtime": {"vllmVersion": "0.11.0", "privateKeyFile": "/tmp/key.json"},
        "token": "abcd",
    })
    first = c.generate_fingerprint([source], include_identity=False, root=tmp_path)
    second = c.generate_fingerprint([source], include_identity=False, root=tmp_path)
    dumped = json.dumps(first)
    assert first["digest"] == second["digest"]
    assert first["secretsOmitted"] is True
    assert first["paidComputeStarted"] is False
    assert "super-secret-key" not in dumped
    assert "/tmp/key.json" not in dumped
    assert any(key.endswith("apiKey") or "apiKey" in key for key in first["redactedKeys"])
    mutated = tmp_path / "mutated.json"
    write_json(mutated, {"publicAlias": "Veronica", "runtime": {"vllmVersion": "0.12.0"}})
    changed = c.generate_fingerprint([mutated], include_identity=False, root=tmp_path)
    assert changed["digest"] != first["digest"]


def test_default_fingerprint_identity_matches_wrapper_defaults(monkeypatch):
    monkeypatch.delenv("VERONICA_UPSTREAM_API_KEY", raising=False)
    monkeypatch.delenv("VERONICA_PUBLIC_MODEL", raising=False)
    monkeypatch.delenv("VERONICA_UPSTREAM_MODEL", raising=False)
    settings = Settings.from_environment()
    identity = c.identity_block()
    assert identity["publicAlias"] == "Veronica"
    assert identity["publicModel"] == settings.public_model
    assert identity["upstreamModel"] == settings.upstream_model
    assert "upstream_api_key" not in json.dumps(identity)
    result = c.generate_fingerprint()
    assert len(result["digest"]) == 64
    assert result["identityIncluded"] is True


def test_init_run_folder_creates_stubs_and_refuses_overwrite(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    created = c.init_run_folder(
        "2026-09-04-contract-test",
        stage="establish",
        scope="Contract initializer test.",
        runs_root=runs,
        fingerprint=False,
        root=tmp_path,
    )
    record = c.read_json(created / "run.json")
    c.validate_instance("run-record", record)
    assert record["runId"] == "2026-09-04-contract-test"
    assert record["paidGpuStarted"] is False
    assert (created / "decision.md").is_file()
    for name in c.REQUIRED_RUN_DIRS:
        assert (created / name).is_dir()
    with pytest.raises(FileExistsError, match="must not be overwritten"):
        c.init_run_folder("2026-09-04-contract-test", runs_root=runs, fingerprint=False, root=tmp_path)
    with pytest.raises(ValueError):
        c.init_run_folder("../escape", runs_root=runs, fingerprint=False, root=tmp_path)
    with pytest.raises(ValueError):
        c.init_run_folder("has/slash", runs_root=runs, fingerprint=False, root=tmp_path)


def test_init_run_folder_can_embed_configuration_fingerprint(tmp_path):
    write_json(tmp_path / "config/model-registry.json", {"publicAlias": "Veronica"})
    write_json(tmp_path / "config/runpod-core.json", {"runtime": {"vllmVersion": "0.11.0"}})
    write_json(tmp_path / "config/workflow.json", {"projectName": "Veronica.v4"})
    write_json(tmp_path / "config/status-states.json", {"states": ["hold"]})
    runs = tmp_path / "runs"
    runs.mkdir()
    created = c.init_run_folder("2026-09-04-fp", runs_root=runs, fingerprint=True, root=tmp_path)
    record = c.read_json(created / "run.json")
    fingerprint = c.read_json(created / "configuration-fingerprint.json")
    assert record["configurationFingerprint"] == fingerprint["digest"]
    assert fingerprint["secretsOmitted"] is True


def test_provenance_reports_missing_readme_license_and_revision(tmp_path):
    snapshot = tmp_path / "prov" / "ok"
    snapshot.mkdir(parents=True)
    (snapshot / "README.md").write_text("card\n", encoding="utf-8")
    (snapshot / "LICENSE").write_text("Apache License Version 2.0\n", encoding="utf-8")
    missing = tmp_path / "prov" / "missing"
    missing.mkdir()
    registry = {
        "candidates": [{
            "id": "good",
            "repository": "org/model",
            "role": "candidate",
            "licenseDeclared": "Apache-2.0",
            "revision": "a" * 40,
            "provenanceSnapshot": "prov/ok",
        }],
        "controls": [{
            "id": "bad",
            "repository": "org/control",
            "role": "official_control",
            "licenseDeclared": "Apache-2.0",
            "revision": "not-a-sha",
            "provenanceSnapshot": "prov/missing",
        }],
    }
    path = tmp_path / "registry.json"
    write_json(path, registry)
    result = c.check_license_provenance(path, tmp_path)
    assert result["ok"] is False
    assert result["networkAccess"] is False
    assert result["weightsDownloaded"] is False
    assert result["paidComputeStarted"] is False
    by_id = {row["id"]: row for row in result["models"]}
    assert by_id["good"]["complete"] is True
    assert by_id["bad"]["revision"] == "invalid"
    assert by_id["bad"]["readme"] == "missing"
    assert by_id["bad"]["license"] == "missing"
    assert any("README.md" in issue for issue in result["issues"])
    assert any("revision" in issue for issue in result["issues"])


def test_current_registry_snapshots_satisfy_provenance_checklist():
    result = c.check_license_provenance()
    assert result["ok"] is True
    assert result["checked"] == 4
    assert result["complete"] == 4
    assert result["weightsDownloaded"] is False
    assert result["paidComputeStarted"] is False


def test_contracts_module_does_not_import_network_clients():
    source = Path(c.__file__).read_text(encoding="utf-8")
    for banned in ("urllib", "httpx", "requests", "runpodctl", "urlopen"):
        assert banned not in source


def test_project_validator_and_local_verify_wire_schema_scripts():
    validator = (ROOT / "scripts/validate-project.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "scripts/verify-local.ps1").read_text(encoding="utf-8")
    for name in c.SCHEMA_NAMES:
        assert f"config/schemas/{name}.schema.json" in validator
    assert "scripts/validate_contracts.py" in verify
    assert "scripts/check_license_provenance.py" in verify
