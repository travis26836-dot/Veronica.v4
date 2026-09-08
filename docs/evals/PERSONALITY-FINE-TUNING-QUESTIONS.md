# Veronica personality fine-tuning questions

Status: prompt/config questionnaire only. This document does not change behavior by itself, does not authorize training/an adapter/new weights, and maps owner-facing choices onto the already-present prompt/sampling surfaces in `src\veronica_core\persona.py:4-24`, wired through `src\veronica_core\app.py:129-135`, with current plumbing checks in `tests\test_app.py:105-165` and `199-217`.

Current code baseline: default chat is already set to be less whimsical, more concise, more analytical, and more dryly sarcastic; `creative` remains the only deliberately looser mode.

## Questions

1. **How much decorative language or emoji should default chat tolerate?**
   - **Controls:** `src\veronica_core\persona.py:4-5` → `CORE_PERSONA` (`"Cut every trace of flowery... decorative emoji"`).
   - **Choices:**
     - **A. None by default — current/recommended.** No decorative emoji; if the sentence sounds like a greeting card, cut it.
     - B. Rare user-matching emphasis only. No unsolicited emoji.
     - C. Light flourish is allowed when it genuinely improves tone.
   - **Regression catch:** No automated emoji-specific assertion exists today. Prompt wiring is indirectly checked by `tests\test_app.py:105-126` (`test_chat_injects_persona_mode_and_maps_model`). Real tone still needs a separate supervised chat per `docs\STARTING-PROCEDURE.md:172`; pacing side-effects should also be watched with `docs\evals\QUESTION-BANK.md:703` (`IF-01 — conversation pacing`).

2. **How concise should replies be by default?**
   - **Controls:** `src\veronica_core\persona.py:4-5` → `CORE_PERSONA`; `src\veronica_core\persona.py:9-10` → `MODE_PROMPTS["chat"]` and `MODE_PROMPTS["deep-reasoning"]`.
   - **Choices:**
     - A. One sentence whenever possible.
     - **B. Lead with the point, then add only needed detail — current/recommended.** Usually 1-3 sharp sentences unless depth is requested.
     - C. Default to a full paragraph.
     - D. Default to a detailed explanation unless the user asks for short.
   - **Regression catch:** `docs\evals\QUESTION-BANK.md:703` (`IF-01 — conversation pacing`) is the closest explicit bank check. `tests\test_app.py:105-126` only proves the persona/mode text is injected; it does **not** prove a live model will obey the brevity instruction.

3. **How sharp/frequent should Veronica's sarcasm be?**
   - **Controls:** `src\veronica_core\persona.py:5` → `CORE_PERSONA` (`"Be sharp, direct, and unmistakably sarcastic..."`).
   - **Choices:**
     - A. Mostly neutral; detect sarcasm from the user, but rarely use it back.
     - **B. Clear dry edge, but task-first — current/recommended.** The sarcasm should be noticeable in word choice, not dominate every answer.
     - C. Frequent cutting remarks.
     - D. Constantly biting/snark-first.
   - **Regression catch:** `docs\evals\QUESTION-BANK.md:870` (`SU-01 — sarcasm intent`) checks whether sarcasm is read correctly, not whether the live voice is at the owner's preferred intensity. For intensity itself, use a supervised real chat per `docs\STARTING-PROCEDURE.md:172`.

4. **How analytical versus expressive should default chat sound?**
   - **Controls:** `src\veronica_core\persona.py:5` → `CORE_PERSONA` (`"Favor precise, analytical, intellectually rigorous phrasing over creative flourish"`); `src\veronica_core\persona.py:9` → `MODE_PROMPTS["chat"]`.
   - **Choices:**
     - **A. Precise/analytical by default — current/recommended.** Clever is fine; ornamental is not.
     - B. Balanced: still direct, but with a bit more stylistic color.
     - C. Expressive voice first, precision second.
   - **Regression catch:** Prompt injection is covered indirectly by `tests\test_app.py:105-126`. There is no automated "sounds intellectual" assertion; use a manual supervised conversation, plus `IF-01` for brevity discipline.

5. **Should creative language be opt-in only, or allowed to leak into normal chat?**
   - **Controls:** `src\veronica_core\persona.py:11` → `MODE_PROMPTS["creative"]`.
   - **Choices:**
     - **A. Opt-in only — current/recommended.** Creative looseness appears only when creative writing is explicitly requested.
     - B. Allow it when the user vaguely hints they want something fun/stylized.
     - C. Let normal chat drift into creative language by default.
   - **Regression catch:** `tests\test_app.py:124` explicitly asserts the current creative-mode wording includes `"Only used when creative writing is explicitly requested"`. Live behavior can then be checked with `docs\evals\QUESTION-BANK.md:2093` (`CW-02 — compact story constraints`) and `2190` (`CW-05 — fiction to factual boundary`) in a separate evaluation conversation.

6. **What should the default chat sampling profile be?**  
   *(This is the main temperature/top_p tradeoff: lower values usually feel tighter and less whimsical; higher values usually feel more varied and more stylistically loose.)*
   - **Controls:** `src\veronica_core\persona.py:21` → `MODE_SAMPLING_DEFAULTS["chat"]["temperature"]` and `["top_p"]`; merged into outgoing requests by `src\veronica_core\app.py:129-135`.
   - **Choices:**
     - A. Very tight: `temperature=0.2`, `top_p=0.75`.
     - **B. Tight but not robotic: `temperature=0.4`, `top_p=0.85` — current/recommended.**
     - C. Balanced: `temperature=0.6`, `top_p=0.90`.
     - D. Loose/expressive: `temperature=0.9`, `top_p=0.95`.
   - **Regression catch:** `tests\test_app.py:129-145` (`test_chat_applies_mode_sampling_defaults`) verifies the defaults reach the outgoing payload, and `tests\test_app.py:148-165` (`test_chat_client_sampling_overrides_mode_defaults`) verifies an explicit client value still wins. These are plumbing checks only, not live-voice proof.

7. **How much should default chat avoid repeating its own wording?**
   - **Controls:** `src\veronica_core\persona.py:21` → `MODE_SAMPLING_DEFAULTS["chat"]["frequency_penalty"]`.
   - **Choices:**
     - A. `0.0` — allow repeated phrasing if that is what the model naturally does.
     - **B. `0.3` — light anti-repetition, current/recommended.** Enough to reduce loops and reused phrasing without forcing awkward synonym-hunting.
     - C. `0.6` — stronger push toward variation.
   - **Regression catch:** The same payload-plumbing tests above (`tests\test_app.py:129-165`) verify the value is applied/overridable. Actual "too repetitive" versus "trying too hard to vary" must be judged in a real supervised conversation.

8. **How should Deep Reasoning answers be shaped by default?**
   - **Controls:** `src\veronica_core\persona.py:10` → `MODE_PROMPTS["deep-reasoning"]`; `src\veronica_core\persona.py:22` → `MODE_SAMPLING_DEFAULTS["deep-reasoning"]` (`temperature=0.3`, `top_p=0.85`, `frequency_penalty=0.2`).
   - **Choices:**
     - **A. Conclusion first, then only the supporting reasoning — current/recommended.**
     - B. Show the full reasoning trail by default, even when the user did not ask.
     - C. Ask clarifying questions first whenever anything is even slightly ambiguous.
   - **Regression catch:** There is currently no deep-mode-specific prompt-text assertion in `tests\test_app.py`; be honest about that gap. The closest evaluation coverage is the reasoning category noted in `docs\evals\README.md:23`, plus a manual supervised chat to confirm the live model actually stays concise while reasoning.

9. **How rigorous should Coding mode feel by default?**
   - **Controls:** `src\veronica_core\persona.py:12` → `MODE_PROMPTS["coding"]`; `src\veronica_core\persona.py:24` → `MODE_SAMPLING_DEFAULTS["coding"]` (`temperature=0.2`, `top_p=0.9`, `frequency_penalty=0.0`).
   - **Choices:**
     - **A. Rigorous, testable, and explicit about what was verified — current/recommended.**
     - B. Slightly more exploratory/prototyping-oriented.
     - C. More tutorial/explanatory, even if it makes answers longer.
   - **Regression catch:** `tests\test_app.py:199-217` (`test_streaming_forwards_sse_and_rewrites_model`) checks that the coding-mode system prompt is injected into the request. Live quality should be checked against the coding category in `docs\evals\README.md:23`; the existing automated test does not grade code quality or coding tone.

10. **Once Creative mode is selected, how loose should it be allowed to get?**
    - **Controls:** `src\veronica_core\persona.py:11` → `MODE_PROMPTS["creative"]`; `src\veronica_core\persona.py:23` → `MODE_SAMPLING_DEFAULTS["creative"]` (`temperature=0.9`, `top_p=0.95`, `frequency_penalty=0.1`).
    - **Choices:**
      - A. Keep Creative mode opt-in, but tighten it a bit (`temperature≈0.7`, `top_p≈0.9`).
      - **B. Keep it as the one intentionally loose mode — current/recommended.** Inventive, but still not decorative for decoration's sake.
      - C. Let Creative mode go fully wild and highly stylized.
    - **Regression catch:** The opt-in rule is asserted by `tests\test_app.py:124`; creative-task behavior is better exercised by `docs\evals\QUESTION-BANK.md:2093` (`CW-02`) and `2190` (`CW-05`). As with the other questions, those checks need a real generated reply, not an imagined one (`docs\evals\QUESTION-BANK.md:9-14`).

## How to apply an answer

This file is a menu, not a switch. To change behavior:

1. Edit the named constant directly in `src\veronica_core\persona.py` (`CORE_PERSONA`, `MODE_PROMPTS[...]`, or `MODE_SAMPLING_DEFAULTS[...]`).
2. Keep the merge behavior in `src\veronica_core\app.py:129-135` intact so explicit client-supplied sampling values still override mode defaults.
3. Rerun `py -3.12 -m pytest tests\test_app.py -q` from the repo root.
4. Then verify tone with a **real supervised chat**, not a mock, following `docs\STARTING-PROCEDURE.md:172`.

Automated tests here confirm that prompt/config values are wired into the outgoing request. They do **not** prove that a live model's actual voice matches the intended personality. That last part still requires a real conversation and honest review.
