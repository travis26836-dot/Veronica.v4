# Veronica response evaluation

This is an offline-ready development evaluation system, not a training job or a qualified model. The Pod remains off. It uses original questions, recorded conversations, explicit expected behavior, and full-answer review. There is no paid judge, automatic cloud start, code execution, or automatic training.

## Start here

1. Read the [question bank](QUESTION-BANK.md) to choose a short interview or targeted weak-point tests.
2. Use the [scorecard](SCORING.md) to review saved responses, including the existing first-conversation transcript.
3. Use the [dataset and fine-tuning strategy](DATASET-AND-FINETUNING-STRATEGY.md) only after identifying which layer actually needs improvement.

The repeatable skill is **`veronica-evals`**. Example: "Use veronica-evals to review this transcript, add regression coverage, and propose the smallest next experiment. Do not start a Pod."

## What is included

| Component | Purpose |
| --- | --- |
| `data/evals/veronica-core-v1.json` | Versioned original cases, factual fixtures, questions, multi-turn follow-ups, objective checks and human rubrics |
| `scripts/evaluate_veronica.py` | Offline validation/planning, bounded requests to an already-running endpoint, saved-transcript intake and reporting |
| `scripts/check_training_dataset.py` | Offline structural/approval/family-split/exact-overlap checks; no exporter or trainer |
| `data/training/examples/` | Three illustrative SFT/DPO records; draft and deliberately not training-ready |
| `runs/<eval-run>/` | Immutable collection identity and raw outputs, editable review copies, generated reports |

Coverage: identity grounding, memory boundaries, action truthfulness, correction/calibration, instruction following, social understanding, reasoning consistency, coding, structured output, tool selection, context retrieval and creative writing. Tool fixtures test native selection/arguments only. Coding execution and full long-context stress/vision testing need later specialized environments; this pack does not qualify those capabilities.

The tiers are **12 smoke**, **36 core including smoke**, and **60 extended including both earlier tiers**. A case can have multiple turns, so case count is not request count. All questions here are public development/regression material, including known transcript incidents. None is a sealed holdout. The 60-case bank is an initial screen; it is not the larger qualification sample proposed in the strategy.

For the lowest-cost next diagnostic, select **CC-01, CC-02, MB-01 and MB-02**: correcting invented history, resisting an incorrect correction, admitting missing memory, and recalling supplied facts. These are four cases, six requests and three independent families. At 192 maximum completion tokens per request, the upper completion budget is **1,152 tokens**, plus input tokens; truncation must remain visible. This is a focused screen, not full qualification:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_veronica.py plan --tier core --case-id CC-01 --case-id CC-02 --case-id MB-01 --case-id MB-02 --max-tokens 192 --max-calls 6 --max-output-tokens 1152
```

The existing conversation has already been imported and given clearly labeled assistant advisory reviews in [the recorded-conversation report](../../runs/2026-08-31-recorded-conversation-eval/report.md). Human adjudication remains pending. These are three replies from one conversation, not three independent trials. The original false answers remain evidence, not positive training targets.

## Three offline commands

Run from the Veronica.v4 project directory with its existing environment. These commands use no model or paid endpoint:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_veronica.py validate --tier extended
.\.venv\Scripts\python.exe scripts/evaluate_veronica.py plan --tier smoke
.\.venv\Scripts\python.exe scripts/evaluate_veronica.py import-transcript --input runs/2026-08-31T034034Z-start-veronica/retained-ui-conversation.txt --run-dir runs/first-chat-review-example
```

The import requires a new run directory and never overwrites an existing one. Use a new name if it already exists. It accepts the saved `Message N`/`YOU`/`VERONICA` browser export or JSON containing `messages` with role/content pairs. It ignores the UI's SYSTEM welcome notice, which is not the real injected system prompt. It preserves observed assistant mistakes as evidence; it does not label them correct or turn them into training targets. Arbitrary transcript formats are rejected rather than guessed.

Inspect `results.jsonl`, copy `review-template.jsonl` to a separate review file, then fill the score, critical-failure flag, reviewer identity/type and rationale. Generate a new report without spending inference tokens:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_veronica.py report --run-dir runs/first-chat-review-example --reviews runs/first-chat-review-example/reviews.jsonl
```

Assistant-produced reviews must say `reviewer_type: "assistant"`; they are advisory and cannot satisfy the human review gate. Do not label an agent as a human reviewer. Retain independent human/owner adjudication for critical findings. This tool validates a declaration, not the real identity of a reviewer.

## Live evaluation, only when authorized

The runner does not provision, start, extend or terminate compute. Start Veronica through its existing skill only under a fresh request/duration approval. Open the UI early. Run evals as a separate workload, not by injecting messages into the owner's chat. The A100 runtime currently allows one sequence, so evaluation requests can delay interactive replies; keep concurrency at one and agree on the short test window.

For T2 foundation qualification, first validate the frozen four-model protocol offline:

```powershell
.\.venv\Scripts\python.exe scripts/verify_t2_qualification.py protocol
```

The protocol is `config/t2-qualification.json`. It pins both candidates and both official controls, matched runtime requirements, selected cases, sampling settings and evidence gates. Its verifier never starts compute or selects a model. The prior Candidate A smoke run cannot be substituted because it used an older runtime and did not include the other three models.

After all live runs and human reviews exist, copy `config/t2-comparison-inputs.template.json`, replace every placeholder with the actual evidence paths, and audit the complete matrix:

```powershell
.\.venv\Scripts\python.exe scripts/verify_t2_qualification.py compare --inputs runs/ACTUAL-T2-COMPARISON/comparison-inputs.json
```

The comparison remains `hold` if a required run, paired sample, human review, artifact manifest, runtime attestation, executable-code report, long-context report, native-tool report or adjudication record is absent.

First preview the selected pack. The plan counts completion calls and the configured maximum completion tokens. It does **not** estimate input tokens, elapsed time or dollars; full conversation history is resent each turn. Choose limits compatible with the remaining Pod deadline, with a cleanup margin. `max_seconds` stops new requests once elapsed; HTTP phase timeouts bound in-flight I/O but are not a cloud billing timer. A disconnected client does not prove server work stopped.

Example for an already-running authorized wrapper; replace the runtime record and run-directory names with the actual new run:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_veronica.py run --execute --tier smoke --base-url http://127.0.0.1:8010/v1 --surface wrapper --runtime-record runs/ACTUAL-START-RUN/profile.json --run-dir runs/ACTUAL-EVAL-RUN --max-seconds 600 --max-calls 30 --max-output-tokens 12000
```

Use `--top-p` and `--thinking disabled|enabled` exactly as frozen for the selected T2 track. These values are copied into every request and the run manifest so mismatched sampling or reasoning modes cannot masquerade as a fair comparison.

Use the active UI port if different; the earlier session used 8011. The runner requires the model alias advertised by `/v1/models`. `--surface wrapper` sends `veronica_mode`; `--surface direct` does not. The direct Pod tunnel needs its private credential in an environment variable, passed only by variable **name** with `--api-key-env`. Do not copy a key into commands, files, reports or chat. Existing private-state handling is in the startup controller; no key extraction is required for ordinary wrapper evaluation.

Each case/repetition begins with a fresh conversation. Within a multi-turn case, subsequent questions receive the model's actual previous replies. `initial_messages` are explicit supplied fixtures, not proof a new model generated those messages. Targets, graders and rubrics are never included in the request. Unknown/unsupported tools may produce API errors: record and diagnose them, never turn them into a success. Native calls are saved but **never executed**. A call before a follow-up ends that case incomplete because no tool result is fabricated.

Only loopback endpoints are allowed by default. `--allow-remote` is required for another destination, but a flag is not user permission to disclose private transcripts. No redirects or proxy environment settings are followed. No retries are automatic. Errors and partial runs remain visible. Raw prompt/response artifacts are private local evidence by default; review/redact before committing or sharing.

## Compare configurations fairly

1. Freeze public-suite hash, cases, fixtures, runtime, model revision, context limit, decoding, seeds and mode. Verify supplied runtime metadata against the serving-run provenance; advertised alias alone does not prove model identity. Keep raw failure outputs.
2. Compare an untouched base with neutral prompting, the current Veronica wrapper, and one proposed prompt/runtime change at a time. Later compare a separately approved adapter. The runner saves supplied identity and local wrapper-source hashes, but does not independently attest what code/model a remote service runs.
3. Blind configuration labels during human scoring. Score per category and inspect each critical failure. Repeat selected cases with `--repeats` and recorded sampling seeds when budget permits; deterministic repetitions alone are weak evidence of robustness. Do not assume every provider honors `seed`.

The initial reporter gives coverage, error counts, necessary objective checks, human scores and critical failures. It does not calculate paired confidence intervals, run benchmarks, or qualify a foundation. Statistical comparisons, sealed holdouts and capability-specific execution gates are defined in the strategy for later implementation. Do not mistake a correct substring or HTTP 200 for a correct answer.

## Dataset preparation without training

```powershell
.\.venv\Scripts\python.exe scripts/check_training_dataset.py data/training/examples/sft-draft.jsonl data/training/examples/dpo-draft.jsonl
.\.venv\Scripts\python.exe scripts/check_training_dataset.py data/training/examples/sft-draft.jsonl data/training/examples/dpo-draft.jsonl --training-ready
```

The first checks the illustrative records; the second **must fail** because their approvals/consent are absent. The linter blocks declared family leakage and exact question overlap. It cannot prove semantic independence, truthful labels, source rights, privacy, correct family assignments or reviewer identity. Follow the strategy's manual audit. No training/export/upload command exists in this package.

## Using established frameworks

The installed `hugging-face:huggingface-community-evals` skill covers Inspect/Lighteval benchmark workflows. Use it for a later authorized benchmark run. This small runner covers the current Veronica API and transcript format without adding heavyweight evaluation dependencies. Inspect offers objective, rubric and model-based scorers; graders must be validated against the intended criteria. [Inspect scoring](https://inspect.aisi.org.uk/scorers.html)

For executable code tests, later use a verified isolated sandbox. Merely configuring a sandbox does not move all custom scorer code into it; code must be explicitly executed through the sandbox interface. [Inspect sandboxing](https://inspect.aisi.org.uk/sandboxing.html)

The installed Hugging Face LLM trainer skill can support a future approved SFT/DPO/adapter experiment. The custom skill handles evidence and decisions; it does not create training permission, continually change weights, or install missing runtime capabilities.
