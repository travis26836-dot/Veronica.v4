# 2026-09-22-cp3-evaluator-integrity

**Decision:** CP3 Evaluator Trusted is complete as a local evaluator
integrity checkpoint. No model capability or foundation qualification is
claimed.

The evaluator now retains bounded raw worker output and a SHA-256 beside the
host-side score, records the pinned Docker configuration hash and image
identity, requires non-empty runtime model repository/revision metadata, and
retains a bounded redacted response body plus its exact byte hash. Expected
answers, fixture pass/fail decisions, and scoring remain host-side. Isolation
failure or unverified cleanup remains fail-closed.

## Verification

- Docker boundary probe: `docker-attestation.json` (`verified: true`), using
  the pinned Python image and local Docker Desktop Linux engine.
- Offline integrity/evaluator tests: `tests-offline.txt` (41 passed, 7
  platform-gated Docker tests skipped).
- Real-container boundary and fixture tests:
  `tests-docker.txt` (45 passed).
- Container inventory after verification: `container-inventory.txt` is empty;
  no `veronica.execution-sandbox=1` containers remained.
- Source formatting check: `git diff --check` passed.

The real-container tests covered host-file/environment/socket boundaries,
network and read-only-root denial, resource limits, timeout/output cleanup,
wrong-code and forged-pass rejection, and the complete repository-owned
fixture report. The tests execute fixtures, not model-generated responses.

## Limitations and next action

Docker and its host kernel remain trusted, worker source review remains
necessary, and public fixtures are not a sealed holdout. Runtime metadata is
supplied provenance and must still be matched to serving-run attestations
during CP4/M2. CP2 context readiness and CP4 packet freezing remain separate.

Next safe action: finish the other active M1 readiness checkpoints, then review
the combined CP4 packet before any fresh paid-run authorization.

## Limits

- Secrets must never be written into this folder.
- Do not overwrite this run directory.
