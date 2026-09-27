The evaluation evidence redactor removes ordinary numeric token-usage metrics because their field names contain `token`. This loses useful cost/context evidence and changes numeric fields into strings.

## Reproduction

`src/veronica_core/evaluation.py` uses `SECRET_FIELD_RE.search(key)` in `_redact_evidence()`. The pattern includes unqualified `token`.

Input:
```json
{"usage":{"prompt_tokens":387,"completion_tokens":18,"total_tokens":405}}
```

The saved parsed response has `[REDACTED]` for all three numeric values. The separately retained raw JSON string still contains the numeric counts, so the two representations disagree.

Observed in real September 23 schema/coding response records. Local evidence: `runs/2026-09-23-live-schema/results.jsonl`; raw artifacts are not claimed to be published here.

## Acceptance checks

- Preserve documented non-secret usage counters and their numeric types using narrowly scoped rules.
- Continue removing actual credentials, bearer values, API keys, access/refresh tokens, and explicitly supplied secret values throughout nested objects and strings.
- Do not broadly allow all fields containing `token`.
- Test standard usage objects, nested details, token-shaped credential fields, and mixed raw/parsed evidence.
- Keep byte hashes and truncation metadata meaningful and document their relation to redacted content.

No real credential values are required to reproduce or test this bug.
