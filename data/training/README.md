# Training data staging area

Status: draft preparation only. No approved training dataset or trained adapter exists here.

Use the [evaluation-to-improvement strategy](../../docs/evals/DATASET-AND-FINETUNING-STRATEGY.md) for the staged process, proposed collection sizes, review rubric, split rules, and promotion gates. Model qualification and prompt/runtime improvements precede any training.

## What belongs here

Store only curated data artifacts, dataset manifests, and approval records here. Keep raw/private transcripts in their original local `runs/` evidence folders, implementation in `src/`, and large research downloads in `NON-SOURCE CODE/`. Do not copy an owner's entire chat history into this directory by default.

The owner authorized recorded conversations for evaluation. Training, remote grading/processing, and publication each need their own recorded permission. A source with unknown rights or consent is quarantined, not exportable.

## Illustrative files

- `examples/sft-draft.jsonl`: two original format demonstrations using conversational `messages`.
- `examples/dpo-draft.jsonl`: one original preference-format demonstration with a shared prompt and chosen/rejected completions.

These are synthetic, original documentation examples written by the evaluation author, not observed Veronica outputs, vetted gold, or authorized training data. `status=draft`, `source.training_consent=false`, `source.evaluation_only=true`, and `reviewer=null` are deliberate. `split=train` is only a proposed format field: these illustrative records remain excluded from every released dataset. These visible examples also belong on the regression-exclusion ledger if future candidate datasets are compared against them.

Each line carries provenance fields plus trainer content: `id`, `type`, `family`, `split`, `status`, `source`, and `reviewer`, with `messages` for SFT or `prompt`/`chosen`/`rejected` for DPO. A future approved exporter would pass only approved trainer-content fields to the trainer; do not feed review metadata into the model. No exporter or training job is implied by these examples. When a correction task includes an incorrect prior assistant answer, prefer converting it to prompt/completion format so the incorrect answer receives no positive training loss.

## Required checks before any export

1. Verify source ownership/licensing, exact-purpose permissions, redaction, independent answer evidence, and reviewer approval. Record source hash and turn/derivation lineage. Never treat raw AI claims as truth.
2. Assign all related conversation turns, paraphrases, translations, templates, and preference pairs to one family; split families before augmentation. Keep published eval/regression families and illustrative examples excluded from training and validation. Check exact and reviewed near-duplicate overlap.
3. Freeze IDs, hashes, family splits, consent/license records, and export destination. Tokenize and inspect completion masks, EOS, and truncation with the actual pinned tokenizer/template. Require the capable-core gate and a separately bounded training approval before launching anything.

Suggested future dataset release layout, not an assertion that these files already exist:

```text
data/training/<dataset-version>/
  manifest.json          # IDs/hashes/family-to-split map; no raw secrets
  dataset-card.md        # provenance, rights, composition, limitations
  approvals.jsonl       # separate evaluation/training/remote/publication decisions
  train.sft.jsonl        # approved prompt/completion samples only
  validation.sft.jsonl  # development holdout; never trained
  train.dpo.jsonl        # optional later preference stage
  review-log.jsonl       # rubric, reviewers, adjudication
```

Sealed-test data belongs in a separately controlled location, not beside training inputs by default. Record the real access controls; a directory name alone does not make a holdout sealed. Preserve adapters separately from the foundation, with dataset and checkpoint hashes, and never merge during the initial adaptation stage.

Export schemas follow TRL's conversational [SFT format](https://huggingface.co/docs/trl/sft_trainer) and [DPO format](https://huggingface.co/docs/trl/v1.12.0/en/dpo_trainer). These links describe formats, not permission or readiness to train.
