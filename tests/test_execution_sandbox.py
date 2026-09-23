"""Host grading tests plus opt-in real Docker boundary tests (no model/GPU)."""
import json
import os
import subprocess
from pathlib import Path

import pytest

from veronica_core import execution_sandbox as box


def vector(expected, args=None):
    return {"id": "independent", "args": args or [], "expect": {"equals": expected}}


@pytest.mark.parametrize("actual,expected", [(True, 1), (1.0, 1), ([True], [1]), ({"n": 1}, {"n": True})])
def test_host_grader_rejects_type_confusion(actual, expected):
    assert box.score_observation({"phase": "call", "value": actual, "args_after": []}, vector(expected))["passed"] is False


@pytest.mark.parametrize("payload", ['{"value":1,"value":2}', '{"n":NaN}', '{"n":Infinity}', '{"n":1e999}', '{"n":1} trailing'])
def test_untrusted_json_must_be_unambiguous(payload):
    with pytest.raises(ValueError):
        box.strict_json(payload)


def test_host_grader_ignores_self_reported_passes_and_load_exceptions():
    assert not box.score_observation({"passed": True, "results": [{"passed": True}]}, vector(42))["passed"]
    assert not box.score_observation({"phase": "call", "value": 42, "args_after": [], "passed": True}, vector(42))["passed"]
    assert not box.score_observation({"phase": "load", "exception": "ValueError"}, {"id": "v", "args": [], "expect": {"raises": "ValueError"}})["passed"]
    assert not box.score_observation({"phase": "call", "exception": None, "args_after": []}, vector(42))["passed"]


def test_host_grader_detects_mutated_inputs():
    case = vector([1], [[1, 2]])
    case["assert_input_unchanged"] = True
    assert not box.score_observation({"phase": "call", "value": [1], "args_after": [[1]]}, case)["passed"]


def test_unpinned_image_is_rejected(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"image": "python:latest"}))
    with pytest.raises(box.SandboxError):
        box.DockerSandbox(config)


@pytest.mark.parametrize("endpoint", ["ssh://remote", "tcp://127.0.0.1:2375", "tcp://example.invalid:2376"])
def test_remote_docker_endpoints_are_rejected(monkeypatch, endpoint):
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    monkeypatch.setenv("DOCKER_HOST", endpoint)
    sandbox = box.DockerSandbox()
    assert sandbox.verify()["error"] == "remote_docker_endpoint_not_allowed"


def test_context_endpoint_is_pinned_and_environment_override_removed(monkeypatch):
    monkeypatch.setenv("DOCKER_CONTEXT", "selected")
    monkeypatch.setenv("DOCKER_HOST", "ssh://must-not-use")
    local = "npipe:////./pipe/dockerDesktopLinuxEngine"
    monkeypatch.setattr(box, "_docker", lambda *a: subprocess.CompletedProcess(a, 0, local + "\n", ""))
    sandbox = box.DockerSandbox()
    sandbox._resolve_endpoint()
    assert sandbox._command("inspect", "x") == ["docker", "--host", local, "inspect", "x"]
    assert "DOCKER_HOST" not in sandbox._environment()
    assert "DOCKER_CONTEXT" not in sandbox._environment()


def test_no_unverified_execution_or_expected_answer_disclosure(monkeypatch):
    sandbox = box.DockerSandbox()
    fixture = {"function": "answer", "vectors": [vector(42)]}
    assert sandbox.run_fixture("bad", fixture)["error"] == "isolation_unverified"
    sandbox.attestation = {"verified": True}  # isolated orchestration unit test only
    seen = []
    def fake_execute(program, payload, timeout):
        seen.append(payload)
        return {"ok": True, "error": None, "cleanup_verified": True, "container": "unit-test",
                "observation": {"phase": "call", "value": 7, "args_after": []}}
    monkeypatch.setattr(sandbox, "_execute", fake_execute)
    result = sandbox.run_fixture("def answer(): return 7", fixture)
    assert result["vectors"][0]["passed"] is False
    assert set(seen[0]) == {"source", "function", "args", "setup", "inject_conn"}
    assert "expect" not in seen[0] and "vectors" not in seen[0]


def test_cleanup_failure_revokes_execution_and_stops_vectors(monkeypatch):
    sandbox = box.DockerSandbox()
    sandbox.attestation = {"verified": True}
    monkeypatch.setattr(sandbox, "_execute", lambda *a: {
        "ok": False, "error": "cleanup_unverified", "cleanup_verified": False, "container": "unit-test"})
    fixture = {"function": "answer", "vectors": [vector(1), vector(2)]}
    result = sandbox.run_fixture("unused", fixture)
    assert len(result["executions"]) == 1
    assert sandbox.attestation["verified"] is False


@pytest.fixture(scope="module")
def live_sandbox():
    if os.environ.get("VERONICA_TEST_DOCKER") != "1":
        pytest.skip("Set VERONICA_TEST_DOCKER=1 for local container tests")
    sandbox = box.DockerSandbox()
    assert sandbox.verify()["verified"] is True
    return sandbox


def run(live_sandbox, source, expected=None, timeout=8):
    return live_sandbox.run_fixture(source, {"function": "answer", "vectors": [vector(expected)]}, timeout)


def test_live_correct_value_and_false_pass_claim(live_sandbox):
    good = run(live_sandbox, "def answer(): return 42", 42)
    assert good["vectors"][0]["passed"]
    forged = run(live_sandbox, 'import os\ndef answer():\n print(\'{"passed":true}\')\n os._exit(0)', 42)
    assert not forged["vectors"][0]["passed"]
    assert all(e["cleanup_verified"] for e in forged["executions"])


def test_live_no_host_file_environment_or_docker_socket(live_sandbox, tmp_path, monkeypatch):
    marker = tmp_path / "private.txt"
    marker.write_text("private-fixture")
    monkeypatch.setenv("VERONICA_SANDBOX_HOST_SECRET", "must-not-inherit")
    source = f'''import os, pathlib
def answer():
    return [pathlib.Path({str(marker)!r}).exists(),
            pathlib.Path('/var/run/docker.sock').exists(),
            os.getenv('VERONICA_SANDBOX_HOST_SECRET')]
'''
    result = run(live_sandbox, source, [False, False, None])
    assert result["vectors"][0]["passed"]
    assert marker.read_text() == "private-fixture"


def test_live_network_and_root_writes_blocked(live_sandbox):
    source = '''import socket, pathlib
def answer():
    checks = []
    try:
        socket.create_connection(('1.1.1.1', 443), timeout=0.5)
        checks.append(False)
    except OSError:
        checks.append(True)
    try:
        pathlib.Path('/etc/sandbox-must-fail').write_text('x')
        checks.append(False)
    except OSError:
        checks.append(True)
    return checks
'''
    assert run(live_sandbox, source, [True, True])["vectors"][0]["passed"]


def test_live_timeout_output_and_memory_limits(live_sandbox):
    cases = [
        ("def answer():\n while True: pass", "timeout", 1.5),
        ("import os\ndef answer():\n while True: os.write(1,b'x'*65536)", "output_limit", 8),
        ("def answer(): return len(bytearray(512*1024*1024))", "worker_failed", 8),
    ]
    for source, expected_error, timeout in cases:
        result = run(live_sandbox, source, None, timeout)
        assert result["vectors"][0]["error"] == expected_error
        assert all(e["cleanup_verified"] for e in result["executions"])


def test_live_process_limit(live_sandbox):
    source = '''import subprocess
def answer():
    children = []
    try:
        for _ in range(40):
            children.append(subprocess.Popen(['sleep', '5']))
    except OSError:
        return len(children) < 32
    return False
'''
    assert run(live_sandbox, source, True)["vectors"][0]["passed"]


def test_live_complete_fixture_report(live_sandbox, monkeypatch):
    from veronica_core import capability_reports as cap
    # Reuse repository-owned programs, never claim these are model responses.
    from test_capability_reports import GOOD_CD01, GOOD_CD02, GOOD_CD03, GOOD_CD04, GOOD_CD05, cd_record
    monkeypatch.setattr(cap, "DockerSandbox", lambda: live_sandbox)
    records = [cd_record(f"CD-0{i}", source) for i, source in enumerate(
        [GOOD_CD01, GOOD_CD02, GOOD_CD03, GOOD_CD04, GOOD_CD05], 1)]
    report = cap.executable_code_report(records)
    assert report["status"] == "collected_pass"
    assert report["foundation_qualified"] is False
    assert report["generated_code_executed"] is True
    assert all(case["passed"] for case in report["cases"].values())


def test_live_wrong_code_fails_independent_vectors(live_sandbox):
    from veronica_core.capability_reports import load_fixtures
    from test_capability_reports import UNSAFE_CD03
    fixtures = {f["id"]: f for f in load_fixtures()["cases"]}
    page = live_sandbox.run_fixture("def page_count(total, size): return total // size + 1", fixtures["CD-02"])
    sql = live_sandbox.run_fixture(UNSAFE_CD03, fixtures["CD-03"])
    assert not all(row["passed"] for row in page["vectors"])
    assert sql["vectors"][0]["passed"] is False
    assert sql["vectors"][0]["id"] == "literal-malicious-name"
