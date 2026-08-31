"""Scoring failures, isolation, budget gates and transcript handling without inference."""
from copy import deepcopy
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
                           temperature=0, max_seconds=10, timeout_seconds=5, runtime_record=runtime, api_key_env=None,
                           run_dir=tmp_path / "results", suite=suite_path, surface="direct", model="Veronica",
                           mode="chat", seed=1, repeats=1, max_tokens=10)
    report = ev.collect(args, data, data["cases"], ev.plan(data["cases"], 1, 10, 10, 100))
    assert requests[1]["messages"][-2] == {"role": "assistant", "content": "reply-1"}
    assert all(m["role"] != "assistant" for m in requests[2]["messages"])
    assert "rubric" not in json.dumps(requests) and "DO_NOT_COPY" not in (args.run_dir / "manifest.json").read_text()
    assert report["gate"] == "human_review_pending"


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
