# Alternative GPU startup and diagnostic

The owner explicitly approved one RTX PRO 6000 Blackwell Server Edition on
Secure Cloud at up to $2.09/hour for 60 minutes, after A100 stock and Community
allocation failures. The normal profile ceiling remains $1.75/hour.

Pod `xfa252ehpmuzzx` was created at 08:26:53 UTC on 2026-09-23. The fixed
supervised termination deadline is 09:26:53 UTC (05:26:53 America/New_York).
This is local supervision, not a provider-enforced timer. Consult
`termination.json` for actual closure; this startup record alone does not prove
the Pod is stopped.

## Verified startup

- Stored model files passed full integrity verification.
- The UI opened before inference completed.
- `provider-smoke.json` and `wrapper-smoke.json` contain real generated replies.
- `startup-ready.json` records successful startup at 08:35:02 UTC.
- A browser exchange returned an actual Veronica introduction.
- `configuration-fingerprint.json`, model manifest, GPU and runtime records
  preserve the actual serving configuration.

## Diagnostic results

The approved four-case, six-request selection was run once through the wrapper
and once directly, at 192 maximum output tokens per request. Both collected
six responses with zero transport errors. Evidence:

- `../2026-09-23T083500Z-alternative-diagnostic/`
- `../2026-09-23T083700Z-alternative-direct-diagnostic/`

Assistant inspection found invented prior quotes on MB-01 and false agreement
with 17 + 26 = 44 on CC-02 in both surfaces. Current-session jasmine recall
worked. CC-01 correction was verbose and truncated, with unsupported claims
remaining. These are advisory findings pending human adjudication. They show
that the wrapper is not the sole cause; they do not isolate model weights from
the serving template/runtime. No weights or persona were changed.

## Qualification limits

This is a diagnostic alternative using vLLM 0.11.0, an 8K context and Blackwell.
It is not the frozen matched four-model T2 runtime. No foundation qualification
or selection is earned. The CP4 wrapper-evidence validator issue discovered
during independent review is being repaired separately; its earlier ready
boolean must not be used as full qualification-readiness proof.

Next action: preserve the live chat session until owner STOP or the fixed
deadline; confirm exact Pod absence, then review the diagnostic and corrected
readiness packet before another qualification run.
