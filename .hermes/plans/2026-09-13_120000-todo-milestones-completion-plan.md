# Veronica.v4 TODO and Milestones Completion Plan

> **For Hermes:** Use subagent-driven-development skill (or direct careful work) to implement this plan task-by-task. Enforce TDD (test-driven-development skill) for any code changes, systematic-debugging for any issues, and kanban tools for tracking checkpoints. Follow veronica-runpod-core skill and AGENTS.md strictly for any RunPod starts (fresh auth, duration question, UI-first, supervised, evidence). Never claim qualification without full evidence. Read full TODO.md, docs/SOURCE-OF-TRUTH.md, latest runs/*/decision.md, and this plan before each phase.

**Goal:** Finish all items in TODO.md with verifiable evidence (real inference where required, not mocks), complete the major milestones (e.g., "Mind Proven"/T2, "Veronica Speaks"/E1 full, "Trail Marked"/E commit, etc.), and advance to a qualified basic capable core (text/chat + modes + reasoning/writing/coding baseline) before specialized modules. Utilize all available tools (reads, terminal read-only where possible, kanban, code inspection, etc.). Create and execute against reasonable, bite-sized checkpoints via kanban and this plan.

**Current Context / Assumptions (as of 2026-09-13 post latest run):**
- Latest verified run: `runs/2026-09-13T135326Z-start-veronica/` (A100 cold start, UI-first via startup-ui-ready.json, full model manifest with shas + VERIFIED logs, wrapper/provider smokes with context recall/"copper lantern", creative, coding is_even+asserts, reasoning self-correction 3/5→3/10, clean termination, volume retained). See its new decision.md.
- Single-model reality: Only Candidate A (`huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` @ e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f) wired. Candidate B and controls not integrated (per 2026-09-09 decision).
- Core implemented (per code + capabilities + tests): Veronica alias, persona (sharp/sarcastic with TRAVIS, mode presets), OpenAI-compat wrapper (health, models, non/stream chat with injection/rewrite), basic UI (mode select, chat, health polling, activity; textContent, no persistence/MD/controls yet), streaming backend.
- Tests: 100% pass on mocks (`uv run pytest tests/ -q`); known Starlette/httpx deprecation warning.
- TODO progress: Many [x] (capture, basic assemble, first chat, some R items now marked with this run's evidence: manifest, transfers, launcher UI verify, deep-reasoning smoke). Still open: full T2 (eval pack live execution + human review), Candidate B, advanced UI, commits, native tools/memory, E2+ stages, full qualification gates.
- Eval system ready offline (docs/evals/README.md, QUESTION-BANK.md 60 cases/69 turns/12 cats, SCORING.md 0-4 + critical_failure, scripts/evaluate_veronica.py + veronica_core/evaluation.py, config/t2-qualification.json frozen protocol for 4 models + tracks, required evidence incl. executable code/human review).
- Constraints: No unauthorized paid Pods (fresh auth + duration question per skill/AGENTS; default 1hr A100 $1.75 cap; UI open ASAP; supervised; evidence in runs/). No foundation weight changes yet. No mocks as "real" inference. Follow plan skill for this document; TDD/systematic for changes.
- Kanban checkpoints created: t_481c5c7f (T2 pack, prio5), t_46568e3e (B wiring), t_0b2dabab (A1 UI), t_baab4d98 (baseline commit), t_019b1724 (deprecation fix).
- No .hermes/plans/ dir yet; no active $HERMES_KANBAN_TASK.

**Proposed Approach:**
- Use this plan + kanban for checkpoints (create/update tasks as needed).
- Phase by TODO sections (R → E → A/T → E1+).
- Local/offline-first where possible (mocks, validate scripts, plan evals).
- For live T2: only on explicit fresh "Start Veronica" with duration; run evals as separate workload; open UI early; respect protocol (matched runtime, blind review, etc. – note current vLLM 0.11 vs protocol 0.28 may need alignment).
- Any code: strict TDD (failing test first via terminal, minimal green, refactor, full suite).
- Debugging: full systematic-debugging 4 phases before any fix.
- Evidence: new run dirs + decision.md for every change; update TODO only with proof; preserve all prior runs.
- Checkpoints: small, verifiable, tied to gates (e.g., "offline T2 protocol verified", "first live T2 sample run").
- Tools: batch read-only (read_file, search_files, terminal ls/cat/grep for inspection), kanban_*, write_file (plan + any future), execute_code sparingly, no web unless for external model cards post-auth.
- Validation: pytest, eval scripts (plan/validate/report), manual review of smokes, git status/diff (read-only).

**Tech Stack:** Python 3.12+ (uv), FastAPI/httpx, vLLM on RunPod, pytest, JSON schemas in config/, static HTML/JS UI, existing eval harness.

**Files Likely to Change (high-level, exact in tasks):**
- TODO.md (evidence updates only)
- New/updated runs/*/decision.md
- .hermes/plans/ (this and future)
- Kanban via tools
- src/veronica_core/ (only via TDD if needed)
- docs/evals/, scripts/, config/ (prep only)
- tests/ (new/updated per TDD)

**Tests / Validation:** Always run `uv run pytest tests/ -q --tb=no` after changes. Use evaluate_veronica.py plan/validate/report. Human review for evals. Decision.md per run.

**Risks, Tradeoffs, Open Questions:**
- Live T2 requires paid Pod + owner auth (cost ~$1.59/hr; 60 cases ~dozens of calls; keep short window).
- Runtime mismatch (current 0.11 vs t2 json 0.28) – align or update protocol.
- UI simplification vs feature requests – keep core first.
- No Candidate B yet – stabilize A.
- Deprecation warning – fix before upgrades.
- Open: full long-context, executable code sandbox, native tools in evals.

---

## Phase 0: Setup and Orientation (Read-Only, 1 checkpoint)
**Objective:** Establish shared understanding and checkpoints without changes.

**Files:**
- Read (already): TODO.md, docs/SOURCE-OF-TRUTH.md, docs/evals/* (README, QUESTION-BANK, SCORING), config/t2-qualification.json, src/veronica_core/evaluation.py (partial), scripts/, latest run artifacts + decision.md, kanban via tools.
- Create: .hermes/plans/ (this file).

**Step 1: Verify current state (read-only)**
- Run: `kanban_list --limit 10`
- Expected: The 5 tasks listed (T2 highest prio).
- Run: `uv run pytest tests/ -q --tb=no`
- Expected: 100% (with deprecation note).
- Inspect: `ls runs/2026-09-13T135326Z-start-veronica/ | grep -E 'decision|smoke|manifest|startup|termination'`
- Expected: decision.md + evidence files present.

**Step 2: Load and follow skills**
- Use skill_view for plan (done), test-driven-development, systematic-debugging, veronica-runpod-core, hermes-agent etc. as needed.
- For any future code: enforce TDD cycle via terminal (RED fail, GREEN pass, REFACTOR, full suite).

**Verification:** This plan saved; kanban shows tasks; no unauthorized actions.

---

## Phase 1: Complete R - Research (Manifest/Validation already advanced; finish remaining)
**Objective:** Record quants, more test categories in bank, GPU/price/deadline expectations. Gate R pass.

**Files:**
- Modify: TODO.md (add [x] with proofs only after evidence).
- Inspect: config/model-registry.json (if exists), runs/ for prior provenance.
- Prep: data/evals/ for added tests (chat/reasoning/creative/coding/long-context/JSON/tool/adult/ablation per TODO).

**Task 1: Select/record quants + GPU expectations**
**Objective:** Document current (bfloat16, no quant for 80GB A100) + plan for 48GB.
**Files:**
- Create: runs/2026-09-13-quant-gpu-note/decision.md (or append to existing).
- Modify: TODO.md (R section).
**Step 1 (RED if code, but doc):** Write failing "test" as checklist in terminal or temp script.
**Step 2:** Inspect current profile.json from latest run (dtype: bfloat16, max 8192).
**Step 3:** Minimal doc update with evidence.
**Step 4:** Run read-only verify: grep TODO for "quantizations".
**Verification:** `uv run python -c "import json; print(json.load(open('runs/2026-09-13T135326Z-start-veronica/profile.json'))['runtime'])"` shows config; TODO updated.

**Task 2: Extend QUESTION-BANK and evals for missing categories**
**Objective:** Add/confirm chat, reasoning, creative, coding, long-context, factuality, JSON-schema, native tool-call, adult, ablation-regression cases.
**Files:**
- Modify: docs/evals/QUESTION-BANK.md + data/evals/veronica-core-v1.json (if expanding).
- Test: scripts/evaluate_veronica.py validate --tier extended.
**Step 1:** Read full bank + t2 json tracks.
**Step 2:** Use TDD if adding code: write test for new case parser first.
**Step 3:** Minimal additions per TODO list.
**Step 4:** `uv run python scripts/evaluate_veronica.py validate --tier core`
**Verification:** Bank covers all listed; no new inference.

**Task 3: Record expected RunPod GPU/price/deadline**
**Objective:** Formalize in profile + docs (A100 80GB, <=$1.75/hr, 1hr default, supervised).
**Files:** config/runpod-core.json, docs/STARTING-PROCEDURE.md (read-only inspect), TODO.
**Steps:** Read-only + doc update with proof from preflight/latest.
**Verification:** Matches skill + preflight.json.

**Gate R checkpoint:** kanban task or new "R complete" card. Update TODO ACK if all [x].

---

## Phase 2: E - Contracts + A1/A2 - Assemble/Wrapper + Model Server
**Objective:** Commit baseline (E), verify launcher/UI (A2 done in latest), add deferred A1 UI, confirm native controls post-T2.

**Files:**
- .hermes/plans/ (future)
- src/veronica_core/static/ (index.html, app.js, styles.css for UI features)
- src/veronica_core/app.py, persona.py, provider.py (TDD only)
- scripts/start-veronica.ps1, runpod_core.py etc. (inspect)
- tests/ (new UI or integration per TDD)

**Task 1: Owner baseline commit prep (E)**
**Objective:** Snapshot current state (post this plan + latest decision).
**Files:** TODO.md, docs/SOURCE-OF-TRUTH.md (read), git (read-only status/log/diff).
**Steps (no actual commit here):**
1. Read full current TODO/SOURCE.
2. Plan exact commit message/files.
3. Verification: `git status --short | head -20` (read-only).
**Use kanban:** Update t_baab4d98 or complete when owner does.

**Task 2: Implement deferred A1 UI features (TDD)**
**Objective:** Add localStorage persistence, Markdown rendering (safe), retry/stop/copy/regenerate, token usage, etc. (per TODO A1 + capabilities note).
**Files:**
- Create/Modify: src/veronica_core/static/app.js (add persistence), index.html (MD divs?), new tests/test_ui.py or extend test_app.
**TDD Cycle (per skill):**
- RED: `uv run pytest tests/test_ui_persistence.py::test_localstorage -v` (expect fail, no storage yet).
- GREEN: Minimal JS localStorage for messages + re-render on load.
- Run full: `uv run pytest tests/ -q`
- REFACTOR: Clean, keep textContent fallback if needed.
- Repeat for Markdown (use marked or simple parser? inspect deps first read-only), controls (buttons in composer).
**Verification:** Manual via `uv run uvicorn src.veronica_core.app:create_app --factory` (if local mock) or TestClient; browser if available. Update capabilities response.
**Risk:** Don't block core; keep simple.

**Task 3: Confirm native reasoning/tool parser (A2, post T2)**
**Objective:** After model qual, test --enable-auto-tool-choice etc. per t2 json.
**Files:** profile.json updates, app/provider for parsing.
**Steps:** Only after T2; use systematic-debugging if issues; TDD for parser.
**Verification:** Live smoke with tool fixtures (no exec).

**Gate A1/A2/E checkpoint:** Update kanban, mark in TODO with new decision.md.

---

## Phase 3: T1/T2 - Test (Core + Foundation Qual)
**Objective:** Local T1 complete (deprecation), full T2 live (Mind Proven).

**Files:**
- tests/ (deprecation fix + new eval tests)
- scripts/verify_t2_qualification.py, evaluate_veronica.py
- runs/ for new eval runs
- data/evals/ (fixtures)

**Task 1: Resolve deprecation (T1)**
**Objective:** Fix Starlette/httpx warning before upgrades.
**Files:** tests/test_app.py (TestClient usage), pyproject.toml dev deps.
**TDD:**
- RED: Run pytest, capture warning as fail in test (or use pytest filter).
- GREEN: Minimal change (e.g., import from starlette or pin/upgrade carefully).
- Full suite pass, no warning.
**Verification:** `uv run pytest tests/test_app.py -q -r w` (warnings).

**Task 2: Offline T2 protocol verification**
**Objective:** Run frozen checks without Pod.
**Steps:**
1. `uv run python scripts/verify_t2_qualification.py protocol`
2. Plan specific cases from t2 json (e.g., neutral-deterministic all, sampled subset).
3. Use evaluate_veronica.py plan --tier extended.
**Verification:** No errors; matches config.

**Task 3: Live T2 execution (highest prio kanban t_481c5c7f)**
**Objective:** Run on fresh authorized Pod (explicit user "Start Veronica" + duration answer required).
**Approach (follow skills/AGENTS exactly):**
- Do NOT start here. Wait for user request.
- When authorized: Use start-veronica.ps1 or Python controller; open UI at 8010 ASAP; run evals separately via script with --execute --base-url http://127.0.0.1:8010/v1 --surface wrapper --runtime-record <latest profile> --run-dir new-eval-run --max-seconds 600 etc.
- Per t2: matched runtime (align vLLM if needed), seeds, modes, repeats, direct surface for neutral.
- Collect: raw responses, objective checks (use t2-executable-fixtures), human reviews (0-4 + critical_failure), manifests.
- For executable code: isolated sandbox (later).
- Update: new decision.md with results, TODO [x] only with proof.
- Compare vs controls.
**Steps (when authorized):**
1. Confirm Pod via preflight.
2. Run bounded eval (smoke first, then core).
3. Import results, human review (owner or adjudicate).
4. `uv run python scripts/verify_t2_qualification.py compare --inputs ...`
5. Decision: selected/hold.
**Verification:** All requiredEvidence present; gate passed or hold documented. No claims without.

**Task 4: Add missing eval coverage (JSON, tools, long-context, etc.)**
**Objective:** Extend for T2 requirements.
**TDD where code added.**
**Verification:** Full pack runs cleanly offline.

**Gate T2 checkpoint:** "Mind Proven" ACK only after signed decision + evidence. Update kanban.

---

## Phase 4: E1+ - Execute Core + Later Modules
**Objective:** Full E1 (commit + capable core), then E2 (persona), E3 (tools), E4 (memory), E5 (modules), D (release).

**Files:** As needed per TDD; new modules behind API alias only.

**Task 1: E1 commit + full smoke/qualification**
**Objective:** After T2 pass, commit verified state.
**Use kanban t_baab4d98.**
**Verification:** Owner ack; another session can resume from docs/runs.

**Subsequent:** Follow strategy in docs/evals/DATASET-AND-FINETUNING-STRATEGY.md only post-regression. Add native tools (E3) with permissions/audit (TDD). Scoped memory (E4). Modules via stable alias (E5).

**Gate E1+:** "Veronica Speaks" full, "Voice Recognized", "Hands Online", etc.

---

## Phase 5: D - Document/Package/Release + Ongoing Checkpoints
**Objective:** Reproducible, with auth/quota/cost, security review.

**Checkpoints:** Pin versions, container, inventories, Serverless test (scale-to-zero), legal review, owner release approval.

**Ongoing:** Use kanban for new cards (e.g., "Add long-context stress"), plan skill for sub-features, TDD always.

**Risk Mitigation:** Bounded Pods only; offline prep max; evidence immutable; no over-claim.

**Final Verification for Goal Complete:**
- All TODO [x] with proofs in runs/decision.md.
- T2 signed decision + human reviews.
- Core passes full rubric (score >=3, 0 critical failures).
- Kanban tasks complete or closed.
- Baseline committed.
- "Mind Proven", "Seven Facets Lit" etc. ACKed with evidence.
- Plan says: Goal complete only when above + user confirms.

**Next Immediate Action After This Plan:** 
1. Owner reviews this plan + latest decision.md.
2. Address highest kanban (T2 prep offline).
3. If ready for live: explicit start request with duration.
4. Dispatch via subagent-driven-development for specific tasks if complex.

This plan makes next steps obvious and bite-sized. Saved to .hermes/plans/2026-09-13_120000-todo-milestones-completion-plan.md. Ready for execution or refinement. No code changed in this planning turn.