import json
from pathlib import Path

import pytest

from veronica_core.context_gate import (
    CONTEXT_POSITIONS,
    CONTEXT_TARGETS,
    ContextPacketError,
    build_probe,
    read_json,
    validate_context_config,
    validate_packet,
)


ROOT = Path(__file__).resolve().parents[1]


class WordTokenizer:
    """Small deterministic tokenizer used only to test packet mechanics."""

    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))


def test_cp2_config_pins_four_models_and_keeps_synthetic_cases_outside_suite():
    config = read_json(ROOT / "config/t2-context.json")
    result = validate_context_config(config, ROOT)
    assert result["valid"] is True, result["issues"]
    assert result["tokenizer_count"] == 4
    assert config["in_frozen_suite"] is False
    assert config["frozen_suite"]["sha256"] == "ce1644f045953b66cd9b98883570d7404cac832cf06a6085453259af86aecf90"


@pytest.mark.parametrize("position", CONTEXT_POSITIONS)
def test_probe_uses_actual_token_count_and_places_one_needle(position):
    probe = build_probe(8192, position, WordTokenizer(), "fixture", 32768)
    assert probe["token_count"] == 8192
    assert probe["needle_occurrences"] == 1
    assert probe["truncated"] is False
    if position == "begin":
        assert probe["needle_start_token"] == 0
    elif position == "end":
        assert probe["needle_start_token"] + probe["needle_token_count"] == 8192
    else:
        assert abs((probe["needle_start_token"] / 8192) - 0.5) < 0.01


def test_config_rejects_word_count_or_moving_revision():
    config = read_json(ROOT / "config/t2-context.json")
    config["in_frozen_suite"] = True
    result = validate_context_config(config, ROOT)
    assert result["valid"] is False
    assert any("outside" in issue for issue in result["issues"])

    config = read_json(ROOT / "config/t2-context.json")
    config["tokenizers"][0]["revision"] = "main"
    result = validate_context_config(config, ROOT)
    assert result["valid"] is False
    assert any("immutable" in issue for issue in result["issues"])


def test_packet_validator_requires_nine_synthetic_probes(tmp_path):
    config = read_json(ROOT / "config/t2-context.json")
    rows = []
    for target in CONTEXT_TARGETS:
        for position in CONTEXT_POSITIONS:
            needle = f"CEDARTOKEN{target}{position.upper()}Q7F3"
            context = needle
            rows.append({
                "probe_id": f"LC-{target // 1024}k-{position}",
                "target_tokens": target,
                "position": position,
                "needle": needle,
                "needle_occurrences": 1,
                "in_frozen_suite": False,
                "source_kind": "synthetic",
                "context": context,
                "context_sha256": __import__("hashlib").sha256(context.encode()).hexdigest(),
                "synthetic_retrieval": {"accuracy": 1.0},
                "token_counts_by_tokenizer": {"fixture": {"token_count": target, "truncated": target > 32768}},
            })
    (tmp_path / "metadata.json").write_text(json.dumps({
        "packet_id": config["packet_id"], "model_behavior_claim": False,
        "model_retrieval_accuracy": None,
    }))
    (tmp_path / "report.json").write_text(json.dumps({
        "kind": "actual_token_context_report", "model_behavior_claim": False,
        "model_retrieval_accuracy": None,
    }))
    (tmp_path / "probes.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    result = validate_packet(tmp_path, config)
    assert result["valid"] is True, result["issues"]
