"""Actual-token context packet generation and validation.

This module prepares the synthetic context probes used by T2.  It deliberately
does not call a model server: tokenization is the only runtime operation here,
and model retrieval remains uncollected until a live qualification run.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
from typing import Any, Callable, Iterable
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
CONTEXT_TARGETS = (8192, 16384, 32768)
CONTEXT_POSITIONS = ("begin", "mid", "end")
PACKET_SCHEMA_VERSION = 1
TOKENIZER_BACKEND = "huggingface-tokenizers"


class ContextPacketError(ValueError):
    """Raised when the CP2 packet is missing a reproducibility input."""


@dataclass(frozen=True)
class TokenizerInfo:
    model_id: str
    repository: str
    revision: str
    tokenizer_sha256: str
    tokenizer_config_sha256: str
    chat_template_sha256: str | None
    source_url: str


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def _is_revision(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdefABCDEF" for c in value)


def validate_context_config(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """Validate the immutable CP2 inputs without loading a tokenizer."""
    issues: list[str] = []
    if config.get("schema_version") != PACKET_SCHEMA_VERSION:
        issues.append("schema_version must be 1")
    if config.get("packet_id") != "t2-actual-token-context-v1":
        issues.append("packet_id must be t2-actual-token-context-v1")
    if tuple(config.get("targets", [])) != CONTEXT_TARGETS:
        issues.append("targets must be exactly 8192, 16384, 32768")
    if tuple(config.get("positions", [])) != CONTEXT_POSITIONS:
        issues.append("positions must be exactly begin, mid, end")
    if config.get("in_frozen_suite") is not False:
        issues.append("synthetic probes must remain outside the frozen suite")

    suite = config.get("frozen_suite", {})
    suite_path_value = suite.get("path")
    if not isinstance(suite_path_value, str) or not suite_path_value:
        issues.append("frozen_suite.path is required")
    else:
        suite_path = (root / suite_path_value).resolve()
        if not suite_path.is_relative_to(root.resolve()) or not suite_path.is_file():
            issues.append("frozen_suite.path must point to a file inside the repository")
        elif suite.get("sha256") != sha256_file(suite_path):
            issues.append("frozen_suite.sha256 does not match the current suite")
    if not _is_sha256(suite.get("sha256")):
        issues.append("frozen_suite.sha256 must be a SHA-256 hash")

    runtime = config.get("runtime", {})
    for key in ("image_digest", "vllm_version", "transformers_version", "tokenizers_version", "dtype", "max_model_len"):
        if runtime.get(key) in (None, ""):
            issues.append(f"runtime.{key} is required")
    if not isinstance(runtime.get("max_model_len"), int) or runtime.get("max_model_len", 0) < max(CONTEXT_TARGETS):
        issues.append("runtime.max_model_len must cover the 32K probe")
    if runtime.get("model_behavior_claim") is not False:
        issues.append("runtime.model_behavior_claim must be false")

    tokenizers = config.get("tokenizers")
    if not isinstance(tokenizers, list) or len(tokenizers) != 4:
        issues.append("exactly four candidate/control tokenizer records are required")
        tokenizers = []
    ids: set[str] = set()
    for row in tokenizers:
        model_id = row.get("model_id") if isinstance(row, dict) else None
        if not isinstance(model_id, str) or not model_id or model_id in ids:
            issues.append(f"invalid or duplicate tokenizer model_id: {model_id}")
        ids.add(model_id)
        if not isinstance(row.get("repository"), str) or not row["repository"]:
            issues.append(f"{model_id}: repository is required")
        if not _is_revision(row.get("revision")):
            issues.append(f"{model_id}: immutable 40-character revision is required")
        artifacts = row.get("artifacts", {})
        tokenizer_json = artifacts.get("tokenizer_json", {}) if isinstance(artifacts, dict) else {}
        if not isinstance(tokenizer_json.get("url"), str) or row.get("revision", "") not in tokenizer_json.get("url", ""):
            issues.append(f"{model_id}: tokenizer_json URL must include the immutable revision")
        if not _is_sha256(tokenizer_json.get("sha256")):
            issues.append(f"{model_id}: tokenizer_json.sha256 is required")
        config_json = artifacts.get("tokenizer_config_json", {}) if isinstance(artifacts, dict) else {}
        if not _is_sha256(config_json.get("sha256")):
            issues.append(f"{model_id}: tokenizer_config_json.sha256 is required")
        elif isinstance(config_json.get("path"), str):
            config_path = (root / config_json["path"]).resolve()
            if not config_path.is_relative_to(root.resolve()) or not config_path.is_file():
                issues.append(f"{model_id}: tokenizer_config_json.path is unavailable")
            elif sha256_file(config_path).casefold() != config_json["sha256"].casefold():
                issues.append(f"{model_id}: tokenizer_config_json.sha256 does not match the snapshot")
        template = artifacts.get("chat_template", {}) if isinstance(artifacts, dict) else {}
        if template.get("source") not in ("standalone", "embedded"):
            issues.append(f"{model_id}: chat_template.source must be standalone or embedded")
        if template.get("source") == "standalone" and not _is_sha256(template.get("sha256")):
            issues.append(f"{model_id}: standalone chat_template.sha256 is required")
        if template.get("source") == "standalone" and isinstance(template.get("path"), str):
            template_path = (root / template["path"]).resolve()
            if not template_path.is_relative_to(root.resolve()) or not template_path.is_file():
                issues.append(f"{model_id}: standalone chat_template.path is unavailable")
            elif sha256_file(template_path).casefold() != template["sha256"].casefold():
                issues.append(f"{model_id}: standalone chat_template.sha256 does not match the snapshot")

    return {"valid": not issues, "issues": issues, "tokenizer_count": len(tokenizers)}


def _encode_ids(tokenizer: Any, text: str) -> list[int]:
    encoded = tokenizer.encode(text, add_special_tokens=False)
    ids = getattr(encoded, "ids", encoded)
    if not isinstance(ids, (list, tuple)) or not all(isinstance(item, int) for item in ids):
        raise ContextPacketError("tokenizer.encode must return token ids")
    return list(ids)


def _compose_context(target: int, position: str, needle: str, tokenizer: Any, filler_units: int) -> tuple[str, str, str]:
    filler = " filler" * filler_units
    if position == "begin":
        return needle + filler, "", filler
    if position == "end":
        return filler + " " + needle, filler, ""
    left = filler_units // 2
    right = filler_units - left
    prefix = " filler" * left
    suffix = " filler" * right
    return prefix + " " + needle + suffix, prefix, suffix


def _exact_context(target: int, position: str, needle: str, tokenizer: Any) -> tuple[str, str, str, list[int]]:
    if position not in CONTEXT_POSITIONS:
        raise ContextPacketError(f"unsupported position: {position}")
    if type(target) is not int or target not in CONTEXT_TARGETS:
        raise ContextPacketError(f"unsupported target: {target}")

    base = needle if position == "begin" else " " + needle
    base_count = len(_encode_ids(tokenizer, base))
    if base_count >= target:
        raise ContextPacketError("needle is larger than the requested context target")
    # Qwen's " filler" unit is one token. Search around the direct solution so
    # this remains correct for a tokenizer whose boundary rules differ.
    estimate = target - base_count
    for delta in range(-8, 9):
        units = estimate + delta
        if units < 0:
            continue
        text, prefix, suffix = _compose_context(target, position, needle, tokenizer, units)
        ids = _encode_ids(tokenizer, text)
        if len(ids) == target:
            return text, prefix, suffix, ids
    # A final bounded repair handles tokenizers that merge one of the filler
    # boundaries differently. It never pads with an unmeasured word count.
    units = max(0, estimate)
    for _ in range(64):
        text, prefix, suffix = _compose_context(target, position, needle, tokenizer, units)
        ids = _encode_ids(tokenizer, text)
        if len(ids) == target:
            return text, prefix, suffix, ids
        if len(ids) < target:
            units += 1
        else:
            units -= 1
            if units < 0:
                break
    raise ContextPacketError(f"could not construct exactly {target} tokens for {position}")


def build_probe(target: int, position: str, tokenizer: Any, model_id: str, max_model_len: int) -> dict[str, Any]:
    needle = f"CEDARTOKEN{target}{position.upper()}Q7F3"
    started = time.perf_counter()
    text, prefix, suffix, ids = _exact_context(target, position, needle, tokenizer)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    needle_text = needle if not prefix else " " + needle
    needle_count = len(_encode_ids(tokenizer, needle_text))
    needle_start = len(_encode_ids(tokenizer, prefix))
    if text.count(needle) != 1:
        raise ContextPacketError(f"{model_id}/{target}/{position}: needle occurrence is not unique")
    if needle_start + needle_count > len(ids):
        raise ContextPacketError(f"{model_id}/{target}/{position}: needle token span is outside context")
    return {
        "target_tokens": target,
        "position": position,
        "needle": needle,
        "needle_start_token": needle_start,
        "needle_token_count": needle_count,
        "token_count": len(ids),
        "truncated": len(ids) > max_model_len,
        "tokenization_latency_ms": elapsed_ms,
        "context": text,
        "context_sha256": sha256_bytes(text.encode("utf-8")),
        "needle_occurrences": text.count(needle),
    }


def _download(url: str) -> bytes:
    with urlopen(url, timeout=120) as response:
        return response.read()


def _load_tokenizer_bytes(row: dict[str, Any], local_path: Path | None, allow_download: bool) -> bytes:
    if local_path is not None:
        payload = local_path.read_bytes()
    elif allow_download:
        payload = _download(row["artifacts"]["tokenizer_json"]["url"])
    else:
        raise ContextPacketError(f"{row['model_id']}: tokenizer unavailable; supply --download or --tokenizer-dir")
    expected = row["artifacts"]["tokenizer_json"]["sha256"]
    actual = sha256_bytes(payload)
    if actual.casefold() != expected.casefold():
        raise ContextPacketError(f"{row['model_id']}: tokenizer hash mismatch ({actual})")
    return payload


def _tokenizer_from_bytes(payload: bytes) -> Any:
    try:
        from tokenizers import Tokenizer
    except ImportError as exc:  # pragma: no cover - exercised by CLI environment
        raise ContextPacketError("tokenizers package is required; use the pinned CP2 runtime") from exc
    return Tokenizer.from_str(payload.decode("utf-8"))


def _runtime_metadata(config: dict[str, Any]) -> dict[str, Any]:
    try:
        import tokenizers
        actual_tokenizers = tokenizers.__version__
    except ImportError:
        actual_tokenizers = None
    return {
        "configured": config["runtime"],
        "observed": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "tokenizers_version": actual_tokenizers,
            "backend": TOKENIZER_BACKEND,
        },
        "model_server_started": False,
        "pod_started": False,
        "model_behavior_claim": False,
    }


def _load_local_map(values: Iterable[str] | None) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values or []:
        if "=" not in value:
            raise ContextPacketError("--tokenizer-dir values must be MODEL_ID=PATH")
        model_id, raw_path = value.split("=", 1)
        if not model_id or not raw_path:
            raise ContextPacketError("--tokenizer-dir values must be MODEL_ID=PATH")
        result[model_id] = Path(raw_path).expanduser().resolve()
    return result


def generate_packet(config: dict[str, Any], output_dir: Path, *, tokenizer_dirs: Iterable[str] | None = None, download: bool = False) -> dict[str, Any]:
    checked = validate_context_config(config)
    if not checked["valid"]:
        raise ContextPacketError("Invalid CP2 config: " + "; ".join(checked["issues"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    local = _load_local_map(tokenizer_dirs)
    loaded: dict[str, Any] = {}
    artifact_rows: list[dict[str, Any]] = []
    for row in config["tokenizers"]:
        model_id = row["model_id"]
        source = local.get(model_id)
        payload = _load_tokenizer_bytes(row, source, download)
        loaded[model_id] = _tokenizer_from_bytes(payload)
        artifact_rows.append({
            "model_id": model_id,
            "repository": row["repository"],
            "revision": row["revision"],
            "tokenizer_json_sha256": sha256_bytes(payload),
            # The local cache is only an acquisition mechanism.  The durable
            # identity is the immutable URL and its verified SHA-256 hash.
            "source": "local_verified" if source else "immutable_url",
            "source_url": row["artifacts"]["tokenizer_json"]["url"],
        })

    primary = config["primary_tokenizer"]
    if primary not in loaded:
        raise ContextPacketError(f"primary tokenizer is not loaded: {primary}")
    probes: list[dict[str, Any]] = []
    for target in CONTEXT_TARGETS:
        for position in CONTEXT_POSITIONS:
            primary_probe = build_probe(target, position, loaded[primary], primary, config["runtime"]["max_model_len"])
            text = primary_probe.pop("context")
            counts: dict[str, dict[str, Any]] = {}
            for model_id, tokenizer in loaded.items():
                started = time.perf_counter()
                ids = _encode_ids(tokenizer, text)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                counts[model_id] = {
                    "token_count": len(ids),
                    "truncated": len(ids) > config["runtime"]["max_model_len"],
                    "tokenization_latency_ms": elapsed_ms,
                }
            primary_probe["probe_id"] = f"LC-{target // 1024}k-{position}"
            primary_probe["source_kind"] = "synthetic"
            primary_probe["in_frozen_suite"] = False
            primary_probe["context"] = text
            primary_probe["token_counts_by_tokenizer"] = counts
            primary_probe["synthetic_retrieval"] = {
                "needle_occurrences": text.count(primary_probe["needle"]),
                "needle_found": primary_probe["needle"] in text,
                "accuracy": 1.0 if text.count(primary_probe["needle"]) == 1 else 0.0,
            }
            primary_probe["model_retrieval_accuracy"] = None
            probes.append(primary_probe)

    metadata = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "packet_id": config["packet_id"],
        "generated_at": utcnow(),
        "config_sha256": sha256_bytes(json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "frozen_suite": config["frozen_suite"],
        "runtime": _runtime_metadata(config),
        "tokenizers": artifact_rows,
        "targets": list(CONTEXT_TARGETS),
        "positions": list(CONTEXT_POSITIONS),
        "probe_count": len(probes),
        "model_behavior_claim": False,
        "limits": [
            "Synthetic literal retrieval is a packet-integrity check, not model evidence.",
            "model_retrieval_accuracy remains null until a live qualification run.",
            "tokenization latency is measured only for the tokenizer backend; model latency is uncollected.",
        ],
    }
    write_json(output_dir / "metadata.json", metadata)
    (output_dir / "probes.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in probes), encoding="utf-8")
    report = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "kind": "actual_token_context_report",
        "status": "ready",
        "probe_count": len(probes),
        "expected_probe_count": 9,
        "primary_tokenizer": primary,
        "all_probes_outside_frozen_suite": all(row["in_frozen_suite"] is False for row in probes),
        "primary_exact_targets": all(row["token_count"] == row["target_tokens"] for row in probes),
        "model_behavior_claim": False,
        "model_retrieval_accuracy": None,
        "model_latency_collected": False,
        "truncation_is_reported_per_tokenizer": True,
        "tokenizer_artifacts": artifact_rows,
    }
    write_json(output_dir / "report.json", report)
    validation = validate_packet(output_dir, config)
    write_json(output_dir / "validation.json", validation)
    if not validation["valid"]:
        raise ContextPacketError("Generated packet failed validation: " + "; ".join(validation["issues"]))
    return {"metadata": metadata, "report": report, "validation": validation}


def validate_packet(output_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    try:
        metadata = read_json(output_dir / "metadata.json")
        report = read_json(output_dir / "report.json")
        rows = [json.loads(line) for line in (output_dir / "probes.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"valid": False, "issues": [f"packet unreadable: {type(exc).__name__}"]}
    if metadata.get("packet_id") != config.get("packet_id") or report.get("kind") != "actual_token_context_report":
        issues.append("packet identity is inconsistent")
    if metadata.get("model_behavior_claim") is not False or report.get("model_behavior_claim") is not False:
        issues.append("packet must not claim model behavior")
    if metadata.get("model_retrieval_accuracy") is not None or report.get("model_retrieval_accuracy") is not None:
        issues.append("model retrieval accuracy must remain null")
    expected = {f"LC-{target // 1024}k-{position}" for target in CONTEXT_TARGETS for position in CONTEXT_POSITIONS}
    observed = {row.get("probe_id") for row in rows}
    if observed != expected:
        issues.append("probe IDs do not cover exactly the nine required probes")
    if len(rows) != 9:
        issues.append("packet must contain exactly nine probes")
    max_len = config.get("runtime", {}).get("max_model_len")
    for row in rows:
        if row.get("in_frozen_suite") is not False or row.get("source_kind") != "synthetic":
            issues.append(f"{row.get('probe_id')}: synthetic/frozen boundary is invalid")
        if row.get("needle_occurrences") != 1 or row.get("synthetic_retrieval", {}).get("accuracy") != 1.0:
            issues.append(f"{row.get('probe_id')}: synthetic needle integrity failed")
        if row.get("context_sha256") != sha256_bytes(row.get("context", "").encode("utf-8")):
            issues.append(f"{row.get('probe_id')}: context hash mismatch")
        if not isinstance(max_len, int):
            issues.append("runtime.max_model_len missing")
        else:
            for model_id, counts in row.get("token_counts_by_tokenizer", {}).items():
                if counts.get("truncated") != (counts.get("token_count", 0) > max_len):
                    issues.append(f"{row.get('probe_id')}/{model_id}: truncation flag mismatch")
    return {"valid": not issues, "issues": issues, "probe_count": len(rows), "model_behavior_claim": False}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the CP2 actual-token context packet")
    parser.add_argument("--config", type=Path, default=ROOT / "config/t2-context.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="download tokenizer.json from immutable URLs")
    parser.add_argument("--tokenizer-dir", action="append", help="MODEL_ID=PATH to a local tokenizer.json")
    args = parser.parse_args(argv)
    config = read_json(args.config)
    result = generate_packet(config, args.output, tokenizer_dirs=args.tokenizer_dir, download=args.download)
    print(json.dumps({"status": "ready", "output": str(args.output), "probe_count": result["report"]["probe_count"]}))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
