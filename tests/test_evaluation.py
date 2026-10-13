"""Scoring failures, isolation, budget gates and transcript handling without inference."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from veronica_core import evaluation as ev
from veronica_core.dataset_checks import lint


def case(case_id="sample", turns=1):
    return {"id": case_id, "family": case_id, "category": "grounding", "tier": "smoke", "release_blocker": True,
            "context": "Text-only test fixture. No tools or persistent memory.",
            "turns": [{"user": f"Question {n}", "checks": [], "rubric": ["Answer using only supplied facts."]} for n in range(turns)]}


def suite(*cases):
    return {"schema_version": 1, "suite_id": "test", "cases": list(cases or [case()])}


def test_duplicate_case_and_unknown_checker_refused():
    with pytest.raises(ValueError, match="duplicate"):
        ev.validate_suite(suite(case(), case()))
    data = suite()
    data["cases"][0]["turns"][0]["checks"] = [{"kind": "pretend_semantic_pass"}]
    with pytest.raises(ValueError, match="unsupported"):
        ev.validate_suite(data)


def test_correct_substring_does_not_pass_exact_or_remove_semantic_review():
    answer = {"content": "The answer is 3/5. Final answer: 3/10."}
    checks = ev.automatic_checks(answer, [{"kind": "contains", "value": "3/10"}, {"kind": "exact", "value": "3/10"}])
    assert checks[0]["passed"] is True
    assert checks[1]["passed"] is False
    record = result_record(checks[:1])
    assert ev.build_report(manifest(), [record], [])["gate"] == "human_review_pending"


@pytest.mark.parametrize("answer", ['{"ok":true,"ok":false}', '{"ok":NaN}', '```json\n{"ok":true}\n```', '{"ok":1}'])
def test_json_grade_rejects_duplicate_keys_nonfinite_fences_and_bool_number_confusion(answer):
    assert not ev.automatic_checks({"content": answer}, [{"kind": "json_equals", "value": {"ok": True}}])[0]["passed"]


def test_evidence_redaction_preserves_only_known_numeric_usage_counters():
    evidence = {
        "usage": {
            "prompt_tokens": 387,
            "completion_tokens": 18,
            "total_tokens": 405,
            "prompt_tokens_details": {"cached_tokens": 7, "audio_tokens": 2},
            "completion_tokens_details": {
                "reasoning_tokens": 11, "audio_tokens": 3,
                "accepted_prediction_tokens": 1, "rejected_prediction_tokens": 0,
            },
            "other_tokens": 9,
        },
        "prompt_tokens": 999,
        "request": {"max_tokens": 384},
        "invalid_usage": {"prompt_tokens": True, "total_tokens": -1, "completion_tokens": "18"},
    }

    cleaned = ev._redact_evidence(evidence)

    assert cleaned["usage"]["prompt_tokens"] == 387
    assert type(cleaned["usage"]["prompt_tokens"]) is int
    assert cleaned["usage"]["completion_tokens"] == 18
    assert cleaned["usage"]["total_tokens"] == 405
    assert cleaned["usage"]["prompt_tokens_details"] == {"cached_tokens": 7, "audio_tokens": 2}
    assert cleaned["usage"]["completion_tokens_details"]["reasoning_tokens"] == 11
    assert cleaned["usage"]["completion_tokens_details"]["accepted_prediction_tokens"] == 1
    assert cleaned["usage"]["other_tokens"] == ev.REDACTED
    assert cleaned["prompt_tokens"] == ev.REDACTED
    assert cleaned["request"]["max_tokens"] == 384
    assert cleaned["invalid_usage"] == {
        "prompt_tokens": ev.REDACTED, "total_tokens": ev.REDACTED, "completion_tokens": ev.REDACTED,
    }


def test_evidence_redaction_scrubs_nested_credentials_strings_and_raw_json():
    explicit_secret = "synthetic-explicit-value"
    known_format_key = "sk-" + "synthetic-api-key-value"
    evidence = {
        "usage": {"prompt_tokens": 387, "completion_tokens": 18, "total_tokens": 405},
        "properties": {
            "api_key": "synthetic-api-key-value",
            "access_token": "synthetic-access-token-value",
            "refresh_token": "synthetic-refresh-token-value",
            "token": "synthetic-bare-token-value",
        },
        "nested": {"authorization": "Bearer " + "synthetic-bearer-value"},
        "message": (
            "Bearer " + "synthetic-inline-bearer-value; "
            "api_key=synthetic-inline-api-key; API key is " + known_format_key + "; synthetic-explicit-value"
        ),
    }

    cleaned = ev._redact_evidence(
        {"parsed": evidence, "raw_json": json.dumps(evidence)},
        [explicit_secret],
    )
    parsed_raw = json.loads(cleaned["raw_json"])
    saved = json.dumps(cleaned, ensure_ascii=False)

    assert cleaned["parsed"]["usage"] == parsed_raw["usage"]
    assert type(parsed_raw["usage"]["prompt_tokens"]) is int
    assert cleaned["parsed"]["properties"] == {
        "api_key": ev.REDACTED,
        "access_token": ev.REDACTED,
        "refresh_token": ev.REDACTED,
        "token": ev.REDACTED,
    }
    assert parsed_raw["properties"] == cleaned["parsed"]["properties"]
    for secret in (
        explicit_secret, "synthetic-api-key-value", "synthetic-access-token-value",
        "synthetic-refresh-token-value", "synthetic-bare-token-value",
        "synthetic-bearer-value", "synthetic-inline-bearer-value", "synthetic-inline-api-key",
        known_format_key,
    ):
        assert secret not in saved


def test_prose_does_not_count_as_native_tool_call_and_multiple_calls_fail():
    check = [{"kind": "tool_call", "name": "weather", "arguments": {"city": "Oslo"}}]
    assert not ev.automatic_checks({"content": 'I called weather(city="Oslo")'}, check)[0]["passed"]
    call = {"type": "function", "function": {"name": "weather", "arguments": '{"city":"Oslo"}'}}
    assert ev.automatic_checks({"content": None, "tool_calls": [call]}, check)[0]["passed"]
    assert not ev.automatic_checks({"content": None, "tool_calls": [call, call]}, check)[0]["passed"]


def test_numeric_tool_arguments_accept_equivalent_json_numbers_but_not_booleans():
    check = [{"kind": "tool_call", "name": "add", "arguments": {"a": 17, "b": 23}}]
    call = {"type": "function", "function": {"name": "add", "arguments": '{"a":17.0,"b":23.0}'}}
    assert ev.automatic_checks({"content": None, "tool_calls": [call]}, check)[0]["passed"]
    assert not ev.equal_json({"a": True}, {"a": 1.0})
    assert not ev.equal_json({"a": 17.1}, {"a": 17})


def result_record(checks=None):
    return {"sample_id": "sample.r1.t1", "status": "response", "category": "grounding", "release_blocker": True,
            "automatic_checks": checks or [], "rubric": ["Ground every claim."]}


def manifest():
    return {"suite_id": "test", "source_kind": "test_only", "plan": {"completion_calls": 1}, "collection_status": "complete"}


def test_ai_review_cannot_qualify_model_or_stand_in_for_human():
    review = {"sample_id": "sample.r1.t1", "score": 4, "critical_failure": False, "reviewer_type": "assistant", "reviewer": "test judge", "rationale": "Advisory only."}
    report = ev.build_report(manifest(), [result_record()], [review])
    assert report["gate"] == "human_review_pending"
    assert report["human_reviewed"] == 0 and not report["foundation_qualified"]
    review.update(reviewer_type="human", score=4, critical_failure=True)
    assert ev.build_report(manifest(), [result_record()], [review])["gate"] == "blocked_on_observed_failures"


def test_incomplete_run_never_passes_and_duplicate_reviews_rejected():
    metadata = manifest()
    metadata["plan"]["completion_calls"] = 2
    assert ev.build_report(metadata, [result_record()], [])["gate"] == "incomplete"
    review = {"sample_id": "sample.r1.t1", "score": 3, "critical_failure": False, "reviewer_type": "human", "reviewer": "reviewer", "rationale": "Reviewed."}
    with pytest.raises(ValueError, match="duplicate"):
        ev.build_report(manifest(), [result_record()], [review, review])


def test_budgets_and_remote_transmission_fail_before_any_network():
    with pytest.raises(ValueError, match="exceeds"):
        ev.plan([case(turns=2)], 3, 384, 5, 50000)
    with pytest.raises(ValueError, match="exceeds"):
        ev.plan([case()], 1, 384, 5, 100)
    for url in ("https://other.example/v1", "http://user:secret@localhost/v1", "http://localhost/v1?key=secret"):
        with pytest.raises(ValueError):
            ev.check_endpoint(url, False)


def test_run_directory_never_overwrites_evidence(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    ev.new_run(root / "one", root)
    with pytest.raises(FileExistsError):
        ev.new_run(root / "one", root)
    with pytest.raises(ValueError):
        ev.new_run(tmp_path / "outside", root)


def test_transcript_import_preserves_failures_and_omits_ui_welcome(tmp_path, monkeypatch):
    source = tmp_path / "chat.txt"
    source.write_text("Header\nMessage 1\nSYSTEMWelcome\n\n---\n\nMessage 2\nYOUHello\n\n---\n\nMessage 3\nVERONICAI read your emails.\n", encoding="utf-8")
    destination = tmp_path / "output"
    monkeypatch.setattr(ev, "new_run", lambda path: (path.mkdir(), path)[1])
    result = ev.import_transcript(source, destination)
    records = ev.read_jsonl(destination / "results.jsonl")
    assert records[0]["message"]["content"] == "I read your emails."
    assert records[0]["request"]["messages"] == [{"role": "user", "content": "Hello"}]
    assert result["source_kind"] == "recorded_conversation"
    assert ev.read_json(destination / "manifest.json")["new_model_calls"] == 0
    assert not ev.read_json(destination / "manifest.json")["training_authorized"]


def test_live_runner_isolates_cases_but_keeps_generated_history_within_case(tmp_path, monkeypatch):
    # HTTP mock transport, not real model inference. It also proves targets never enter prompts.
    data = suite(case("first", 2), case("second"))
    suite_path = tmp_path / "suite.json"
    ev.write_json(suite_path, data)
    runtime = tmp_path / "runtime.json"
    ev.write_json(runtime, {"model": {"repository": "fixture", "revision": "fixture"}, "secret": "DO_NOT_COPY"})
    requests = []
    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "Veronica"}]})
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": f"reply-{len(requests)}"}}]})
    actual_client = httpx.Client
    monkeypatch.setattr(ev.httpx, "Client", lambda **kwargs: actual_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(ev, "new_run", lambda path: (path.mkdir(), path)[1])
    args = SimpleNamespace(execute=True, base_url="http://127.0.0.1:9999/v1", allow_remote=False,
                           temperature=0, top_p=1, thinking="disabled", max_seconds=10, timeout_seconds=5,
                           runtime_record=runtime, api_key_env=None,
                           run_dir=tmp_path / "results", suite=suite_path, surface="direct", model="Veronica",
                           mode="chat", seed=1, repeats=1, max_tokens=10)
    report = ev.collect(args, data, data["cases"], ev.plan(data["cases"], 1, 10, 10, 100))
    assert requests[1]["messages"][-2] == {"role": "assistant", "content": "reply-1"}
    assert requests[0]["top_p"] == 1
    assert requests[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert all(m["role"] != "assistant" for m in requests[2]["messages"])
    assert "rubric" not in json.dumps(requests) and "DO_NOT_COPY" not in (args.run_dir / "manifest.json").read_text()
    assert report["gate"] == "human_review_pending"


def test_live_collection_redacts_saved_response_and_hashes_original_body(tmp_path, monkeypatch):
    data = suite()
    suite_path = tmp_path / "suite.json"
    ev.write_json(suite_path, data)
    runtime = tmp_path / "runtime.json"
    ev.write_json(runtime, {"model": {"repository": "fixture", "revision": "fixture"}})
    api_key = "synthetic-explicit-api-key"
    monkeypatch.setenv("VERONICA_TEST_API_KEY", api_key)
    response_data = {
        "choices": [{"message": {"role": "assistant", "content": "Bearer " + "synthetic-bearer-value"}}],
        "usage": {
            "prompt_tokens": 387,
            "completion_tokens": 18,
            "total_tokens": 405,
            "prompt_tokens_details": {"cached_tokens": 7},
            "completion_tokens_details": {"reasoning_tokens": 11},
        },
        "properties": {"api_key": api_key, "access_token": "synthetic-access-token"},
    }
    response_body = json.dumps(response_data, separators=(",", ":")).encode("utf-8")

    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "Veronica"}]})
        return httpx.Response(200, content=response_body, headers={"content-type": "application/json"})

    actual_client = httpx.Client
    monkeypatch.setattr(ev.httpx, "Client", lambda **kwargs: actual_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(ev, "new_run", lambda path: (path.mkdir(), path)[1])
    args = SimpleNamespace(
        execute=True, base_url="http://127.0.0.1:9999/v1", allow_remote=False,
        temperature=0, top_p=1, thinking="disabled", max_seconds=10, timeout_seconds=5,
        runtime_record=runtime, api_key_env="VERONICA_TEST_API_KEY",
        run_dir=tmp_path / "results", suite=suite_path, surface="direct", model="Veronica",
        mode="chat", seed=1, repeats=1, max_tokens=10,
    )

    ev.collect(args, data, data["cases"], ev.plan(data["cases"], 1, 10, 10, 100))

    record = ev.read_jsonl(args.run_dir / "results.jsonl")[0]
    raw_response = json.loads(record["raw_response"])
    saved = json.dumps(record, ensure_ascii=False)
    assert record["response"]["usage"] == raw_response["usage"]
    assert record["response"]["usage"]["prompt_tokens"] == 387
    assert type(record["response"]["usage"]["prompt_tokens"]) is int
    assert record["response"]["properties"] == {
        "api_key": ev.REDACTED, "access_token": ev.REDACTED,
    }
    assert record["message"]["content"] == ev.REDACTED
    assert record["response_body_sha256"] == hashlib.sha256(response_body).hexdigest()
    assert record["response_body_bytes"] == len(response_body)
    assert record["response_body_truncated"] is False
    assert api_key not in saved and "synthetic-access-token" not in saved
    assert "synthetic-bearer-value" not in saved


@pytest.mark.parametrize(("top_p", "thinking"), [(0, "default"), (1.1, "default"), (1, "invalid")])
def test_live_runner_rejects_invalid_sampling_or_thinking_before_network(tmp_path, monkeypatch, top_p, thinking):
    data = suite()
    suite_path = tmp_path / "suite.json"
    ev.write_json(suite_path, data)
    runtime = tmp_path / "runtime.json"
    ev.write_json(runtime, {"model": {"repository": "fixture", "revision": "fixture"}})
    args = SimpleNamespace(execute=True, base_url="http://127.0.0.1:9999/v1", allow_remote=False,
                           temperature=0, top_p=top_p, thinking=thinking, max_seconds=10, timeout_seconds=5,
                           runtime_record=runtime, api_key_env=None, run_dir=tmp_path / "results", suite=suite_path,
                           surface="direct", model="Veronica", mode="chat", seed=1, repeats=1, max_tokens=10)
    if thinking == "invalid":
        # argparse enforces this in normal CLI use; collect defensively rejects it too.
        with pytest.raises(ValueError, match="Thinking"):
            ev.collect(args, data, data["cases"], ev.plan(data["cases"], 1, 10, 10, 100))
    else:
        with pytest.raises(ValueError, match="Top-p"):
            ev.collect(args, data, data["cases"], ev.plan(data["cases"], 1, 10, 10, 100))


def training_record(record_id="example", family="new-family", split="train"):
    return {"id": record_id, "type": "sft", "family": family, "split": split, "status": "draft",
            "source": {"kind": "synthetic", "reference": "original", "license": "pending", "training_consent": False, "evaluation_only": True},
            "messages": [{"role": "user", "content": "An independent training question."}, {"role": "assistant", "content": "A reviewed answer would go here."}], "reviewer": None}


def test_dataset_drafts_are_valid_examples_but_not_ready_for_training():
    row = training_record()
    assert lint([row], suite())["structurally_valid"]
    result = lint([row], suite(), training_ready=True)
    assert not result["structurally_valid"] and not result["training_authorized_by_tool"]


def test_dataset_family_and_exact_prompt_leakage_are_blocked():
    first = training_record()
    second = training_record("other", "new-family", "test")
    assert any("across splits" in e for e in lint([first, second], suite())["errors"])
    first["messages"][0]["content"] = "Question 0"
    assert any("overlaps" in e for e in lint([first], suite())["errors"])
    first["family"] = "sample"
    assert any("reserved" in e for e in lint([first], suite())["errors"])
