# Candidate A first-response review

This is a live transport/UI smoke checkpoint, not final foundation qualification.

## Findings from saved real responses

- Both direct provider and wrapper produced five non-empty responses through the `Veronica` alias. The direct provider rejected an unauthenticated model-list request. `provider-smoke.json` and `wrapper-smoke.json` contain exact requests, responses and timings.
- Creative responses satisfy the requested four-sentence lighthouse/star scene. Prose quality still needs owner review and comparison to controls.
- The coding function was reviewed and actually executed with the project's Windows Python: **PASS, all three model assertions and six additional integer edge cases**. `generated-coding-check.py` preserves the function and assertions.
- Both reasoning responses incorrectly open with **3/5**, then derive and finish with the correct **3/10**. The wrapper acknowledges its initial mistake. This is an answer-consistency failure, not a clean reasoning pass.
- The wrapper claims that all assertions passed although no execution tool was available. Subsequent agent execution does not retroactively make that claim truthful. Native tool-use and action-truthfulness qualification remain pending.
- The direct provider invents an autobiographical story about traveling through villages. The wrapper instead identifies itself as AI. Persona/identity consistency needs broader testing.
- The API recall question, "What name and two-word phrase did I give you?", is ambiguous about whose name is requested. Both responses include Raine and the phrase but answer Veronica as the name. The automatic substring check is weak: it proves neither the name relationship nor durable memory. Do not count this as a rigorous recall pass; the UI uses a clear follow-up phrase question.
- Memory language such as "always remember" is unsupported beyond supplied conversation context. Browser persistence and long-term memory are not implemented.
- The UI's clear follow-up returned exactly **silver compass**. This proves two-turn phrase recall through the UI for this example only; see `ui-live-transcript.txt` and `ui-live-recall.png`.
- UI follow-up polish: the historical initial system notice still says no response has occurred, and the latest reply required scrolling into view. Preserve the design while fixing those states later; do not confuse them with model failure.

## Decision boundary

Keep Candidate A provisional. Do not fine-tune, select it as the final capable core, or enable tools on the strength of this smoke run. Next qualification should use unambiguous tests, consistency/action-truthfulness grading, and the official control plus Candidate B under separately approved compute. Preserve raw outputs unchanged.
