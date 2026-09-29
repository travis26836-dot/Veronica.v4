# Model Anchor Decision — 2026-09-29

**Owner direction:** "Let's do it." Explicit instruction to anchor the model, reconfigure rules as needed, stop the restart loop, and build forward from the installed model as Veronica core.

**Action taken:** Stage 0 of the core destination plan executed.

## Decision
- The installed model on RunPod volume `v53gj9flzs` (`huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` @ `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f`) is the **sole foundation**.
- Public name and API alias: `Veronica` (stable).
- Candidate B (`huihui-ai/Huihui-Qwen3.8-27B-abliterated`) is **retired** — no download, no comparison, no use.
- No new Veronica.v4.1 forks or donor projects for organization.
- The text model is the director. Image and video generation will be a separate diffusion worker (ComfyUI-style) that Veronica calls via tool use. The LLM itself does not generate pixels.
- Rules updated to make this the anchor. Future reconfigurations require explicit owner direction + evidence.

## Changes
- `config/model-registry.json`: selectionStatus → "owner_selected", Candidate B role → "retired_not_selected", added ownerDecision and date.
- `docs/SOURCE-OF-TRUTH.md` section 4: full rewrite declaring the lock, preserving history, clarifying text-directs-media separation.
- `docs/CURRENT-STATE.md`: added model anchor note.
- This plan updated and claim created.

## Evidence of prior progress (acknowledged)
- Cold start 2026-09-13: UI at :8010 before model fully loaded, multi-turn chat (including creative/adult-capable replies), mode switching, clean Pod termination with volume retained.
- This is real: you can spin up a powerful uncensored text model from a laptop + RunPod on demand.

## Why anchor first
Per AGENTS.md and SOURCE-OF-TRUTH section 5:
- Basic text/chat core precedes tool execution and media generation.
- "Tool execution, long-term memory, fine-tuning, media generation... remain off until this works."
- Anchoring stops the pattern of "playing around then starting over."

We can (and will) adapt rules, but the anchor is the foundation that lets us branch and add the image/video studio without losing the core.

## Next concrete step
Owner must provide a bounded duration (default 1 hour, $1.75 cap) for any paid Pod run.

Once authorized:
1. Run a fresh supervised text session.
2. Confirm basic multi-turn explicit natural language + ordinary task replies.
3. Record evidence.
4. Then implement the first tool (structured image prompt handoff).
5. Then wire a real uncensored diffusion worker.

**No GPU spend or Pod start until owner says the duration and confirms "go".**

Claim: coordination/tasks/active/anchor-veronica-model-2026-09-29.json

Handoff: Anchor complete. Ready for Stage 1 when authorized.