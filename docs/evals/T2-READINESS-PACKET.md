# T2 readiness packet

The CP4 packet is an offline manifest for the frozen foundation qualification.
It makes the protocol inputs reviewable before any paid run: protocol and suite
hashes, runtime pins, thresholds, case IDs, sampling, model/control matrix, and
required evidence are recorded together.

Build or validate it with:

```powershell
uv run python scripts/build_t2_readiness_packet.py build `
  --packet runs/<run-id>/t2-readiness-packet.json `
  --report runs/<run-id>/t2-readiness-report.json

uv run python scripts/build_t2_readiness_packet.py validate `
  --packet runs/<run-id>/t2-readiness-packet.json `
  --report runs/<run-id>/t2-readiness-report.json
```

The builder accepts `--cp2-evidence` and `--cp3-evidence` when those checkpoint
wrapper records exist. A complete wrapper must identify its checkpoint and
contain a decision reference plus a typed artifact list. Every reference must
include a repository-relative path and SHA-256, for example:

```json
{
  "checkpoint": "actual-token-context-packet",
  "status": "complete",
  "decision": {"path": "runs/.../decision.md", "sha256": "..."},
  "artifacts": [
    {"kind": "config", "path": "config/t2-context.json", "sha256": "..."},
    {"kind": "report", "path": "runs/.../report.json", "sha256": "..."}
  ]
}
```

The validator follows every reference and checks the real CP2/CP3 report and
artifact contents. A `status: complete` wrapper with no transitive evidence is
rejected, even when its own wrapper hash is valid. Until both dependency
records are supplied and validated, the report is `hold`. A structurally valid
hold is useful evidence that the packet is assembled; it is not CP4 completion
and does not qualify a model.

The packet intentionally preserves these boundaries:

- It uses `config/t2-qualification.json` and the published 60-case suite as
  frozen inputs; synthetic long-context cases remain outside that suite.
- It records the four-model, two-pair matrix and all ten required model-track
  runs without collecting responses.
- It cannot claim paid compute, foundation qualification, or model selection.
- It requires CP2 actual-token context evidence and CP3 evaluator-integrity
  evidence before it can report `ready`.
- Its negative path rejects changed hashes, missing fields, escaped evidence
  paths, complete-only wrappers, mutated transitive artifacts, incomplete
  dependencies, and false qualification claims.

The packet validator only establishes readiness. Live inference, raw response
collection, human review, comparison, and the signed selection decision remain
M2 work after CP4 and fresh bounded owner authorization.
