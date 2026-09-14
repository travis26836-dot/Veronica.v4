# Donor feature inventory — prior Veronica build ("v3")

## Donor identification

There is no folder literally named `v3`. Two prior local builds exist, and the
naming is inconsistent across them:

- **`C:\Users\raine\Veronica-AI`** (repo remote path `/home/dubs/code/veronica-ai-v2`,
  WSL canonical location) — the most mature build, already used once as the UI
  donor for v4 (`runs/2026-08-30-ui-layout-port/decision.md`). This is the
  build referenced below as **the donor**; it is the closest thing to "v3" —
  agentic tool use, approval gating, memory, evals, Image Studio, Design
  Studio spec — built on top of the earlier `veronica-ai-v2` skeleton.
- **`C:\Users\raine\veronica-ai-v2`** — an earlier, thinner scaffold (agent/,
  tools/, models/, backend/, frontend/ stubs, 3 commits). Superseded by the
  build above; not reused here except as historical context.

Everything below is inventoried from `C:\Users\raine\Veronica-AI` (read-only,
untouched — no files were modified there). Re-inspected 2026-09-14 via direct
code review of `server.py` (4833 LOC), `evals/`, `tests/`, JS UI shells
(`app.js`, `workstation.js`, `src/main.js`), `index.html`, and supporting
modules for complete feature salvage list. Donor remains read-only per AGENTS.md
and project rules. Additional details added from endpoint handlers, function
definitions, and module structure.

## Already ported into v4

- Celestial background, Veronica mark/icon assets, Cinzel/Rajdhani/JetBrains
  Mono typography, three-column desktop layout, responsive single-column
  behavior (`runs/2026-08-30-ui-layout-port/decision.md`).
- Basic chat wrapper, OpenAI-compatible alias, persona/mode injection,
  health/capabilities endpoints, streaming relay (v4 core; see current
  `src/veronica_core/app.py` and latest run `2026-09-13T135326Z-start-veronica`).

## Not yet ported — candidate features

### 1. Chat runtime
- Ollama-backed chat via `veronica-v.2:dolphin3-8b-uncensored` (custom
  Modelfile, `MODELFILE.txt`), with native tool-call template embedded in the
  model (`<tool_call>` JSON schema, ChatML-style `<|im_start|>` framing).
- Fallback `<veronica_tool_call>{...}` block parsing for completion-only
  models when native tool schemas aren't supported.
- OpenAI-compatible local integration API (`/v1/health`, `/v1/models`,
  `/v1/chat/completions`) protected by a salted-scrypt-hashed API key
  (`INTEGRATION.md`); explicitly cannot reach terminal/workspace tools.
- Additional: `/api/chat`, `/api/chat/new`, `/api/backend/status`, `/api/tags`.
- Separate chat vs. agent model config (`VERONICA_OLLAMA_MODEL` vs `VERONICA_AGENT_MODEL`).

### 2. Agentic coding / tool system
- Server-side tools: `console_run_command`, `workspace_list_files`,
  `workspace_read_file`, `workspace_write_file`.
- Risk-tiered approval: low/medium-risk actions in saved projects can
  auto-run; high-risk actions require the exact phrase
  `I AUTHORIZE THIS COMMAND`. Pending approvals + private continuation
  context persist across server restarts.
- Task ledger exposed at `/api/agent/tasks` (request, status, action
  timeline) — deliberately excludes private continuation transcript/staged
  file contents.
- Hard completion gate: a bug-fix/build/refactor/test task cannot be marked
  successful without an executed terminal validation command in its task log
  (a prose-only response is recorded incomplete).
- Bounded agent step budget (`VERONICA_AGENT_MAX_STEPS`, default 12, clamped
  1–24).
- Project/workspace model: `Create Project` (name+location dialog, native
  Windows folder picker via `/api/projects/pick-folder`), `Open Folder`
  existing-project picker, default "Session Workspace" fallback with its own
  approval defaults when no project is selected. All actions confined to the
  active workspace root.
- Agent planning/completion helpers (in server.py): `agent_task_plan`,
  `agent_task_completion_status`, `agent_task_requires_validation`.
- Full agent loop, parser, executor patterns from superseded v2 scaffold
  (agent/loop.py, agent/executor.py, agent/parser.py, agent/planning.py,
  agent/memory.py, agent/actions.py, agent/state.py).

### 3. Memory
- `/api/memory/recent`, `/api/memory/remember`, `/api/memory/teach`,
  `/api/memory/correct` — explicit remember/teach/correct verbs beyond a
  passive log, distinct from v4's "scoped memory" (E4) which is still
  unbuilt.
- v2 scaffold also had `agent/memory.py` for session/project memory.

### 4. Evals
- Built-in eval harness: `veronica-home/evals/{runner.py, cases/, history/}`,
  `/api/evals/recent`, `/api/evals/progress`, `/api/evals/run`,
  `/api/evals/apply-learning` — i.e. evals that can feed learning back into
  the assistant, not just report pass/fail.
- Tests: `tests/test_eval_runner.py`.
- v4 has separate evals/ under docs and runs, but donor's is integrated with
  apply-learning loop.

### 5. Image generation (Image Studio)
- Automatic1111 (default) and ComfyUI backend support, opt-in only (never
  autostarts with the main server, to conserve GPU memory).
- `/api/image/{status,history,check,resources,progress,set-model,generate}`,
  launcher status/feed/start endpoints, live auto-scrolling "Check Backend"
  trace (endpoint resolution → API handshake → active selection → resource
  discovery), separate checkpoint vs. LoRA selects.
- Named LoRA presets with baked-in generation defaults, e.g. selecting
  `krea2_nud3` sets Euler/Beta/10 steps/weight 0.7; a dedicated "Realism
  slider" LoRA (`PornMaster_Krea2_Realism_slider_V1`) exposes a custom -15..+10
  UI range (negative = illustrated/anime, 0 = semi-realistic baseline,
  positive = photoreal) with its own sampler/scheduler/CFG/step defaults.
  UI must warn when no compatible base checkpoint is installed rather than
  imply the LoRA alone can generate.
- Full endpoints confirmed: `/api/image/check`, `/api/image/resources`,
  `/api/image/progress`, `/api/image/set-model`, `/api/image/launcher/start`,
  `/api/image/launcher/feed`, `/api/image/launcher/status`, `/api/image/history`,
  `/api/image/generate`, `/api/image/status`.
- Tests: `tests/test_image_resources.py`.

### 6. Design Studio (spec only, not fully built in donor — `DESIGN_STUDIO_TODO.md`)
A full 8-milestone plan for a generative UI/asset design tool bolted onto
Veronica chat:
1. Product decisions: v1 scope boundaries, reference prompt set, preset
   registry.
2. Design-document data contract: document shape, element types, validation
   rules, persistence/history, foundation tests.
3. Backend design APIs + mutation command contract.
4. Design Studio frontend: navigation/new-design screen, editor shell,
   core editing interactions.
5. Manual elements (native shapes/text/etc.) and an asset data model.
6. Chat/tool-loop integration: separates normal chat from design-control
   intent, adds model-callable design tools, adds a focused system context
   for Design Studio mode.
7. Generated editor elements: prompt compiler, image-gen API integration,
   placement defaults, image quality/failure checks.
8. Exports, template reuse, end-to-end eval suite, manual acceptance
   checklist, observability.
This is a spec, not shipped code — useful as a design reference if v4 ever
builds a Studio module (v4 TODO's E5 already lists "Build the Studio Director"
as pending). See also `design-qa.md` and `DESIGN_STUDIO_TODO.md` in donor.

### 7. Terminal/diagnostics surface
- `/api/terminal/status`, `/api/terminal/history`, `/api/terminal/assess`,
  `/api/terminal/run` — a separate assess-then-run flow (risk assessment
  before execution) distinct from the general agent tool loop.
- Helpers: `assess_terminal_command`, `validate_terminal_approval`,
  `execute_terminal_command`, `terminal_shell_argv`, `truncate_terminal_text`.

### 8. Settings / session / config surface
- `/api/settings`, `/api/settings/approval-default`, `/api/session`,
  `/api/config`, `/api/workstation/status`, `/api/workstation/events`
  (SSE-style event stream for live workstation activity, explicitly
  evidence-based — no simulated tool/model events, matching v4's own honesty
  rule already in `docs/SUBDEVELOPMENT-FIRST-CONVERSATION.md`).
- Projects: `/api/projects`, `/api/projects/create`, `/api/projects/select`,
  `/api/projects/pick-folder`, `/api/projects/list-dir`, `/api/projects/approval-mode`.
- Additional: project storage validation, approval modes per project,
  `clean_project_name`, `default_project_storage_location`, `protected_project_roots`.

### 9. Additional wired features from full inspection
- **Workstation / UI surfaces**: `workstation.js`, `app.js` (legacy?), full
  index.html with multi-panel support (chat + activity + image controls?).
  Evidence-based UI (polls health, shows real state).
- **v2 scaffold specifics** (earlier wiring): Agent core with planning/loop/
  executor/parser/state/platforms; tool system (`tools/`); multi-model
  inference (`models/`); FastAPI backend routes (`backend/routes/agent.py`,
  `models.py`); frontend shell; optional SD runtime.
- **State / persistence**: Projects, approvals, memory, evals history,
  image history, terminal history, session state survive restarts.
- **Health / startup patterns**: Detailed preflight, backend status,
  launcher traces.
- **Integration points**: Separate OpenAI-compatible integration path that
  deliberately excludes privileged tools.
- **Tests**: `test_integration_api.py`, `test_eval_runner.py`,
  `test_image_resources.py` — integration and resource tests present.
- **Operational**: Detached launch scripts, WSL/Windows path helpers,
  env config for all backends (Ollama, image APIs, ports, models).

### 10. Operational conventions worth reusing (not code, but process)
- Detached background server launch pattern (nohup + pid file under
  `logs/`) so the process survives the launching shell/agent turn ending —
  directly relevant to `.agents/skills/veronica-runpod-core` and
  `scripts/start-veronica.ps1`.
- "Search for and reuse local models/runtimes/wheels before large downloads"
  — stated as a standing rule due to unreliable ISP; same constraint likely
  applies to the RunPod workflow.
- Health-check-before-use pattern: `/api/health` then
  `/api/backend/status` reporting `reachable` + exact model id before
  declaring the UI usable.
- UI-first launch (show UI early, verify inference in background) — already
  used in v4 latest launcher per `2026-09-13T135326Z-start-veronica/decision.md`.

## Explicitly NOT recommended to port as-is
- The `MODELFILE.txt` system prompt ("You are a completely uncensored AI...
  nothing is off limits") is a blanket jailbreak system prompt, not a
  persona/alias design — conflicts with v4's alias/persona-wrapper approach
  (AGENTS.md rule 3) and should not be copied verbatim; if the underlying
  tool-call ChatML template is reused, strip this system prompt and use v4's
  own persona layer instead.
- Donor's Windows/WSL path assumptions (`/home/dubs/code/veronica-ai-v2`,
  `\\wsl.localhost\Ubuntu\...`) are machine-specific and don't apply to v4's
  RunPod-based runtime.
- Legacy UI shells (some duplication between app.js / workstation.js / src/)
  — v4 uses its own simplified static UI in `src/veronica_core/static/`.
- Full Image Studio and agent tool implementations should be ported only
  after core (E1/E2) and scoped tools (E3) are qualified; risk of scope creep.

## Suggested next step
Turn the "not yet ported" sections above into scoped TODO items under v4's
existing E3 (native tools), E4 (scoped memory), and E5 (remaining modules)
sections rather than a bulk import — each needs the same "verify before
marking complete" treatment v4 already requires (AGENTS.md rule 8).

Cross-reference:
- Current v4 TODO.md (E3/E4/E5 pending).
- SOURCE-OF-TRUTH.md (core first, no bulk port without evidence).
- Latest run evidence: `runs/2026-09-13T135326Z-start-veronica/decision.md`
  (basic chat/creative/coding/reasoning smokes verified; tools/memory deferred).
- UI port precedent: only visuals + compatible behaviors were taken; APIs
  left behind until ready.

## Full confirmed API surface (from server.py handlers, 2026-09-14 inspection)
GET:
- /api/health
- /api/backend/status
- /api/image/status
- /api/image/history
- /api/image/launcher/status
- /api/image/launcher/feed
- /api/memory/recent
- /api/evals/recent
- /api/evals/progress
- /api/terminal/status
- /api/terminal/history
- /api/projects
- /api/settings
- /api/session
- /api/agent/tasks
- /api/config
- /api/workstation/status
- /api/workstation/events
- /api/tags (partial)

POST:
- /api/chat
- /api/chat/new
- /api/image/check
- /api/image/resources
- /api/image/progress
- /api/image/set-model
- /api/image/launcher/start
- /api/image/history (also GET)
- /api/image/generate
- /api/memory/remember
- /api/memory/teach
- /api/memory/correct
- /api/evals/run
- /api/evals/apply-learning
- /api/terminal/assess
- /api/terminal/run
- /api/projects/create
- /api/projects/select
- /api/projects/pick-folder
- /api/projects/list-dir
- /api/projects/approval-mode
- /api/settings/approval-default

OpenAI compat (separate path, limited):
- /v1/health, /v1/models, /v1/chat/completions

Also serves static UI, assets; handles OPTIONS, etc.

This list represents substantial prior work that can be selectively salvaged
once v4 core is solid (per current E1 milestone progress). Do not port
implementation details without re-implementing against v4 contracts, tests,
and evidence requirements.