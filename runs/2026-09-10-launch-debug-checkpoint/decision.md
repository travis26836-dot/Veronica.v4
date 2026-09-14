# Launch Debug Checkpoint - 2026-09-10

**Decision:** Primary PowerShell launcher (`start-veronica.ps1`) repeatedly fails with "ApprovalFile does not exist" when invoked from the Hermes terminal tool due to path resolution/quoting issues between MSYS bash and PowerShell.

This is **not** a model or quota problem. We are still on `grok-4.20-0309-reasoning` (xAI SuperGrok/Premium+ OAuth). No rate limits or quota errors have been hit.

The `STARTING-PROCEDURE.md` documents both the .ps1 launcher **and** the lower-level Python controllers (`runpod_core.py` + `supervised_runpod.py`). We should have fallen back to the Python path after the first failure.

**Improvement recorded:**
- When the primary launcher fails due to environment-specific path problems, immediately switch to the Python supervised flow.
- Add frequent status polling and explicit "background task failed" messages for all long-running work.
- Make launcher invocation robust to MSYS/Windows path differences (use native PowerShell session or Python entrypoint).

**Current state:**
- Single model (Candidate A) remains wired and documented.
- No Pod is running.
- Approval.json and run directories were created but not consumed by the launcher.
- All live tasks (UI-ready verification, smoke tests, capability probes, clean termination) remain pending.

Work paused here per owner request. Ready to resume with Python-based launch on return.

**Owner acknowledgment:** Checkpoint accepted. Bug root cause and fallback strategy documented.  
**Next legitimate action:** Retry launch using Python controllers or switch provider if desired.