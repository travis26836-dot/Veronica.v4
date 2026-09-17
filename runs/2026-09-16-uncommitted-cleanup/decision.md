# Pending-change cleanup

Decision: preserve September 14 launch evidence and commit focused maintenance changes.

- Consolidated three attempted warning filters into one message-specific pytest filter using UserWarning, the base of the installed StarletteDeprecationWarning. Dependency remediation remains open in TODO.md.
- Default core profile now selects one A100-SXM4-80GB, no automatic GPU fallbacks, and a $1.75/hour ceiling, matching AGENTS.md. Optional fallback machinery remains covered with an explicit test-only profile.
- Updated offline budget and launcher tests to cover the corrected ceiling.
- Preserved 38 September 14 artifacts across seven startup directories. All JSON parsed; a scan found no common private-key or provider-token patterns. Historical approvals and profile snapshots are evidence, not reusable authorization or current defaults.
- The final September 14 state records creationDefinitivelyRejected=true and confirmedAbsent=true; it does not prove inference.
- Ignored disposable runs/**/test-tmp*/ directories without deleting their contents.

Validation: uv run pytest tests -q -r a exited 0, with one Linux/WSL locking test skipped on Windows and no warning summary. Authored changes passed git diff --check with core.whitespace=cr-at-eol to accommodate existing CRLF-tracked files. Archived upstream model-card README snapshots contain trailing whitespace; preserved verbatim and excluded from the evidence whitespace check. No cloud resources started, no dependency upgrade, and no push performed.
