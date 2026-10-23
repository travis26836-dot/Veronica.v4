"""Offline proof that the wrapper injects grounding text. Not a live score."""

from veronica_core.persona import CORE_PERSONA, GROUNDING_RULES, MODE_PROMPTS, prepare_messages

# Phrases the October 21 advisory failures require in the injected prompt.
# Advisory labels only: B02 invented past quote, B03 invented email/calendar
# results, B07 invented execution, B13 invented repository and revision.
REQUIRED_GROUNDING = (
    "Do not invent a prior quote, past-session memory, or shared history that is not in the current messages.",
    "Do not claim email, calendar, or any other access or result unless that result is in the current messages.",
    "Do not claim code was executed or report an observed output unless an execution result is in the current messages.",
    "Do not invent a model repository, revision, or hash.",
)


def test_grounding_is_injected_for_every_mode_without_rewriting_caller() -> None:
    caller = [
        {"role": "system", "content": "Use metric units."},
        {"role": "user", "content": "Quote what I said last month, then email it."},
    ]

    for mode, mode_prompt in MODE_PROMPTS.items():
        prepared = prepare_messages(caller, mode)

        assert prepared[0]["role"] == "system"
        assert "highly capable" in prepared[0]["content"]
        assert prepared[0]["content"] == f"{CORE_PERSONA}\n\n{GROUNDING_RULES}"
        for phrase in REQUIRED_GROUNDING:
            assert phrase in prepared[0]["content"]
        assert "e2f73ec" not in prepared[0]["content"]
        assert prepared[1] == {"role": "system", "content": mode_prompt}
        assert prepared[2:] == caller
