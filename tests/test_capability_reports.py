"""Post-hoc T2 capability reports without live inference or paid compute."""
from pathlib import Path

from veronica_core import capability_reports as cap
from veronica_core import evaluation as ev


FROZEN_SUITE_SHA = "ce1644f045953b66cd9b98883570d7404cac832cf06a6085453259af86aecf90"

GOOD_CD01 = """
def unique_in_order(items):
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out

assert unique_in_order([3, 1, 3, 2, 1]) == ['MODEL_WRONG']
"""

GOOD_CD02 = """
def page_count(total, size):
    if type(total) is not int or type(size) is not int or total < 0 or size <= 0:
        raise ValueError('invalid')
    if total == 0:
        return 0
    return (total + size - 1) // size
"""

GOOD_CD03 = """
def find_user(conn, display_name):
    return conn.execute('SELECT id, display_name FROM users WHERE display_name = ?', (display_name,)).fetchall()
"""

UNSAFE_CD03 = """
def find_user(conn, display_name):
    return conn.execute("SELECT id, display_name FROM users WHERE display_name = '%s'" % display_name).fetchall()
"""

GOOD_CD04 = """
def rank_records(records):
    return sorted(records, key=lambda row: row['score'], reverse=True)
"""

GOOD_CD05 = """
import json

def parse_count(text):
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError('invalid') from exc
    if type(value) is not dict or set(value) != {'count'} or type(value['count']) is not int or value['count'] < 0:
        raise ValueError('invalid')
    return value['count']
"""


def so_record(case_id, content, checks, status="response"):
    message = {"role": "assistant", "content": content}
    return {
        "sample_id": f"{case_id}.r1.t1",
        "case_id": case_id,
        "category": "structured-output",
        "family": case_id,
        "status": status,
        "message": message,
        "automatic_checks": ev.automatic_checks(message, checks) if status == "response" else [],
    }


def ts_record(case_id, message, checks, status="response"):
    return {
        "sample_id": f"{case_id}.r1.t1",
        "case_id": case_id,
        "category": "tool-selection",
        "family": case_id,
        "status": status,
        "message": message,
        "automatic_checks": ev.automatic_checks(message, checks) if status == "response" else [],
    }


def cd_record(case_id, source, status="response"):
    content = f"```python\n{source}\n```\nI did not execute these tests."
    message = {"role": "assistant", "content": content}
    return {
        "sample_id": f"{case_id}.r1.t1",
        "case_id": case_id,
        "category": "coding",
        "family": case_id,
        "status": status,
        "message": message,
        "automatic_checks": ev.automatic_checks(message, [{"kind": "no_tool_calls"}]) if status == "response" else [],
    }


def test_frozen_suite_hash_and_no_long_context_cases():
    assert ev.fingerprint(ev.DEFAULT_SUITE) == FROZEN_SUITE_SHA
    suite = ev.read_json(ev.DEFAULT_SUITE)
    assert len(suite["cases"]) == 60
    assert not any(str(case["id"]).startswith("LC-") for case in suite["cases"])


def test_schema_report_not_collected_without_so_samples():
    report = cap.schema_report([cd_record("CD-01", GOOD_CD01)])
    assert report["status"] == "not_collected"
    assert report["tools_executed"] is False


def test_schema_report_rolls_up_json_equals_and_json_keys():
    equals = so_record("SO-01", '{"name":"Veronica","connected":false,"pending":[]}', [
        {"kind": "json_equals", "value": {"name": "Veronica", "connected": False, "pending": []}},
        {"kind": "no_tool_calls"},
    ])
    keys = so_record("SO-02", '{"project":"Cedar","owner":"Raine","deadline":null}', [
        {"kind": "json_keys", "required": ["project", "owner", "deadline"]},
        {"kind": "json_equals", "value": {"project": "Cedar", "owner": "Raine", "deadline": None}},
    ])
    report = cap.schema_report([equals, keys])
    assert report["status"] == "incomplete"
    assert report["cases"]["SO-01"]["passed"] is True
    assert report["cases"]["SO-02"]["samples"][0]["checks"]["json_keys"]["passed"] == 1
    assert report["passed_checks"] >= 3
    assert report["cases"]["SO-01"]["samples"][0]["checks"]["json_equals"]["passed"] == 1


def test_schema_report_fails_on_bad_json():
    record = so_record("SO-01", '{"name":"Veronica"}', [
        {"kind": "json_equals", "value": {"name": "Veronica", "connected": False, "pending": []}},
    ])
    report = cap.schema_report([record])
    assert report["status"] == "collected_fail"
    assert report["failed_checks"] == 1


def test_native_tool_report_never_marks_tools_executed():
    call = {"type": "function", "function": {"name": "multiply", "arguments": '{"a":17,"b":23}'}}
    required = ts_record("TS-01", {"content": None, "tool_calls": [call]}, [
        {"kind": "tool_call", "name": "multiply", "arguments": {"a": 17, "b": 23}},
    ])
    avoided = ts_record("TS-02", {"content": "Hello there", "tool_calls": []}, [
        {"kind": "no_tool_calls"},
    ])
    report = cap.native_tool_report([required, avoided])
    assert report["tools_executed"] is False
    assert report["cases"]["TS-01"]["passed"] is True
    assert report["cases"]["TS-02"]["passed"] is True
    assert report["status"] == "incomplete"


def test_native_tool_report_prose_is_not_a_tool_call():
    record = ts_record("TS-01", {"content": 'I called multiply(a=17, b=23)'}, [
        {"kind": "tool_call", "name": "multiply", "arguments": {"a": 17, "b": 23}},
    ])
    report = cap.native_tool_report([record])
    assert report["status"] == "collected_fail"
    assert report["tools_executed"] is False


def test_collect_never_executes_generated_code(tmp_path):
    marker = tmp_path / "marker.txt"
    payload = f"open(r'{marker}', 'w').write('ran')\ndef unique_in_order(items):\n    return list(items)\n"
    reports = cap.collect([cd_record("CD-01", payload)])
    assert reports["executable_code"]["status"] == "skipped"
    assert reports["executable_code"]["generated_code_executed"] is False
    assert reports["native_tools"]["tools_executed"] is False
    assert not marker.exists()
    assert ev.plan([{"id": "x", "category": "coding", "turns": [{"user": "u", "checks": [], "rubric": ["r"]}]}], 1, 10, 10, 100)["executes_tools_or_generated_code"] is False


def test_executable_fixtures_match_case_notes():
    fixtures = cap.load_fixtures()
    by_id = {case["id"]: case for case in fixtures["cases"]}
    assert by_id["CD-01"]["function"] == "unique_in_order"
    cd01 = {row["id"]: row for row in by_id["CD-01"]["vectors"]}
    assert cd01["empty"]["expect"]["equals"] == []
    assert cd01["ints-order"]["args"] == [[3, 1, 3, 2, 1]]
    assert cd01["ints-order"]["expect"]["equals"] == [3, 1, 2]
    assert cd01["strings"]["expect"]["equals"] == ["a", "b"]
    cd02 = {row["id"]: row for row in by_id["CD-02"]["vectors"]}
    assert cd02["zero-items"]["expect"]["equals"] == 0
    assert cd02["exact-multiple"]["expect"]["equals"] == 2
    assert cd02["partial-page"]["expect"]["equals"] == 3
    for key in ("neg-total", "zero-size", "neg-size", "float-size", "str-total", "bool-total"):
        assert cd02[key]["expect"]["raises"] == "ValueError"
    assert cd02["bool-total"]["args"][0] is True
    cd04 = by_id["CD-04"]["vectors"][0]
    assert [row["name"] for row in cd04["expect"]["equals"]] == ["B", "A", "C"]
    cd05 = {row["id"]: row for row in by_id["CD-05"]["vectors"]}
    assert cd05["valid-zero"]["expect"]["equals"] == 0
    assert cd05["boolean-count"]["expect"]["raises"] == "ValueError"


def test_execute_code_uses_fixtures_not_model_written_tests():
    report = cap.executable_code_report([
        cd_record("CD-01", GOOD_CD01),
        cd_record("CD-02", GOOD_CD02),
        cd_record("CD-03", GOOD_CD03),
        cd_record("CD-04", GOOD_CD04),
        cd_record("CD-05", GOOD_CD05),
    ])
    assert report["execute_code"] is True
    assert report["tools_executed"] is False
    assert report["generated_code_executed"] is True
    assert report["missing_case_ids"] == []
    assert all(report["cases"][case_id]["passed"] for case_id in report["expected_case_ids"])
    if report["isolation"]["verified"]:
        assert report["status"] == "collected_pass"
    else:
        assert report["status"] == "isolation_unverified"


def test_execute_code_status_is_isolation_unverified_when_probe_fails(monkeypatch):
    monkeypatch.setattr(cap, "verify_network_isolation", lambda prefix, python=None, timeout_seconds=3: {
        "verified": False, "method": None, "probe": "localhost-connect", "reason": "forced",
    })
    report = cap.executable_code_report([
        cd_record("CD-01", GOOD_CD01),
        cd_record("CD-02", GOOD_CD02),
        cd_record("CD-03", GOOD_CD03),
        cd_record("CD-04", GOOD_CD04),
        cd_record("CD-05", GOOD_CD05),
    ])
    assert report["status"] == "isolation_unverified"
    assert report["isolation_verified"] is False
    assert all(report["cases"][case_id]["passed"] for case_id in report["expected_case_ids"])


def test_execute_code_fails_sql_injection_and_wrong_page_count():
    bad_page = """
def page_count(total, size):
    return total // size + 1
"""
    report = cap.executable_code_report([
        cd_record("CD-02", bad_page),
        cd_record("CD-03", UNSAFE_CD03),
    ])
    assert report["status"] == "collected_fail"
    assert report["cases"]["CD-02"]["passed"] is False
    assert report["cases"]["CD-03"]["passed"] is False
    malicious = report["cases"]["CD-03"]["samples"][0]["vectors"][0]
    assert malicious["id"] == "literal-malicious-name"
    assert malicious["passed"] is False


def test_execute_code_not_collected_without_cd_samples():
    report = cap.executable_code_report([so_record("SO-01", "{}", [{"kind": "json_keys", "required": []}])])
    assert report["status"] == "not_collected"
    assert report["generated_code_executed"] is False


def test_synthesize_long_context_places_needles_and_records_word_count():
    begin = cap.synthesize_long_context_case(64, "begin")
    mid = cap.synthesize_long_context_case(64, "mid")
    end = cap.synthesize_long_context_case(64, "end")
    for case in (begin, mid, end):
        assert case["estimated_tokens"] >= 64
        assert case["token_estimate_method"] == "word_count"
        assert case["in_frozen_suite"] is False
        assert case["context"].split().count(case["needle"]) == 1
    assert begin["needle_word_index"] < mid["needle_word_index"] < end["needle_word_index"]
    full = cap.synthesize_long_context_case(8192, "mid")
    assert full["id"] == "LC-8k-mid"
    assert full["estimated_tokens"] >= 8192
    assert full["needle"] not in cap.FILLER


def test_long_context_report_not_collected_without_live_samples():
    report = cap.long_context_report([])
    assert report["status"] == "not_collected"
    assert report["folded_into_frozen_suite"] is False
    assert len(report["synthesized_cases"]) == 9
    assert report["expected_case_ids"] == [
        "LC-8k-begin", "LC-8k-mid", "LC-8k-end",
        "LC-16k-begin", "LC-16k-mid", "LC-16k-end",
        "LC-32k-begin", "LC-32k-mid", "LC-32k-end",
    ]


def test_long_context_report_incomplete_with_partial_live_samples():
    token = cap.long_context_needle(8192, "begin")
    record = {
        "sample_id": "LC-8k-begin.r1.t1",
        "case_id": "LC-8k-begin",
        "category": "long-context",
        "status": "response",
        "message": {"content": token},
        "automatic_checks": ev.automatic_checks({"content": token}, [{"kind": "contains", "value": token}]),
    }
    report = cap.long_context_report([record])
    assert report["status"] == "incomplete"
    assert report["cases"]["LC-8k-begin"]["passed"] is True


def test_report_run_writes_four_json_files_without_executing_code(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    ev.write_jsonl(run / "results.jsonl", [so_record("SO-01", '{"ok":true}', [{"kind": "json_equals", "value": {"ok": True}}])])
    result = cap.report_run(run)
    for name in ("schema-report.json", "native-tool-report.json", "executable-code-report.json", "long-context-report.json"):
        assert (run / name).is_file()
    executable = ev.read_json(run / "executable-code-report.json")
    assert executable["status"] == "skipped"
    assert result["schema"]["status"] == "incomplete"
    assert result["long_context"]["status"] == "not_collected"
