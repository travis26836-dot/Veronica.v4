"""Offline dataset checks; never exports training data or trains a model."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

from .evaluation import DEFAULT_SUITE, read_json, read_jsonl


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def lint(records: list[dict], suite: dict, training_ready: bool = False) -> dict:
    errors, warnings, ids = [], [], set()
    family_splits, prompt_splits = defaultdict(set), defaultdict(set)
    eval_families = {c["family"] for c in suite["cases"]}
    eval_prompts = {normalized(t["user"]) for c in suite["cases"] for t in c["turns"]}
    eval_sources = {c.get("source", {}).get("path") for c in suite["cases"] if c.get("source", {}).get("path")}
    for index, record in enumerate(records):
        label = str(record.get("id") or f"row-{index + 1}")
        if not record.get("id") or label in ids:
            errors.append(f"{label}: missing or duplicate id")
        ids.add(label)
        family, split = record.get("family"), record.get("split")
        if not isinstance(family, str) or not family.strip() or split not in ("train", "validation", "test"):
            errors.append(f"{label}: valid family and split required")
            continue
        family_splits[family].add(split)
        if family in eval_families:
            errors.append(f"{label}: family is reserved for public regression")
        source = record.get("source", {})
        if not isinstance(source, dict) or source.get("kind") not in ("synthetic", "owner_transcript", "licensed_dataset"):
            errors.append(f"{label}: invalid source provenance")
            source = {}
        for key in ("reference", "license"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                errors.append(f"{label}: source.{key} required")
        for key in ("training_consent", "evaluation_only"):
            if type(source.get(key)) is not bool:
                errors.append(f"{label}: source.{key} must be boolean")
        if source.get("reference") in eval_sources:
            errors.append(f"{label}: source transcript is reserved for regression")
        if record.get("status") not in ("draft", "approved"):
            errors.append(f"{label}: status must be draft or approved")
        if training_ready:
            if record.get("status") != "approved" or not record.get("reviewer"):
                errors.append(f"{label}: training-ready requires approval and reviewer")
            if source.get("training_consent") is not True or source.get("evaluation_only") is not False:
                errors.append(f"{label}: training use is not authorized")
            if source.get("license", "").casefold() in ("unknown", "pending", "unreviewed"):
                errors.append(f"{label}: source rights are unresolved")
            if split == "test":
                errors.append(f"{label}: sealed test records cannot be included in training-ready input")
        elif record.get("status") == "draft":
            warnings.append(f"{label}: draft example, not training-ready")
        kind = record.get("type")
        groups = [record.get("messages")] if kind == "sft" else [record.get(k) for k in ("prompt", "chosen", "rejected")] if kind == "dpo" else []
        if not groups:
            errors.append(f"{label}: type must be sft or dpo")
            continue
        valid = True
        for group in groups:
            if not isinstance(group, list) or not group:
                valid = False
                break
            if any(not isinstance(m, dict) or m.get("role") not in ("system", "user", "assistant", "tool") or not isinstance(m.get("content"), str) or not m["content"].strip() for m in group):
                valid = False
        if not valid:
            errors.append(f"{label}: malformed message groups")
            continue
        if kind == "sft" and groups[0][-1]["role"] != "assistant":
            errors.append(f"{label}: SFT target must end in an assistant answer")
        if kind == "dpo":
            if any(len(g) != 1 or g[0]["role"] != "assistant" for g in groups[1:]):
                errors.append(f"{label}: chosen/rejected must each be one assistant answer")
            if groups[1] == groups[2]:
                errors.append(f"{label}: preference pair has identical chosen and rejected answers")
        for group in groups:
            for message in group:
                content = normalized(message["content"])
                if content in eval_prompts:
                    errors.append(f"{label}: exact text overlaps a public evaluation question")
        prompt = groups[0] if kind == "dpo" else groups[0][:-1]
        prompt_key = normalized(json.dumps(prompt, sort_keys=True, ensure_ascii=False))
        prompt_splits[prompt_key].add(split)
    for family, splits in family_splits.items():
        if len(splits) > 1:
            errors.append(f"family {family}: appears across splits {sorted(splits)}")
    for splits in prompt_splits.values():
        if len(splits) > 1:
            errors.append("Identical normalized prompt appears across splits")
    return {"records": len(records), "errors": errors, "warnings": warnings,
            "structurally_valid": not errors, "training_ready_checks_requested": training_ready,
            "training_authorized_by_tool": False,
            "limits": "Checks declared metadata and exact overlap only. Human review must verify consent, rights, correct answers, privacy, family assignments and semantic/paraphrase overlap. No export or training occurs."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--training-ready", action="store_true")
    args = parser.parse_args()
    try:
        records = [r for path in args.files for r in read_jsonl(path)]
        if not records:
            raise ValueError("Dataset has no records")
        result = lint(records, read_json(args.suite), args.training_ready)
        print(json.dumps(result, indent=2))
        if result["errors"]:
            raise SystemExit(1)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Dataset check stopped: {exc}\n")


if __name__ == "__main__":
    main()
