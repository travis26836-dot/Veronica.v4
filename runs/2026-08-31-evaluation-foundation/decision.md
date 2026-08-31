# Evaluation foundation checkpoint — 2026-08-31

**Decision: offline evaluation preparation accepted; model qualification and training remain pending.**

The owner requested a reusable question/test/evaluation suite and a dataset improvement strategy, then explicitly authorized recorded conversational transcripts as evaluation inputs. This checkpoint does not reuse the terminated Pod's spending approval. No model endpoint, paid judge, training job, upload, or compute-provisioning operation was invoked. Foundation weights, persona, and the `Veronica` alias were not changed.

## Delivered

- [Evaluation guide](../../docs/evals/README.md), [question bank](../../docs/evals/QUESTION-BANK.md), [scorecard](../../docs/evals/SCORING.md), and [dataset strategy](../../docs/evals/DATASET-AND-FINETUNING-STRATEGY.md).
- `data/evals/veronica-core-v1.json`: 60 original development cases, 69 user turns, 12 categories, 25 release-blocker cases. Fourteen cases trace to existing failure evidence. All are exposed regression material, not sealed holdouts.
- `src/veronica_core/evaluation.py` and `scripts/evaluate_veronica.py`: offline validate/plan/import/report; an opt-in bounded collector for an already-running authorized endpoint. Real multi-turn history, case isolation, preserved failures, no tool/code execution, no automatic judge or retries, and a stop after three consecutive inference errors.
- `src/veronica_core/dataset_checks.py` and its script: draft structure, declared consent/approval, family split and exact evaluation overlap checks. Three illustrative SFT/DPO records remain draft and intentionally fail training-ready validation. This does not prove privacy, licensing, label correctness or semantic independence.
- `.agents/skills/veronica-evals/`: reusable project skill, discovered globally through `C:\Users\raine\.codex\skills\veronica-evals`, a verified junction to the canonical project folder. Existing Hugging Face evaluation/training skills are used as supporting workflows; no additional plugin installed.
- [Saved-conversation report](../2026-08-31-recorded-conversation-eval/report.md): three observed replies from one conversation family, original context and source hash preserved, three explicitly assistant-authored advisory reviews, no new model calls. Human adjudication is pending.

## Verification evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Full local software tests | **125 passed, 1 skipped**, one existing Starlette/TestClient deprecation warning | [offline-tests.txt](offline-tests.txt) |
| Extended bank validation | 60 cases / 69 completion requests planned; zero calls made | [suite-validation.json](suite-validation.json) |
| Smoke plan | 12 cases / 12 requests; at most 4,608 completion tokens | [smoke-plan.json](smoke-plan.json) |
| Core plan | 36 cases / 39 requests | [core-plan.json](core-plan.json) |
| Focused correction/memory plan | 4 cases / 6 requests; at most 1,152 completion tokens | [targeted-plan.json](targeted-plan.json) |
| Draft dataset structure | Three records pass with draft warnings | [dataset-structure.json](dataset-structure.json) |
| Training-ready refusal | Expected nonzero exit; all three drafts lack required approval/consent | [dataset-training-ready-refused.json](dataset-training-ready-refused.json) |
| Skill metadata validation | Passed | [skill-validation.txt](skill-validation.txt) |
| Reproducible command outcomes | Seven checks matched expected exit codes | [offline-checks.json](offline-checks.json) |

The local tests validate software using mock transport where HTTP behavior is needed. They do not measure Veronica's real inference quality. The skipped test is not a successful check. No benchmark, executable generated-code evaluation, live native-tool test or heldout qualification is claimed.

An independent review of the bank against the runner identified unnecessarily strict number/date substring checks; those were removed where the prompt did not mandate literal formatting. Equivalent JSON numbers such as `17` and `17.0` now compare correctly while booleans remain distinct. A regression test covers numeric tool arguments. Correct substrings still cannot substitute for full-answer review.

An independent skill forward test selected CC-01, CC-02, MB-01 and MB-02 and successfully previewed the bounded six-request plan offline. These four cases contain three independent families; CC-01's prior false answer is an explicit fixture, not a claim that a fresh model generated it. Input tokens and elapsed GPU time are additional, not included in the 1,152 completion-token bound. Truncation must be reviewed.

## Transcript assessment and next decision

The first reply has an ambiguous unsupported monitoring implication (advisory 2/4, no critical flag). The next two contain specific invented history, background integrations, telemetry and audio claims (advisory 0/4, critical flags). The owner name is actually supplied by the current persona; name recognition alone is not evidence of learning or memory. These are contextual review findings, not a population failure rate or a conclusion about consciousness. Current source is corroborating evidence, not independent attestation of every historical runtime detail.

The report remains `human_review_pending`, with `foundation_qualified=false`. Owner/human adjudication and a separately authorized small live baseline are the next decisions. Keep the user's chat available and conduct any future inference through a separate evaluation workload.

Improve the responsible layer first: verify the actual capabilities/system context, compare a grounded prompt against the current untouched base, then consider independently authored and reviewed training examples only if a measured behavior gap remains. Fine-tuning cannot create missing memory, tools, telemetry or audio. Use family-grouped splits, consent/provenance records, independent holdouts and reversible adapters; no automatic learning or scheduled spending is enabled.

Known unfinished work: live runner verification, full schema/executable-code/long-context environments, benchmark comparisons, human adjudication, independent qualification sets/statistical reports, approved datasets, actual fine-tuning, and final model selection. These remain open in `TODO.md`.
