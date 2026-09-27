Live coding evaluations can report `extraction_failed` for complete, executable functions when an answer contains explanatory snippets or unfenced code. This prevents reliable coding measurements.

## Reproduction

In `src/veronica_core/capability_reports.py`, `extract_python()` merges all fenced chunks and parses the combined text before selecting definitions.

- CD-02 includes an explanatory Python block containing `page_count(0, 5) → 1`, standalone `return` examples, then a complete `def page_count(...)`. Merging these makes parsing fail. The answer's later test section is also truncated, but the function itself is complete.
- CD-03 starts with a complete, unfenced `def find_user(...)`, followed by prose and a fenced SQL example. Extraction fails even though the function is usable.
- Independently reviewed, unchanged function spans subsequently passed 9/9 and 3/3 fixtures in the existing verified Docker sandbox.

Evidence is retained locally in `runs/2026-09-23-live-coding/` (`results.jsonl`, `executable-code-report.json`, `reviewed-extraction-report.json`). These artifacts are not claimed to be published on GitHub.

## Acceptance checks

- Extract a complete requested function from the two response shapes above without executing anything on the host.
- Preserve required imports and helpers; reject ambiguous competing definitions or incomplete target functions.
- Record exact selected spans and source/response hashes. Preserve raw answers and truncation status.
- Keep independent fixture scoring and verified Docker isolation unchanged.
- Report extraction failure separately from an executed algorithm failure.
- Add regression tests for mixed explanatory fences, unfenced code plus prose, incomplete later test blocks, missing functions, and ambiguous definitions.

This is an evaluator defect. It does not make the separate CD-05 boolean-handling failure a pass.
