"""Independent strict schema and native-call checks for the T2 SO/TS cases.

These checks are deliberately separate from the model's automatic-check fields:
those fields are evidence to audit, never an authority that can self-certify.
"""
from __future__ import annotations

import json
import math
from typing import Any


def strict_json(text: str) -> Any:
    if not isinstance(text, str):
        raise ValueError("json_content_must_be_string")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    def reject(value):
        raise ValueError("nonfinite_json_number")

    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite_json_number")
        return parsed

    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite_float)


def equal_json(left: Any, right: Any) -> bool:
    if type(left) in (int, float) and type(right) in (int, float):
        return not isinstance(left, bool) and not isinstance(right, bool) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal_json(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equal_json(a, b) for a, b in zip(left, right))
    return left == right


def _json_check(message: dict, check: dict) -> tuple[bool, str | None]:
    content = message.get("content")
    try:
        parsed = strict_json(content)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return False, str(exc)
    if not isinstance(parsed, dict):
        return False, "json_root_must_be_object"
    kind = check.get("kind")
    if kind == "json_equals":
        expected = check.get("value")
        return (equal_json(parsed, expected), None if equal_json(parsed, expected) else "json_value_mismatch")
    if kind == "json_keys":
        required = check.get("required")
        allowed = check.get("allowed")
        if not isinstance(required, list) or len(required) != len(set(required)) or not all(isinstance(k, str) for k in required):
            return False, "invalid_required_keys"
        if not set(required) <= parsed.keys():
            return False, "missing_required_key"
        if allowed is not None and (not isinstance(allowed, list) or not set(parsed) <= set(allowed)):
            return False, "unexpected_json_key"
        return True, None
    return False, "unsupported_schema_check"


def _tool_check(message: dict, check: dict) -> tuple[bool, str | None]:
    calls = message.get("tool_calls") or []
    if check.get("kind") == "no_tool_calls":
        return (not calls and not message.get("function_call"), None if not calls else "unexpected_tool_call")
    if check.get("kind") != "tool_call":
        return False, "unsupported_tool_check"
    if len(calls) != 1 or not isinstance(calls[0], dict) or calls[0].get("type") != "function":
        return False, "exactly_one_native_function_call_required"
    function = calls[0].get("function")
    if not isinstance(function, dict) or function.get("name") != check.get("name"):
        return False, "tool_name_mismatch"
    try:
        arguments = strict_json(function.get("arguments"))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return False, str(exc)
    expected = check.get("arguments")
    return (equal_json(arguments, expected), None if equal_json(arguments, expected) else "tool_arguments_mismatch")


def validate_record(record: dict, case: dict) -> dict:
    """Validate one response against case checks without trusting auto-checks."""
    row = {"sample_id": record.get("sample_id"), "case_id": case.get("id"), "passed": False, "errors": []}
    if record.get("status") != "response":
        row["errors"].append("sample_not_response")
        return row
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        row["errors"].append("invalid_assistant_message")
        return row
    checks = [check for turn in case.get("turns", []) for check in turn.get("checks", [])
              if check.get("kind") in {"json_equals", "json_keys", "tool_call", "no_tool_calls"}]
    if not checks:
        row["errors"].append("case_has_no_schema_checks")
        return row
    for check in checks:
        passed, error = _json_check(message, check) if check["kind"].startswith("json_") else _tool_check(message, check)
        row.setdefault("checks", []).append({"kind": check["kind"], "passed": passed, "error": error})
        if not passed:
            row["errors"].append(error or "schema_check_failed")
    row["passed"] = not row["errors"]
    return row


def schema_report(records: list[dict], suite: dict) -> dict:
    cases = [case for case in suite.get("cases", []) if str(case.get("id", "")).startswith("SO-")]
    by_case = {case["id"]: [] for case in cases}
    for record in records:
        if record.get("case_id") in by_case:
            by_case[record["case_id"]].append(validate_record(record, next(case for case in cases if case["id"] == record["case_id"])))
    rows = {case["id"]: by_case[case["id"]] for case in cases}
    missing = [case_id for case_id, samples in rows.items() if not samples]
    failed = [case_id for case_id, samples in rows.items() if samples and not all(row["passed"] for row in samples)]
    if not records or all(not samples for samples in rows.values()):
        status = "not_collected"
    elif failed:
        status = "collected_fail"
    elif missing:
        status = "incomplete"
    else:
        status = "collected_pass"
    return {
        "schema_version": 1, "kind": "schema_report", "status": status,
        "expected_case_ids": list(rows), "missing_case_ids": missing,
        "failed_case_ids": failed, "cases": rows, "tools_executed": False,
        "foundation_qualified": False,
        "limits": "Independent strict schema/native-call checks; semantic human review remains required.",
    }
