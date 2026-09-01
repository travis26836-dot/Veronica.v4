# Codex credit checkpoint

The exact account-level Codex credit balance is not available to this workspace agent. Do not infer it from RunPod credits, shell output, or token estimates.

## Safe operating rule

1. Treat the current handoff as a safe stop point: the UI port is verified, no model files were changed, and no Pod was created.
2. Before beginning a new checkpoint, the operator checks the Codex usage meter in the Codex/VS Code UI.
3. Stop at the end of the current small checkpoint—or immediately when the meter reaches the operator's 25% reserve—whichever occurs first. Do not begin a paid Pod, transfer, or destructive action unless enough Codex capacity remains to verify and clean it up.
4. Before stopping, run the relevant validation, update `TODO.md` only with evidence, write a dated `runs/` decision, and refresh the Copilot handoff.

The reserve is a conservative process guard, not a claim about a particular plan's remaining credits.
