# Veronica.v4 Current State

**Status date:** 2026-09-25
**Update rule:** authority changes only through an explicit dated decision, never filesystem modification time.

## Current authority

- Canonical product definition: `docs/SOURCE-OF-TRUTH.md`
- Execution checklist: `TODO.md`
- Authoritative current decision: `runs/2026-09-25-installed-foundation-identity/decision.md`
- Collaboration contract: `docs/AGENT-COLLABORATION.md`

## Active state

- The sole active foundation configuration is the installed foundation baseline in `config/model-registry.json`.
- The only public API/model alias is **`Veronica.v.4.1-30B-A3B-BF16`**.
- The internal record pins the repository/revision, persistent-storage path, Apache-2.0 declaration, Qwen3MoeForCausalLM architecture, and BF16/no-quantization state.
- Full live baseline qualification is **pending**. No inference occurred during the identity migration.
- Historical RunPod smoke evidence remains preserved and does not constitute full qualification.
- The Pod is not asserted to be running. Any new paid run requires fresh explicit, bounded owner authorization.

## Important limitations

- Native tools, long-context stress, complete JSON-schema qualification, executable-code isolation, and final human review remain open.
- Prompt-preset modes do not prove native behavior.
- Persistent storage presence and previous smoke responses are not full qualification evidence.
- Saved run records describe their observed time; they are not current resource status.

## Next legitimate action

Run the offline baseline protocol validation and local test suite. A live baseline collection may occur only after a fresh authorized RunPod start, with all missing evidence recorded and the foundation held pending a signed decision.
