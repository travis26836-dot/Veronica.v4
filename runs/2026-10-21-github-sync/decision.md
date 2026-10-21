# Reviewed GitHub publication packet

Owner authorization: after reviewing the proposed exact-path commit, branch push
and PR, the owner said, "Yeah, let's do that."

Scope: Global Storage checked launcher, transport regressions, startup progress
scrolling, reproducible CLI cache prerequisite and a sanitized operational report.
The regional default policy, older tools/app/workflow changes and historical
test-folder anomalies are preserved outside this packet. The milestone branch
is not merged. No approvals, raw conversations, images, private runtime logs,
credential stores or executable artifacts are included.

Validation: `verify_publication.py` exported base commit 3010c0b plus only the nine
listed source/config/test changes into a temporary checkout. Six startup/safety
suites passed with 149 passes and two platform/prerequisite skips, exit 0.
PowerShell and universal CLI offline previews also passed without creating a Pod.
`validation.json` records the base, exact overlays, suites, counts and exit code.

The first verification attempt used an inaccessible system pytest temp folder
and omitted the unchanged GitHub workflow from the archive. Its failed output is
retained locally in initial-clean-tests.xml and initial-validation.json. The
runner now uses its own temporary directory and includes the workflow. This was
a validation-runner correction, not a product test suppression.

The local verified CLI was copied, not moved, from the migration evidence to
ignored `.cache/runpod/runpodctl.exe`. The profile and bridge now enforce that
cache boundary and the same pinned SHA-256. Regressions reject a missing,
tampered or out-of-cache artifact. Setup instructions identify the official
pinned release and checksum; no binary or credential is published.

Live status: the migration and two live Pods are confirmed absent. Both volumes
remain. Actual model hashes and generated inference were verified; browser
quality is HOLD (5/13 met target; four critical failures). Whole-volume checksum
equality, connection reliability and eager-loading speed remain unverified.

Next: review the PR and its limits; prepare offline grounding fixes. Any future
paid session needs a fresh bounded owner request. This publication grants no
training, deployment, merge or further paid-run authorization.
