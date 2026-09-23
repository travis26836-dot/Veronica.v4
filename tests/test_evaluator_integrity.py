"""CP3 evaluator-integrity checks without model or paid-resource access."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from veronica_core import evaluation as ev
from veronica_core import execution_sandbox as sandbox_module


def _suite():
    return {
        "schema_version": 1,
        "suite_id": "cp3-integrity",
        "cases": [{
            "id": "CP3-01", "family": "integrity", "category": "grounding",
            "tier": "smoke", "release_blocker": True, "context": "fixture",
            "turns": [{"user": "Answer.", "checks": [], "rubric": ["Review the raw answer."]}],
        }],
    }


def _args(tmp_path: Path, suite_path: Path, runtime_path: Path, **overrides):
    values = {
        "execute": True, "base_url": "http://127.0.0.1:9999/v1", "allow_remote": False,
        "temperature": 0, "top_p": 1, "thinking": "disabled", "max_seconds": 10,
        "timeout_seconds": 5, "runtime_record": runtime_path, "api_key_env": "CP3_TEST_KEY",
        "run_dir": tmp_path / "results", "suite": suite_path, "surface": "direct",
        "model": "Veronica", "mode": "chat", "seed": 1, "repeats": 1, "max_tokens": 10,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_runtime_provenance_requires_pinned_identity_before_network(tmp_path, monkeypatch):
    suite_path = tmp_path / "suite.json"
    runtime_path = tmp_path / "runtime.json"
    ev.write_json(suite_path, _suite())
    ev.write_json(runtime_path, {"model": {"repository": "fixture"}})

    class NetworkMustNotRun:
        def __init__(self, **kwargs):
            raise AssertionError("network was reached before provenance validation")

    monkeypatch.setattr(ev.httpx, "Client", NetworkMustNotRun)
    with pytest.raises(ValueError, match="repository and revision"):
        ev.collect(_args(tmp_path, suite_path, runtime_path), _suite(), _suite()["cases"], ev.plan(_suite()["cases"], 1, 10, 10, 100))


def test_raw_response_hash_and_redaction_are_retained(tmp_path, monkeypatch):
    suite_data = _suite()
    suite_path = tmp_path / "suite.json"
    runtime_path = tmp_path / "runtime.json"
    ev.write_json(suite_path, suite_data)
    ev.write_json(runtime_path, {"schemaVersion": 1, "model": {"repository": "fixture/model", "revision": "fixture-revision"}, "apiKey": "must-not-copy"})
    secret = "cp3-api-secret"
    monkeypatch.setenv("CP3_TEST_KEY", secret)
    raw_body = json.dumps({
        "api_key": secret,
        "choices": [{"message": {"role": "assistant", "content": "raw answer"}}],
    }).encode()

    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "Veronica"}]})
        return httpx.Response(200, content=raw_body, headers={"content-type": "application/json"})

    actual_client = httpx.Client
    monkeypatch.setattr(ev.httpx, "Client", lambda **kwargs: actual_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(ev, "new_run", lambda path: (path.mkdir(), path)[1])
    result = ev.collect(_args(tmp_path, suite_path, runtime_path), suite_data, suite_data["cases"], ev.plan(suite_data["cases"], 1, 10, 10, 100))
    record = ev.read_jsonl(tmp_path / "results" / "results.jsonl")[0]
    manifest = ev.read_json(tmp_path / "results" / "manifest.json")

    assert result["gate"] == "human_review_pending"
    assert record["status"] == "response"
    assert record["raw_response"]
    assert record["raw_response_sha256"] == hashlib.sha256(raw_body).hexdigest()
    assert secret not in json.dumps(record)
    assert "raw answer" in record["raw_response"]
    assert manifest["runtime_record_sha256"] == ev.fingerprint(runtime_path)
    assert manifest["identity"] == {"repository": "fixture/model", "revision": "fixture-revision"}
    assert secret not in (tmp_path / "results" / "manifest.json").read_text()


def test_credential_shaped_text_is_redacted_without_a_known_environment_secret():
    evidence = ev._redact_evidence('{"password":"embedded-value","message":"keep this"}')
    assert "embedded-value" not in evidence
    assert "keep this" in evidence


def test_sandbox_retains_untrusted_worker_bytes_alongside_host_score(monkeypatch):
    sandbox = sandbox_module.DockerSandbox()
    sandbox.attestation = {"verified": True}
    raw = '{"phase":"call","value":42,"args_after":[]}'

    monkeypatch.setattr(sandbox, "_execute", lambda *args: {
        "ok": True, "error": None, "cleanup_verified": True, "container": "unit-test",
        "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "observation": {"phase": "call", "value": 42, "args_after": []},
    })
    result = sandbox.run_fixture("def answer(): return 42", {
        "function": "answer", "vectors": [{"id": "v", "args": [], "expect": {"equals": 42}}],
    })

    execution = result["executions"][0]
    assert result["vectors"][0]["passed"] is True
    assert execution["raw_output"] == raw
    assert execution["raw_output_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
    assert execution["cleanup_verified"] is True
