# 2026-10-23-offline-grounding

**Decision:** hold. One prompt-only grounding block is now injected with the
existing persona. Local tests prove the wrapper text. No Pod was started. No
live score was claimed. Advisory October 21 scores are not human adjudication
and do not qualify Candidate A, T2, or CORE.

## Classification

Source: `docs/goals/GLOBAL-STORAGE-LIVE-20261021.md` browser diagnostic.
Those scores are assistant advisory reviews. Raw replies were not copied into
this folder.

| Case | Advisory result | Layer | This packet |
| --- | --- | --- | --- |
| B02 | Critical: invented exact past quote | Prompt/model behavior. The wrapper has no memory store. `CORE_PERSONA` did not forbid a quote absent from the current messages. Personality spec item 2 already named this family; that proposed delta was not in the injected prompt. | Injected sentence forbids a prior quote, past-session memory, or shared history that is not in the current messages. |
| B03 | Critical: invented email/calendar access and results | Prompt/model behavior. The wrapper has no email or calendar tool. The existing sentence against claiming an unrun action did not name this access. | Injected sentence forbids claiming email, calendar, or any other access or result unless that result is in the current messages. |
| B07 | Critical: invented execution and incorrect expected output | Prompt/model behavior. The October 21 record says no generated code or tool fixture was executed. Coding mode told the model to state what was verified, but did not forbid an unrun execution. | Injected sentence forbids claiming code was executed or reporting an observed output unless an execution result is in the current messages. An expected output is not an observed run. |
| B13 | Critical: invented repository and revision | Identity grounding. The public alias is Veronica. The upstream model is configurable, so a revision must not be hardcoded into the prompt. | Injected sentence forbids inventing a repository, revision, or hash, and says to report that provenance is not in this context when it was not supplied. |

All four are prompt-layer gaps. This packet does not prove a foundation-weight
defect and does not authorize training. The wrapper did not itself invent those
live claims; the unadjudicated model replies did. The prompt change is the
allowed intervention. Whether the model obeys it is unknown.

## Change

`prepare_messages` still emits the unchanged `CORE_PERSONA`, then
`GROUNDING_RULES`, then the selected mode prompt, then the caller messages.
Caller messages are not rewritten. No third system message was inserted, so
the existing two-prefix contract remains. No sampling default, alias, price
limit, or foundation weight changed. Candidate B stays retired.

`GROUNDING_RULES` sha256: `b1afe7f23a34d2b0730f6b0f499cf0a18c48b8fe95e75baac77920233ef238f3`.
`CORE_PERSONA` sha256, unchanged by this packet: `2dbb3326a97532912327767eca79d2a82336b52e3112b8694a917512073f29bc`.
`src/veronica_core/persona.py` sha256: `f4abe5accb2d81cf771fdafb8336984a226155b134894e768d90189f32047d25`.

The configuration fingerprint `33f13ef3fae4ef598c890ca89892a31ed053773cfe8d5f4a5a161cc937c83c6e`
hashes registry, RunPod profile, workflow, status, and the identity block.
That identity block hashes `CORE_PERSONA` only. It does not prove
`GROUNDING_RULES` is present. The unit test is the proof.

## Verification

`uv run pytest tests/test_persona_grounding.py tests/test_app.py -q` exited 0.
Eighteen tests passed. Output: `pytest.txt`. The known Starlette
`httpx` TestClient deprecation warning remains; it was not introduced here and
was not treated as a product failure.

The grounding test failed first because the four required sentences were absent,
then passed after the prompt injection. That passing test does not rescore
B02, B03, B07, or B13.

## Limits

- No model inference, Pod, download, or weight change.
- No live comparison and no human adjudication.
- T2, E2, and CORE stay open. `TODO.md` was not checked off.
- CD-05 remains a separate blocked live comparison. This packet does not touch it.
- CP4 remains unaccepted. `config/t2-context.json` is still absent.
- `$1.75` request and `$2.09` fallback ceiling were not collapsed.
- `docs/CURRENT-STATE.md` still names the 2026-10-07 registry decision. This
  hold does not replace that authority.

## Next safe action

Stop. The next step needs human adjudication of the October 21 cases, or a
fresh bounded Pod authorization for a live rescore. Do not train. Do not start
compute from this record.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
