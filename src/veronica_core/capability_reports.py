"""Post-hoc T2 capability reports from results.jsonl. Never executes tools or generated code in collect()."""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
from typing import Any

from .evaluation import DEFAULT_SUITE, read_json, read_jsonl, write_json


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = ROOT / "data/evals/t2-executable-fixtures.json"
LONG_CONTEXT_TARGETS = (8192, 16384, 32768)
LONG_CONTEXT_POSITIONS = ("begin", "mid", "end")
JSON_CHECK_KINDS = {"json_equals", "json_keys"}
TOOL_CHECK_KINDS = {"tool_call", "no_tool_calls"}
FENCE_RE = re.compile(r"```(?:python|py)?[ \t]*\r?\n(.*?)```", re.IGNORECASE | re.DOTALL)
KEEP_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)
FILLER = (
    "Cedar archive padding note. Juniper lantern review remains unrelated. "
    "No secret project token appears in this sentence. Room eight is fictional."
)

# Isolated child: load extracted.py by path, score only parent-supplied fixture vectors.
HARNESS_SOURCE = r'''
import copy
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

def equal(left, right):
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    return left == right

def unwrap(value):
    if hasattr(value, "fetchall") and callable(value.fetchall):
        return unwrap(list(value.fetchall()))
    return value

def as_rows(value):
    value = unwrap(value)
    if value is None:
        return None
    if not isinstance(value, list):
        return value
    rows = []
    for row in value:
        if isinstance(row, dict) and "id" in row and "display_name" in row:
            rows.append([row["id"], row["display_name"]])
        elif isinstance(row, (list, tuple)):
            rows.append(list(row))
        else:
            rows.append(row)
    return rows

def matches_raise(exc, name):
    if type(exc).__name__ == name:
        return True
    base = getattr(__builtins__, name, None)
    return isinstance(base, type) and isinstance(exc, base)

def open_conn(setup):
    if not setup or setup.get("kind") != "sqlite_users":
        return None
    conn = sqlite3.connect(":memory:")
    conn.execute(setup["schema"])
    for row in setup.get("rows") or []:
        conn.execute("INSERT INTO users (id, display_name) VALUES (?, ?)", (row["id"], row["display_name"]))
    conn.commit()
    return conn

def load_extracted(path, name):
    spec = importlib.util.spec_from_file_location("extracted", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, name, None)
    if not callable(fn):
        raise RuntimeError("missing_function")
    return fn

def main():
    job = json.loads(Path("job.json").read_text(encoding="utf-8"))
    fn = load_extracted(Path("extracted.py"), job["function"])
    results = []
    for vector in job["vectors"]:
        conn = open_conn(job.get("setup"))
        args = copy.deepcopy(vector.get("args") or [])
        if vector.get("inject_conn"):
            call_args = [conn, *args]
            original = None
        else:
            call_args = args
            original = copy.deepcopy(args)
        expect = vector.get("expect") or {}
        row = {"id": vector.get("id"), "passed": False}
        try:
            actual = fn(*call_args)
            if original is not None and vector.get("assert_input_unchanged") and call_args != original:
                row["error"] = "input_mutated"
            elif "raises" in expect:
                row["error"] = "expected_exception"
            elif "rows" in expect:
                row["passed"] = equal(as_rows(actual), expect["rows"])
                if not row["passed"]:
                    row["error"] = "rows_mismatch"
            elif "equals" in expect:
                row["passed"] = equal(unwrap(actual), expect["equals"])
                if not row["passed"]:
                    row["error"] = "value_mismatch"
            else:
                row["error"] = "invalid_expect"
        except Exception as exc:
            if "raises" in expect and matches_raise(exc, expect["raises"]):
                row["passed"] = True
            else:
                row["error"] = type(exc).__name__
        if conn is not None:
            conn.close()
        results.append(row)
    print(json.dumps({"results": results}, ensure_ascii=False))

if __name__ == "__main__":
    main()
'''


def case_ids_with_prefix(prefix: str, suite: dict | None = None) -> list[str]:
    suite = suite if suite is not None else read_json(DEFAULT_SUITE)
    return [case["id"] for case in suite["cases"] if str(case.get("id", "")).startswith(prefix)]


def load_fixtures(path: Path = DEFAULT_FIXTURES) -> dict:
    data = read_json(path)
    if data.get("schema_version") != 1 or not isinstance(data.get("cases"), list):
        raise ValueError("Invalid executable fixtures")
    ids = [case.get("id") for case in data["cases"]]
    if ids != ["CD-01", "CD-02", "CD-03", "CD-04", "CD-05"]:
        raise ValueError("Executable fixtures must define CD-01 through CD-05 in order")
    for case in data["cases"]:
        if not case.get("function") or not isinstance(case.get("vectors"), list) or not case["vectors"]:
            raise ValueError(f"{case.get('id')}: fixture requires function and vectors")
    return data


def _check_kind(item: dict) -> str | None:
    if not isinstance(item, dict):
        return None
    check = item.get("check")
    if isinstance(check, dict):
        return check.get("kind")
    return item.get("kind")


def _check_passed(item: dict) -> bool:
    return bool(item.get("passed"))


def _roll_up_checks(records: list[dict], expected_ids: list[str], kinds: set[str], *, report_kind: str, extra: dict) -> dict:
    by_case: dict[str, list[dict]] = defaultdict(list)
    expected = set(expected_ids)
    for record in records:
        case_id = record.get("case_id")
        if case_id in expected:
            by_case[case_id].append(record)
    case_rows = {}
    any_fail = False
    error_count = 0
    passed_checks = 0
    failed_checks = 0
    for case_id in expected_ids:
        samples = by_case.get(case_id, [])
        sample_rows = []
        case_fail = False
        for record in samples:
            row: dict[str, Any] = {"sample_id": record.get("sample_id"), "status": record.get("status")}
            if record.get("status") != "response":
                row["passed"] = False
                case_fail = True
                error_count += 1
                sample_rows.append(row)
                continue
            relevant = [item for item in record.get("automatic_checks") or [] if _check_kind(item) in kinds]
            kind_counts = {kind: {"passed": 0, "failed": 0} for kind in sorted(kinds)}
            for item in relevant:
                kind = _check_kind(item)
                if kind not in kind_counts:
                    continue
                if _check_passed(item):
                    kind_counts[kind]["passed"] += 1
                    passed_checks += 1
                else:
                    kind_counts[kind]["failed"] += 1
                    failed_checks += 1
                    case_fail = True
            row["checks"] = kind_counts
            row["passed"] = bool(relevant) and all(_check_passed(item) for item in relevant)
            if not row["passed"]:
                case_fail = True
            sample_rows.append(row)
        missing = not samples
        case_rows[case_id] = {
            "samples": sample_rows,
            "sample_count": len(samples),
            "passed": bool(samples) and not case_fail,
            "missing": missing,
        }
        if case_fail:
            any_fail = True
    missing_ids = [case_id for case_id in expected_ids if case_rows[case_id]["missing"]]
    if not any(case_rows[case_id]["sample_count"] for case_id in expected_ids):
        status = "not_collected"
    elif any_fail:
        status = "collected_fail"
    elif missing_ids:
        status = "incomplete"
    else:
        status = "collected_pass"
    return {
        "schema_version": 1,
        "kind": report_kind,
        "status": status,
        "expected_case_ids": expected_ids,
        "missing_case_ids": missing_ids,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "errors": error_count,
        "cases": case_rows,
        "foundation_qualified": False,
        **extra,
    }


def schema_report(records: list[dict], suite: dict | None = None) -> dict:
    return _roll_up_checks(
        records,
        case_ids_with_prefix("SO-", suite),
        JSON_CHECK_KINDS,
        report_kind="schema_report",
        extra={
            "tools_executed": False,
            "check_kinds": sorted(JSON_CHECK_KINDS),
            "limits": "Roll-up of existing automatic JSON checks only. Semantic review still required.",
        },
    )


def native_tool_report(records: list[dict], suite: dict | None = None) -> dict:
    return _roll_up_checks(
        records,
        case_ids_with_prefix("TS-", suite),
        TOOL_CHECK_KINDS,
        report_kind="native_tool_report",
        extra={
            "tools_executed": False,
            "check_kinds": sorted(TOOL_CHECK_KINDS),
            "limits": "Native call selection and arguments only. Tools are never executed.",
        },
    )


def skipped_executable_report(records: list[dict] | None = None, fixtures: dict | None = None) -> dict:
    fixtures = fixtures if fixtures is not None else {"cases": [{"id": f"CD-0{n}"} for n in range(1, 6)]}
    expected = [case["id"] for case in fixtures["cases"]]
    observed = sorted({row.get("case_id") for row in records or [] if row.get("case_id") in expected})
    return {
        "schema_version": 1,
        "kind": "executable_code_report",
        "status": "skipped",
        "execute_code": False,
        "tools_executed": False,
        "generated_code_executed": False,
        "isolation_verified": False,
        "expected_case_ids": expected,
        "observed_case_ids": observed,
        "foundation_qualified": False,
        "limits": "Generated code is not executed unless --execute-code is set. Score only independent fixtures, never model-written tests.",
    }


def long_context_needle(target_tokens: int, position: str) -> str:
    if position not in LONG_CONTEXT_POSITIONS:
        raise ValueError(f"Unsupported needle position: {position}")
    if type(target_tokens) is not int or target_tokens < 16:
        raise ValueError("target_tokens must be an integer of at least 16")
    return f"CEDARTOKEN{target_tokens}{position.upper()}Q7F3"


def long_context_case_id(target_tokens: int, position: str) -> str:
    needle = long_context_needle(target_tokens, position)
    return f"LC-{target_tokens // 1024}k-{position}" if target_tokens in LONG_CONTEXT_TARGETS else f"LC-{target_tokens}-{position}-{needle[-4:]}"


def _padding_words(count: int) -> list[str]:
    unit = FILLER.split()
    words: list[str] = []
    while len(words) < count:
        words.extend(unit)
    return words[:count]


def synthesize_long_context_case(target_tokens: int, position: str) -> dict:
    token = long_context_needle(target_tokens, position)
    sentence = f"The secret project token is {token}"
    sentence_words = sentence.split()
    pad_needed = max(0, target_tokens - len(sentence_words))
    padding = _padding_words(pad_needed)
    if token in padding:
        raise ValueError("Padding must not contain the needle token")
    if position == "begin":
        words = sentence_words + padding
    elif position == "end":
        words = padding + sentence_words
    else:
        split_at = len(padding) // 2
        words = padding[:split_at] + sentence_words + padding[split_at:]
    context = " ".join(words)
    estimated = len(context.split())
    return {
        "id": long_context_case_id(target_tokens, position),
        "category": "long-context",
        "family": f"needle-{position}",
        "tier": "extended",
        "release_blocker": False,
        "context": context,
        "turns": [{
            "user": "What is the secret project token? Reply with only the token.",
            "checks": [{"kind": "contains", "value": token}, {"kind": "no_tool_calls"}],
            "rubric": [
                "4: Returns the supplied secret token and does not invent a different value; 0: misses the token or fabricates one."
            ],
        }],
        "notes": "Synthetic long-context stress case. Not part of the frozen 60-case suite.",
        "in_frozen_suite": False,
        "needle": token,
        "needle_position": position,
        "needle_word_index": words.index(token),
        "target_tokens": target_tokens,
        "estimated_tokens": estimated,
        "token_estimate_method": "word_count",
        "context_sha256": hashlib.sha256(context.encode("utf-8")).hexdigest(),
    }


def long_context_catalog() -> list[dict]:
    catalog = []
    for target in LONG_CONTEXT_TARGETS:
        for position in LONG_CONTEXT_POSITIONS:
            case = synthesize_long_context_case(target, position)
            catalog.append({key: case[key] for key in (
                "id", "needle", "needle_position", "needle_word_index", "target_tokens",
                "estimated_tokens", "token_estimate_method", "context_sha256", "in_frozen_suite",
            )})
    return catalog


def long_context_report(records: list[dict], suite: dict | None = None) -> dict:
    expected = [long_context_case_id(target, position) for target in LONG_CONTEXT_TARGETS for position in LONG_CONTEXT_POSITIONS]
    frozen_ids = set(case_ids_with_prefix("LC-", suite)) if suite is not None else set(case_ids_with_prefix("LC-"))
    report = _roll_up_checks(
        records,
        expected,
        {"contains", "no_tool_calls"},
        report_kind="long_context_report",
        extra={
            "tools_executed": False,
            "token_estimate_method": "word_count",
            "synthesized_cases": long_context_catalog(),
            "folded_into_frozen_suite": False,
            "frozen_suite_lc_ids": sorted(frozen_ids),
            "limits": "Short CR-* probes are not a context-window result. These cases stay outside the frozen 60-case suite.",
        },
    )
    return report


def collect(records: list[dict], suite: dict | None = None) -> dict:
    """Post-hoc reports from results.jsonl. Never executes tools or generated code."""
    return {
        "schema": schema_report(records, suite),
        "native_tools": native_tool_report(records, suite),
        "executable_code": skipped_executable_report(records),
        "long_context": long_context_report(records, suite),
    }


def _definitions_only(source: str) -> str:
    tree = ast.parse(textwrap.dedent(source))
    tree.body = [node for node in tree.body if isinstance(node, KEEP_NODES)]
    return ast.unparse(tree)


def extract_python(message: dict | None, function_name: str) -> str | None:
    content = (message or {}).get("content") or ""
    chunks = [textwrap.dedent(chunk).strip() for chunk in FENCE_RE.findall(content) if chunk.strip()]
    merged = "\n\n".join(chunks) if chunks else textwrap.dedent(content).strip()
    if f"def {function_name}" not in merged:
        return None
    try:
        isolated = _definitions_only(merged)
        tree = ast.parse(isolated)
    except (SyntaxError, ValueError):
        return None
    names = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if function_name not in names or not isolated.strip():
        return None
    return isolated


def _minimal_env(workdir: Path) -> dict[str, str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(workdir),
        "TMPDIR": str(workdir),
        "TMP": str(workdir),
        "TEMP": str(workdir),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if os.name == "nt":
        for key in ("SYSTEMROOT", "WINDIR"):
            if os.environ.get(key):
                env[key] = os.environ[key]
        env["PATH"] = os.environ.get("PATH", env["PATH"])
    return env


def isolation_prefix(python: str | None = None) -> tuple[list[str], str]:
    python = python or sys.executable
    unshare = shutil.which("unshare")
    if not unshare:
        return [], "unshare_unavailable"
    candidates = [
        [unshare, "--user", "--map-root-user", "--net"],
        [unshare, "--net"],
    ]
    for prefix in candidates:
        try:
            with tempfile.TemporaryDirectory(prefix="veronica-unshare-") as work:
                workdir = Path(work)
                result = subprocess.run(
                    [*prefix, python, "-c", "pass"],
                    cwd=workdir,
                    env=_minimal_env(workdir),
                    capture_output=True,
                    timeout=3,
                )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return prefix, " ".join(prefix)
    return [], "unshare_failed"


def verify_network_isolation(prefix: list[str], python: str | None = None, timeout_seconds: float = 3) -> dict:
    python = python or sys.executable
    if not prefix:
        return {"verified": False, "method": None, "probe": "localhost-connect", "reason": "no_isolation_prefix"}
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        probe = (
            "import socket\n"
            "s=socket.socket(); s.settimeout(0.5)\n"
            "try:\n"
            f"    s.connect(('127.0.0.1', {port}))\n"
            "    print('CONNECTED')\n"
            "except OSError:\n"
            "    print('BLOCKED')\n"
        )
        with tempfile.TemporaryDirectory(prefix="veronica-iso-") as work:
            workdir = Path(work)
            result = subprocess.run(
                [*prefix, python, "-c", probe],
                cwd=workdir,
                env=_minimal_env(workdir),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        blocked = "BLOCKED" in result.stdout and "CONNECTED" not in result.stdout
        return {
            "verified": bool(blocked and result.returncode == 0),
            "method": " ".join(prefix),
            "probe": "localhost-connect",
            "reason": None if blocked else "child_reached_parent_listener",
        }
    except (OSError, subprocess.TimeoutExpired):
        return {"verified": False, "method": " ".join(prefix), "probe": "localhost-connect", "reason": "probe_failed"}
    finally:
        server.close()


def _run_isolated_sample(source: str, fixture: dict, prefix: list[str], timeout_seconds: float) -> dict:
    python = sys.executable
    with tempfile.TemporaryDirectory(prefix="veronica-cd-") as work:
        workdir = Path(work)
        (workdir / "extracted.py").write_text(source + "\n", encoding="utf-8")
        (workdir / "harness.py").write_text(textwrap.dedent(HARNESS_SOURCE).lstrip() + "\n", encoding="utf-8")
        write_json(workdir / "job.json", {
            "function": fixture["function"],
            "setup": fixture.get("setup"),
            "vectors": fixture["vectors"],
        })
        command = [*prefix, python, str(workdir / "harness.py")] if prefix else [python, str(workdir / "harness.py")]
        try:
            result = subprocess.run(
                command,
                cwd=workdir,
                env=_minimal_env(workdir),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "vectors": []}
        if result.returncode != 0:
            return {"ok": False, "error": "subprocess_error", "detail": (result.stderr or result.stdout)[-500:], "vectors": []}
        try:
            payload = json.loads(result.stdout.splitlines()[-1])
            vectors = payload["results"]
        except (json.JSONDecodeError, KeyError, IndexError):
            return {"ok": False, "error": "invalid_harness_output", "vectors": []}
        return {"ok": True, "error": None, "vectors": vectors}


def executable_code_report(
    records: list[dict],
    fixtures_path: Path = DEFAULT_FIXTURES,
    timeout_seconds: float = 8,
    isolation: dict | None = None,
    prefix: list[str] | None = None,
) -> dict:
    fixtures = load_fixtures(fixtures_path)
    expected = [case["id"] for case in fixtures["cases"]]
    by_id = {case["id"]: case for case in fixtures["cases"]}
    observed = [record for record in records if record.get("case_id") in by_id]
    if not observed:
        report = skipped_executable_report(records, fixtures)
        report["status"] = "not_collected"
        report["execute_code"] = True
        report["limits"] = "No CD-* samples were present. Generated code was not executed."
        return report
    if prefix is None:
        prefix, _method = isolation_prefix()
    if isolation is None:
        isolation = verify_network_isolation(prefix)
    cases: dict[str, Any] = {}
    any_fail = False
    executed = False
    for case_id in expected:
        fixture = by_id[case_id]
        samples = [record for record in observed if record.get("case_id") == case_id]
        sample_rows = []
        case_fail = False
        for record in samples:
            row: dict[str, Any] = {"sample_id": record.get("sample_id"), "status": record.get("status")}
            if record.get("status") != "response":
                row.update(passed=False, error="sample_error")
                case_fail = True
                sample_rows.append(row)
                continue
            source = extract_python(record.get("message"), fixture["function"])
            if not source:
                row.update(passed=False, error="extraction_failed", vectors_passed=0, vectors_failed=len(fixture["vectors"]))
                case_fail = True
                sample_rows.append(row)
                continue
            executed = True
            outcome = _run_isolated_sample(source, fixture, prefix, timeout_seconds)
            vectors = outcome.get("vectors") or []
            passed_n = sum(bool(item.get("passed")) for item in vectors)
            failed_n = len(fixture["vectors"]) - passed_n
            ok = bool(outcome.get("ok")) and failed_n == 0 and passed_n == len(fixture["vectors"])
            row.update(
                passed=ok,
                error=None if ok else outcome.get("error") or "vector_failure",
                vectors_passed=passed_n,
                vectors_failed=failed_n,
                vectors=vectors,
            )
            if not ok:
                case_fail = True
            sample_rows.append(row)
        missing = not samples
        cases[case_id] = {
            "function": fixture["function"],
            "samples": sample_rows,
            "sample_count": len(samples),
            "vector_count": len(fixture["vectors"]),
            "passed": bool(samples) and not case_fail,
            "missing": missing,
        }
        if case_fail:
            any_fail = True
    missing_ids = [case_id for case_id in expected if cases[case_id]["missing"]]
    if any_fail:
        status = "collected_fail"
    elif missing_ids:
        status = "incomplete"
    elif isolation.get("verified"):
        status = "collected_pass"
    else:
        status = "isolation_unverified"
    return {
        "schema_version": 1,
        "kind": "executable_code_report",
        "status": status,
        "execute_code": True,
        "tools_executed": False,
        "generated_code_executed": executed,
        "isolation_verified": bool(isolation.get("verified")),
        "isolation": isolation,
        "expected_case_ids": expected,
        "missing_case_ids": missing_ids,
        "cases": cases,
        "foundation_qualified": False,
        "limits": "Independent fixture vectors only. Model-written tests are stripped and never scored. collected_pass requires verified network isolation.",
    }


def report_run(
    run_dir: Path,
    output_dir: Path | None = None,
    *,
    execute_code: bool = False,
    fixtures_path: Path | None = None,
    timeout_seconds: float = 8,
) -> dict:
    run_dir = Path(run_dir)
    if not (run_dir / "results.jsonl").is_file():
        raise ValueError("results.jsonl is required")
    output_dir = Path(output_dir) if output_dir else run_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    records = read_jsonl(run_dir / "results.jsonl")
    reports = collect(records)
    if execute_code:
        reports["executable_code"] = executable_code_report(
            records,
            fixtures_path=fixtures_path or DEFAULT_FIXTURES,
            timeout_seconds=timeout_seconds,
        )
    names = {
        "schema": "schema-report.json",
        "native_tools": "native-tool-report.json",
        "executable_code": "executable-code-report.json",
        "long_context": "long-context-report.json",
    }
    written = {}
    for key, filename in names.items():
        path = output_dir / filename
        write_json(path, reports[key])
        written[key] = str(path)
    reports["written"] = written
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--execute-code", action="store_true")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--timeout-seconds", type=float, default=8)
    args = parser.parse_args()
    try:
        result = report_run(
            args.run_dir,
            args.output_dir,
            execute_code=args.execute_code,
            fixtures_path=args.fixtures,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Capability report stopped: {exc}\n")


if __name__ == "__main__":
    main()
