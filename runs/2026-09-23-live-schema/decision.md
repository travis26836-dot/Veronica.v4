# Live schema diagnostic

Five real responses from the existing owner-authorized alternative Pod, through
the Chat-mode wrapper. 512 maximum output tokens per case; five independent
fresh conversations; no transport errors. Full requests/responses and runtime
references are retained in results.jsonl and manifest.json.

Independent strict schema gate: SO-01, SO-02, SO-03, SO-05 pass. SO-04 fails
json_value_mismatch: the title includes instruction text rather than only the
requested literal title. See strict-schema-report.json. Human semantic review
remains open. This is public diagnostic evidence, not full qualification.

The owner can inspect every prompt and actual response at http://127.0.0.1:8766/
or the durable ../2026-09-23-visible-evals/public/index.html file.
Next: review the failed literal extraction, retain its unchanged output, and
resolve matched runtime/template provenance before a full T2 comparison.
