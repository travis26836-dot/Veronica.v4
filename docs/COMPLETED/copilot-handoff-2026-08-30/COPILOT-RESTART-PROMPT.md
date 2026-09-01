# Copy into VS Code Copilot

**Update before resuming:** read `docs/STARTING-PROCEDURE.md` and the latest run decision first. The approved two-hour Pod has not started because RunPod's old auto-termination flags were ineffective. Use the `veronica-runpod-core` skill and preserve that hold; the original prompt below is historical context.

```text
Continue the existing Veronica.v4 build in this repository. You are resuming a handoff, not starting a new design. Read AGENTS.md, docs/SOURCE-OF-TRUTH.md, TODO.md, docs/SUBDEVELOPMENT-FIRST-CONVERSATION.md, docs/CODEX-CREDIT-CHECKPOINT.md, docs/COPILOT-HANDOFF.md, and the two latest decision files under runs/ before changing anything.

Goal: reach the first real, multi-turn Veronica chat through the public `Veronica` alias. The current model target is provisional Candidate A: huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated at revision e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f. Do not call it final, native-thinking-qualified, or a real inference result until evidence exists. Candidate B remains a later capability challenger.

Keep this core-first boundary: first text/chat, then qualification, then optional modules. Do not import the old v2 Image Studio, tool queue, workstation APIs, or media-generation backend into the core. The v2 visual layout/assets have already been ported to v4 and tested.

Work one checkpoint at a time. Start with Checkpoint A: Candidate A artifact integrity only. Save model-card/license snapshots at pinned revisions; locate the owner's copied artifact storage without duplicate downloading; create a complete manifest with paths, byte counts, SHA-256 values, and `.uploading` state. If storage cannot be safely inspected without paid compute, stop and ask the owner for the exact storage location. Do not create a Pod yet.

For every checkpoint: preserve the uncommitted worktree, use apply_patch for text edits, keep secrets uncommitted, run proportional validation, add a dated runs/<date>-<purpose>/ decision record, and only then mark the relevant TODO item complete. Completed/superseded TODO snapshots belong in docs/COMPLETED/; obsolete non-source material belongs in ARCHIVE/.

Paid RunPod safety: no Pod unless the owner gives a current maximum hourly price and UTC termination deadline. The existing volume is v53gj9flzs in EUR-IS-1, but do not assume the model is on it. The launch scripts are scaffolding, not authorization. Before any pause or when the Codex usage meter reaches the operator's 25% reserve, finish the active checkpoint, validate, and refresh docs/COPILOT-HANDOFF.md.

When you finish Checkpoint A, report only: evidence path, files validated, unresolved blocker (if any), and the exact next checkpoint. Do not start Checkpoint B in the same turn without owner approval.
```
