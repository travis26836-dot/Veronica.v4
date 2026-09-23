import json
from pathlib import Path

from veronica_core import evaluation as ev
from veronica_core import schema_gate as gate


ROOT = Path(__file__).parents[1]


def suite():
    return ev.read_json(ev.DEFAULT_SUITE)


def response(case, content, **extra):
    return {"sample_id": case["id"] + ".r1.t1", "case_id": case["id"], "status": "response",
            "message": {"role": "assistant", "content": content, **extra}}


def expected_json(case):
    check = next(check for turn in case["turns"] for check in turn["checks"] if check["kind"] == "json_equals")
    return json.dumps(check["value"], ensure_ascii=False, separators=(",", ":"))


def test_complete_public_schema_cases_pass_independent_gate():
    cases = [case for case in suite()["cases"] if case["id"].startswith("SO-")]
    report = gate.schema_report([response(case, expected_json(case)) for case in cases], suite())
    assert report["status"] == "collected_pass"
    assert report["missing_case_ids"] == []
    assert report["failed_case_ids"] == []


def test_schema_gate_has_distinct_collection_states():
    cases = [case for case in suite()["cases"] if case["id"].startswith("SO-")]
    assert gate.schema_report([], suite())["status"] == "not_collected"
    partial = [response(cases[0], expected_json(cases[0]))]
    assert gate.schema_report(partial, suite())["status"] == "incomplete"
    bad = [response(cases[0], "{\"wrong\":true}")]
    assert gate.schema_report(bad, suite())["status"] == "collected_fail"


def test_negative_fixtures_fail_with_expected_errors():
    data = ev.read_json(ROOT / "data/evals/schema-gate-negative.json")
    multiply = next(case for case in suite()["cases"] if case["id"] == "TS-01")
    for fixture in data["cases"]:
        if "content" in fixture:
            check_case = next(case for case in suite()["cases"] if case["id"] == "SO-01")
            row = gate.validate_record(response(check_case, fixture["content"]), check_case)
        else:
            row = gate.validate_record({"sample_id": fixture["id"], "case_id": multiply["id"], "status": "response", "message": fixture["message"]}, multiply)
        assert row["passed"] is False, fixture["id"]
        assert any(fixture["expected_error"] in error for error in row["errors"]), (fixture["id"], row)


def test_strict_json_rejects_duplicate_nonfinite_and_wrong_root():
    for content in ('{"x":1,"x":2}', '{"x":1e999}'):
        try:
            gate.strict_json(content)
        except ValueError:
            pass
        else:
            raise AssertionError(content)
    assert gate._json_check({"content": "[1]"}, {"kind": "json_equals", "value": {}})[1] == "json_root_must_be_object"


def test_tool_gate_never_treats_prose_as_native_call():
    case = next(case for case in suite()["cases"] if case["id"] == "TS-01")
    check = next(check for turn in case["turns"] for check in turn["checks"] if check["kind"] == "tool_call")
    row = gate._tool_check({"role": "assistant", "content": "I called multiply."}, check)
    assert row == (False, "exactly_one_native_function_call_required")
