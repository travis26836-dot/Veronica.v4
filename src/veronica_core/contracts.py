"""Project contract schemas, fingerprints, immutable run folders, and provenance checks.

Never downloads weights, starts compute, or writes secrets.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Iterator

from . import __version__
from .persona import CORE_PERSONA, MODE_PROMPTS


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "config" / "schemas"
SCHEMA_NAMES = ("run-record", "model-record", "evaluation-case", "module-manifest")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
SECRET_KEY_RE = re.compile(
    r"(?:^|_)(api[_-]?key|token|secret|password|passwd|authorization|private[_-]?key|credentials?|bearer|ssh[_-]?key)s?$",
    re.I,
)
EXACT_SECRET_KEYS = {"privatekeyfile", "apikey", "accesskey"}
REQUIRED_RUN_DIRS = ("inputs", "outputs", "logs", "evaluations")
DEFAULT_FINGERPRINT_SOURCES = (
    "config/model-registry.json",
    "config/runpod-core.json",
    "config/workflow.json",
    "config/status-states.json",
)
CANONICAL_INSTANCES = (
    ("model-record", "config/model-registry.json"),
    ("evaluation-case", "data/evals/veronica-core-v1.json"),
)
IDENTITY_DEFAULTS = {
    "publicModel": "Veronica",
    "upstreamBaseUrl": "http://127.0.0.1:8000/v1",
    "upstreamModel": "huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated",
    "providerTimeoutSeconds": 180,
}


class SchemaError(ValueError):
    """One or more JSON Schema violations."""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def schema_path(name: str) -> Path:
    if name not in SCHEMA_NAMES:
        raise ValueError(f"Unknown schema: {name}")
    return SCHEMA_DIR / f"{name}.schema.json"


def load_schema(name: str) -> dict:
    schema = read_json(schema_path(name))
    if not isinstance(schema, dict):
        raise ValueError(f"Schema {name} must be an object")
    return schema


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def relative_to_root(path: Path, root: Path = ROOT) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _is_secret_key(key: str) -> bool:
    compact = key.replace("-", "").replace("_", "").casefold()
    return compact in EXACT_SECRET_KEYS or bool(SECRET_KEY_RE.search(key.replace("-", "_")))


def _json_equal(left: Any, right: Any) -> bool:
    if type(left) is bool or type(right) is bool:
        return type(left) is bool and type(right) is bool and left is right
    if type(left) in (int, float) and type(right) in (int, float) and type(left) is not bool and type(right) is not bool:
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_json_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return type(value) is bool
    if expected == "null":
        return value is None
    if expected == "integer":
        if type(value) is bool:
            return False
        if type(value) is int:
            return True
        return type(value) is float and value.is_integer()
    if expected == "number":
        return type(value) in (int, float) and type(value) is not bool
    return False


def _resolve_ref(root: dict, ref: str) -> Any:
    if not ref.startswith("#/"):
        raise SchemaError(f"Unsupported $ref: {ref}")
    current: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(current, dict) or part not in current:
            raise SchemaError(f"Unresolved $ref: {ref}")
        current = current[part]
    return current


def iter_schema_errors(instance: Any, schema: Any, *, root: dict, path: str = "$") -> Iterator[str]:
    if schema is True:
        return
    if schema is False:
        yield f"{path}: value is not allowed"
        return
    if not isinstance(schema, dict):
        yield f"{path}: invalid schema"
        return
    if "$ref" in schema:
        yield from iter_schema_errors(instance, _resolve_ref(root, schema["$ref"]), root=root, path=path)
        return
    if "type" in schema:
        expected = schema["type"]
        names = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(instance, name) for name in names):
            yield f"{path}: expected {'|'.join(names)}"
            return
    if "const" in schema and not _json_equal(instance, schema["const"]):
        yield f"{path}: expected const {schema['const']!r}"
    if "enum" in schema and not any(_json_equal(instance, option) for option in schema["enum"]):
        yield f"{path}: value is not in enum"
    if "allOf" in schema:
        for index, item in enumerate(schema["allOf"]):
            yield from iter_schema_errors(instance, item, root=root, path=f"{path}/allOf/{index}")
    if "anyOf" in schema:
        if not any(not list(iter_schema_errors(instance, item, root=root, path=path)) for item in schema["anyOf"]):
            yield f"{path}: no anyOf variant matched"
    if "oneOf" in schema:
        matches = [item for item in schema["oneOf"] if not list(iter_schema_errors(instance, item, root=root, path=path))]
        if len(matches) != 1:
            yield f"{path}: expected exactly one oneOf variant, matched {len(matches)}"
            return
    if "if" in schema:
        if not list(iter_schema_errors(instance, schema["if"], root=root, path=path)):
            if "then" in schema:
                yield from iter_schema_errors(instance, schema["then"], root=root, path=path)
        elif "else" in schema:
            yield from iter_schema_errors(instance, schema["else"], root=root, path=path)
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            yield f"{path}: shorter than minLength {schema['minLength']}"
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            yield f"{path}: longer than maxLength {schema['maxLength']}"
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            yield f"{path}: does not match pattern"
    if type(instance) in (int, float) and type(instance) is not bool:
        if "minimum" in schema and instance < schema["minimum"]:
            yield f"{path}: below minimum {schema['minimum']}"
        if "maximum" in schema and instance > schema["maximum"]:
            yield f"{path}: above maximum {schema['maximum']}"
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            yield f"{path}: fewer than minItems {schema['minItems']}"
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            yield f"{path}: more than maxItems {schema['maxItems']}"
        if schema.get("uniqueItems") and any(
            _json_equal(instance[i], instance[j]) for i in range(len(instance)) for j in range(i + 1, len(instance))
        ):
            yield f"{path}: items are not unique"
        item_schema = schema.get("items")
        if item_schema is not None and not isinstance(item_schema, list):
            for index, item in enumerate(instance):
                yield from iter_schema_errors(item, item_schema, root=root, path=f"{path}[{index}]")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                yield f"{path}: missing required property {key}"
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                yield from iter_schema_errors(value, properties[key], root=root, path=f"{path}.{key}")
            elif additional is False:
                yield f"{path}: unexpected property {key}"
            elif isinstance(additional, dict):
                yield from iter_schema_errors(value, additional, root=root, path=f"{path}.{key}")


def validate_instance(name: str, instance: Any) -> None:
    schema = load_schema(name)
    errors = list(iter_schema_errors(instance, schema, root=schema))
    if name == "evaluation-case" and isinstance(instance, dict):
        from .evaluation import validate_suite
        try:
            validate_suite(instance)
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        raise SchemaError("\n".join(errors))


def validate_file(name: str, path: Path) -> None:
    validate_instance(name, read_json(path))


def validate_canonical_contracts(root: Path = ROOT) -> dict:
    issues: list[str] = []
    validated = []
    for name in SCHEMA_NAMES:
        path = root / "config" / "schemas" / f"{name}.schema.json"
        record = {"schema": name, "path": relative_to_root(path, root), "role": "schema", "ok": False}
        try:
            schema = read_json(path)
            if not isinstance(schema, dict) or schema.get("$id") != f"{name}.schema.json":
                issues.append(f"{relative_to_root(path, root)}: schema $id must be {name}.schema.json")
            else:
                record["ok"] = True
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{relative_to_root(path, root)}: unreadable schema ({type(exc).__name__})")
        validated.append(record)
    for name, relative in CANONICAL_INSTANCES:
        path = root / relative
        record = {"schema": name, "path": relative, "role": "instance", "ok": False}
        try:
            validate_file(name, path)
            record["ok"] = True
        except (OSError, ValueError, json.JSONDecodeError, SchemaError) as exc:
            issues.append(f"{relative}: {exc}")
        validated.append(record)
    return {
        "schemas": list(SCHEMA_NAMES),
        "validated": validated,
        "issues": issues,
        "ok": not issues,
        "paidComputeStarted": False,
        "weightsDownloaded": False,
    }


def identity_block() -> dict:
    return {
        "publicAlias": "Veronica",
        "packageVersion": __version__,
        "personaSha256": hashlib.sha256(CORE_PERSONA.encode("utf-8")).hexdigest(),
        "modes": sorted(MODE_PROMPTS),
        **IDENTITY_DEFAULTS,
    }


def redact(value: Any, prefix: str = "") -> tuple[Any, list[str]]:
    removed: list[str] = []
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            pointer = f"{prefix}.{key}" if prefix else key
            if _is_secret_key(str(key)):
                removed.append(pointer)
                continue
            child, nested = redact(item, pointer)
            cleaned[key] = child
            removed.extend(nested)
        return cleaned, removed
    if isinstance(value, list):
        cleaned_list = []
        for index, item in enumerate(value):
            child, nested = redact(item, f"{prefix}[{index}]")
            cleaned_list.append(child)
            removed.extend(nested)
        return cleaned_list, removed
    return value, removed


def default_fingerprint_sources(root: Path = ROOT) -> list[Path]:
    return [root / relative for relative in DEFAULT_FINGERPRINT_SOURCES]


def generate_fingerprint(
    sources: list[Path] | None = None,
    *,
    include_identity: bool = True,
    root: Path = ROOT,
) -> dict:
    paths = list(sources) if sources is not None else default_fingerprint_sources(root)
    files: dict[str, Any] = {}
    redacted: list[str] = []
    source_records = []
    for path in paths:
        data = read_json(path)
        if not isinstance(data, dict) and not isinstance(data, list):
            raise ValueError(f"Fingerprint source must be JSON object or array: {path}")
        cleaned, keys = redact(data)
        label = relative_to_root(path, root)
        files[label] = cleaned
        redacted.extend(f"{label}:{key}" for key in keys)
        source_records.append({"path": label, "sha256": hashlib.sha256(canonical_json(cleaned).encode("utf-8")).hexdigest()})
    payload: dict[str, Any] = {"files": files}
    if include_identity:
        identity = identity_block()
        payload["identity"] = identity
        source_records.append({"path": "identity", "sha256": hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()})
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return {
        "schemaVersion": 1,
        "algorithm": "sha256",
        "digest": digest,
        "encoding": "json-utf8-sort_keys-separators-comma-colon",
        "identityIncluded": include_identity,
        "sources": source_records,
        "redactedKeys": redacted,
        "secretsOmitted": True,
        "paidComputeStarted": False,
        "weightsDownloaded": False,
    }


def _write_keep(directory: Path) -> None:
    (directory / ".keep").write_text("", encoding="utf-8")


def init_run_folder(
    run_id: str,
    *,
    stage: str = "establish",
    scope: str = "Durable contract artifacts.",
    owner: str = "Raine",
    runs_root: Path | None = None,
    fingerprint: bool = True,
    root: Path = ROOT,
) -> Path:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("Run id must be a named token matching [A-Za-z0-9][A-Za-z0-9_-]*")
    runs_root = (runs_root or (root / "runs")).resolve()
    destination = (runs_root / run_id).resolve()
    if destination.parent != runs_root:
        raise ValueError("Run folder must be a direct child of runs/")
    if destination.exists():
        raise FileExistsError(f"Run folder already exists and must not be overwritten: {destination}")
    destination.mkdir(parents=False, exist_ok=False)
    try:
        for name in REQUIRED_RUN_DIRS:
            folder = destination / name
            folder.mkdir()
            _write_keep(folder)
        digest = None
        if fingerprint:
            record = generate_fingerprint(root=root)
            digest = record["digest"]
            write_json(destination / "configuration-fingerprint.json", record)
        run_record = {
            "schemaVersion": 1,
            "runId": run_id,
            "recordedAt": utcnow(),
            "owner": owner,
            "stage": stage,
            "status": "in_progress",
            "scope": scope,
            "modelInferencePerformed": False,
            "paidGpuStarted": False,
            "weightsModified": False,
            "modelSelectionStatus": "benchmark_required",
            "modelRevision": None,
            "runtimeVersion": None,
            "gpu": None,
            "configurationFingerprint": digest,
            "lastDurableHandoff": "Run folder initialized; evidence pending.",
            "nextAction": "Record decision.md and required evidence. Do not overwrite this folder.",
        }
        validate_instance("run-record", run_record)
        write_json(destination / "run.json", run_record)
        (destination / "decision.md").write_text(
            f"# {run_id}\n\n**Decision:** pending.\n\n"
            "This run folder was created by the immutable initializer. Replace this stub with the recorded decision.\n\n"
            "## Limits\n\n- Secrets must never be written into this folder.\n- Do not overwrite this run directory.\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def _snapshot_status(snapshot: Path) -> dict:
    issues = []
    if not snapshot.is_dir():
        issues.append("provenance snapshot directory is missing")
        return {
            "snapshot": "missing",
            "readme": "missing",
            "license": "missing",
            "issues": issues,
        }
    readme = snapshot / "README.md"
    license_file = snapshot / "LICENSE"
    readme_state = "present" if readme.is_file() and readme.stat().st_size > 0 else "missing"
    license_state = "present" if license_file.is_file() and license_file.stat().st_size > 0 else "missing"
    if readme_state != "present":
        issues.append("README.md is missing or empty")
    if license_state != "present":
        issues.append("LICENSE is missing or empty")
    return {
        "snapshot": "present",
        "readme": readme_state,
        "license": license_state,
        "issues": issues,
    }


def check_license_provenance(registry_path: Path | None = None, root: Path = ROOT) -> dict:
    registry_path = registry_path or (root / "config" / "model-registry.json")
    registry = read_json(registry_path)
    rows = list(registry.get("candidates", [])) + list(registry.get("controls", []))
    models = []
    issues: list[str] = []
    for row in rows:
        model_id = row.get("id") or "<missing-id>"
        revision = row.get("revision")
        if isinstance(revision, str) and REVISION_RE.fullmatch(revision):
            revision_state = "present"
        elif revision in (None, ""):
            revision_state = "missing"
        else:
            revision_state = "invalid"
        snapshot_value = row.get("provenanceSnapshot")
        if not isinstance(snapshot_value, str) or not snapshot_value.strip():
            snapshot_info = {
                "snapshot": "missing",
                "readme": "missing",
                "license": "missing",
                "issues": ["provenanceSnapshot path is missing"],
            }
            snapshot_path = None
        else:
            snapshot_path = (root / snapshot_value).resolve()
            if not snapshot_path.is_relative_to(root.resolve()):
                snapshot_info = {
                    "snapshot": "missing",
                    "readme": "missing",
                    "license": "missing",
                    "issues": ["provenanceSnapshot escapes the project root"],
                }
            else:
                snapshot_info = _snapshot_status(snapshot_path)
        model_issues = []
        if revision_state != "present":
            model_issues.append("immutable revision is missing or not a 40-character SHA")
        model_issues.extend(snapshot_info["issues"])
        if not row.get("licenseDeclared"):
            model_issues.append("licenseDeclared is missing")
        record = {
            "id": model_id,
            "role": row.get("role"),
            "repository": row.get("repository"),
            "revision": revision_state,
            "revisionValue": revision if revision_state == "present" else None,
            "licenseDeclared": row.get("licenseDeclared"),
            "snapshot": snapshot_info["snapshot"],
            "readme": snapshot_info["readme"],
            "license": snapshot_info["license"],
            "provenanceSnapshot": snapshot_value,
            "issues": model_issues,
            "complete": not model_issues,
        }
        models.append(record)
        issues.extend(f"{model_id}: {item}" for item in model_issues)
    return {
        "schemaVersion": 1,
        "registry": relative_to_root(registry_path, root),
        "models": models,
        "checked": len(models),
        "complete": sum(1 for model in models if model["complete"]),
        "issues": issues,
        "ok": not issues,
        "networkAccess": False,
        "weightsDownloaded": False,
        "paidComputeStarted": False,
        "limits": "Presence checklist only. It does not download weights, fetch remote cards, start compute, or replace legal review.",
    }


def _print(value: dict) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def _add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=ROOT)


def validate_contracts_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate canonical JSON documents against Establish schemas.")
    _add_root_argument(parser)
    parser.add_argument("--schema", choices=SCHEMA_NAMES)
    parser.add_argument("--instance", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.instance is not None:
            if args.schema is None:
                raise ValueError("--instance requires --schema")
            validate_file(args.schema, args.instance)
            _print({"ok": True, "schema": args.schema, "path": str(args.instance), "paidComputeStarted": False})
            return
        result = validate_canonical_contracts(args.root)
        _print(result)
        if not result["ok"]:
            raise SystemExit(1)
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as exc:
        parser.exit(2, f"Contract validation stopped: {exc}\n")


def fingerprint_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Hash non-secret profile, runtime, and identity settings.")
    _add_root_argument(parser)
    parser.add_argument("--source", action="append", type=Path)
    parser.add_argument("--no-identity", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = generate_fingerprint(args.source, include_identity=not args.no_identity, root=args.root)
        if args.output is not None:
            write_json(args.output, result)
        _print(result)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Fingerprint stopped: {exc}\n")


def init_run_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create an immutable runs/<id>/ folder with required stubs.")
    _add_root_argument(parser)
    parser.add_argument("run_id")
    parser.add_argument("--stage", default="establish")
    parser.add_argument("--scope", default="Durable contract artifacts.")
    parser.add_argument("--owner", default="Raine")
    parser.add_argument("--runs-dir", type=Path)
    parser.add_argument("--no-fingerprint", action="store_true")
    args = parser.parse_args(argv)
    try:
        path = init_run_folder(
            args.run_id,
            stage=args.stage,
            scope=args.scope,
            owner=args.owner,
            runs_root=args.runs_dir,
            fingerprint=not args.no_fingerprint,
            root=args.root,
        )
        _print({"ok": True, "path": str(path), "runId": args.run_id, "overwritten": False})
    except FileExistsError as exc:
        parser.exit(1, f"{exc}\n")
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as exc:
        parser.exit(2, f"Run folder initializer stopped: {exc}\n")


def provenance_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Checklist pinned README/LICENSE/revision snapshots without downloading weights or starting compute."
    )
    _add_root_argument(parser)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check_license_provenance(args.registry, args.root)
        if args.output is not None:
            write_json(args.output, result)
        _print(result)
        if not result["ok"]:
            raise SystemExit(1)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Provenance checklist stopped: {exc}\n")
