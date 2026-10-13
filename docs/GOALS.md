# Veronica goal register

Owner: Travis/Raine. Updated: 2026-09-24. Status is conservative pending evidence audit.
Parent P0: maintain and improve one capable Veronica product indefinitely.
Bounded milestone CORE-1: satisfy SOURCE-OF-TRUTH.md section 11, target 2026-10-23.
CORE-1 is open; the date is a planning target, not a qualification claim.

| ID / goal | Status | Dependencies | Child packets and acceptance | TODO mapping |
| --- | --- | --- | --- | --- |
| G0 Establish trustworthy baseline | ready | none | G0.1 compare main/milestone work and map evidence; G0.2 classify dirty changes and reconcile conflicting launch policy; G0.3 capture complete test exits and review integration. Accept when baseline and exact next packet are reproducible. | E, T1, E1 |
| G1 Trustworthy evaluator and routing | backlog | G0 | G1.1 reproduce/fix extraction and redaction findings (#6/#7; recheck GitHub); G1.2 finish schema, code isolation, context and native-call graders; G1.3 implement score-to-intervention report with invalid/missing evidence holds and human adjudication; G1.4 freeze protocol/holdouts. Accept with positive and negative tests and versioned rubric. | R, T2 prep |
| G2 Qualify owner-selected foundation | backlog | G1 | G2.1 reconcile matched runtime and bounded run packet; G2.2 Candidate A/control runs, precision and latency/cost evidence; G2.3 independent scores, human review and signed T2 qualification/hold. Requires fresh compute authorization. | R, A2, T2 |
| G3 Stable chat and persona | backlog | G2 | G3.1 remaining A1 controls/access/context display; G3.2 prompt persona and blind preference; G3.3 capability regression. Adapter only if justified; document not-applicable training steps if prompt meets gate. | A1, E2 |
| G4 Native tool execution | backlog | G2 | G4.1 schemas/registry; G4.2 permissioned bounded execution loop and audit; G4.3 real tool results, errors, no invented success, chat when disabled. | E3 |
| G5 Scoped memory | backlog | G2 | G5.1 attributed scoped storage/retrieval; G5.2 inspect/correct/export/delete/disable; G5.3 leakage, stale-source and relevance tests. | E4 |
| G6 Application integration | backlog | G3, G4, G5 | G6.1 one external client using Veronica alias; G6.2 assistant/reasoner/writer/agent acceptance. G6.3 Studio Director and G6.4 Application Builder remain separate scoped extension packets, never silently dropped. | E5 |
| G7 Reproducibility and controlled operation | backlog | G2; final acceptance G3-G6 | G7.1 pinned package/container and inventories; G7.2 clean local/Pod recovery; G7.3 auth/quota/cost/telemetry; G7.4 authorized serverless cold start, failures, concurrency and scale-to-zero; G7.5 release review. | D |
| G8 CORE acceptance | backlog | G0-G7 required CORE outcomes | Map every section-11 criterion to current evidence, regression results and recovery proof; owner decision. Public release is separate authorization. | SOURCE-OF-TRUTH section 11 |
| O1 Repository hygiene | recurring | none | Daily classification; weekly reviewed integration queue. Each actual cleanup is a bounded claim. | All stages |
| O2 Continuous model improvement | recurring | G1; training G2 | Capture/adjudicate failures; create independent experiments with dataset rights/splits, comparison and rollback. Each experiment has a terminal decision. | E2, T2 |
| O3 Workflow improvement | recurring | demonstrated repeated need | Weekly identify one friction point; validate manual workflow, then skill/plugin/automation with a measurable time/error benefit. | Workflow |

## Owner priority, updated 2026-10-07 (decision dated 2026-09-29)

Candidate A is owner-selected for operational use; this does not pass T2 or
establish CORE acceptance. Candidate B and its control are retired, so the
remaining qualification comparison is Candidate A against its active official
control only. No additional model shopping or Candidate B download is part of
this goal.

The active packet is **LV1 — single-model live Core verification**, with an
offline CP4 protocol repair required before the T2 packet can be built:

1. review the clean offline integration branch;
2. start the existing Candidate A behind the Veronica alias in one fresh,
   bounded Pod session;
3. verify real chat responses in Chat, Deep Reasoning, Creative, and Coding
   modes and record failures honestly; and
4. use those results to fix the actual Core behavior. Do not re-open retired
   Candidate B comparison work.

LV1 does not pass T2 or complete Veronica Core. Owner selection is distinct
from qualification; the active Candidate A/control evidence and signed T2
adjudication remain open.

No product goal is newly marked complete by this restructuring. Initial history:
the September 13 decision proves chat smoke and shutdown, not full qualification;
September 23 routing handoff documents a proposed contract, not executable routing.
Prior claims that partial pytest output proved a hang or shared-process fault are
unconfirmed hypotheses. G0.3 must preserve session handles and verify final exits.
The default $1.75 instruction conflicts with dirty $2.09 configuration; G0.2 must
resolve scope of historical approvals before paid work. This plan authorizes neither.

## Four-week forecast

- Through Sep 30: G0 and G1; runnable qualification packet and reviewable baseline.
- Oct 1-7: G2 comparison and selection. If it fails, revise forecast and foundation
  decision; do not silently borrow time from acceptance testing.
- Oct 8-14: G3-G5; disjoint packets may parallelize after G2. Prepare G7 packaging.
- Oct 15-23: G6 integration, G7 recovery/staging and G8 acceptance audit.

Weekly review must assess whether these gates fit available engineering capacity,
human review and authorized compute. Expansion modules can follow CORE, but their
existing TODO obligations remain tracked. Section-11 serverless and integration
requirements cannot be deferred while still claiming complete CORE.

## Next packet

Repair and validate offline CP4 for the owner-selected Candidate A and active
control, without starting compute. LV1 remains the next live behavior packet
only after its separate fresh bounded authorization; Candidate B stays retired.
