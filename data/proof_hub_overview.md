# OrangePro KG Proof Hub

**URL:** https://orangepro-kg-proof-hub.onrender.com/

---

OrangePro KG Proof Hub

Shareable working artifacts for the KG proof effort. These pages are meant to stay current: update the HTML files in this folder, redeploy the static site, and the public links keep working.

Focus:
 KG vs baseline lift
Tenants:
 HTTP Core + Airflow + Click public proof
Audience:
 Aamir / review
94.1%
CROSS-TENANT KG WIN RATE
48 KG wins of 51 judged pairs · 9 packets · repeatability 9/9
HTTP CORE
22 / 24 · 91.7%
AIRFLOW
20 / 21 · 95.2%
CLICK
6 / 6 · 100.0% (n=6, CI wide)
JUDGE
gpt-4.1, calibration-floor-passed at point estimate
BRIDGE STATE
cross_tenant_aggregate_positive_authorized
MODE MIX
48 active · 2 KG-only · 1 timeout
PHASE C
graphlit_neutral · 6-packet A/B, delta -2.3pp
PUBLIC CLAIM
RQ1 safe_to_present=true · signed governance authorization; RQ2/RQ3 remain false
FIRST PICTURE TO SHOW
From User Story To Generated Tests

This is the product path we are locking down. The KG does not just add a big text blob: it turns the story into auditable anchors, executes competency questions, builds CoverageCells, injects bounded prompt context, then verifies what the model produced before any lift claim. CQs retrieve graph facts; RQ/rubric checks shape requirement quality; oracle rules decide what a generated test must actually assert.

1
Story Enters OPRO

Input can be GitHub issue, Jira ticket, manual story, or document. We freeze the source text, app overview, explicit acceptance criteria, and AC hash before generation.

No hidden AC rewrite for KG.
Baseline and KG receive the same explicit AC contract.
2
KG Resolves Anchors

The graph links the story to known requirements, PRs, changed files, services, endpoints, existing tests, incidents, outcomes, and generated-test history.

Proof edges are separated from candidate/vector/lexical context.
Messy public issues can stay diagnostic-only.
3
CQs Retrieve Context

Registered competency questions now run before prompt construction when required parameters are available. They ask which ACs exist, which code changed, what runtime surfaces are affected, what tests already cover it, and what gaps remain.

Rows carry cq_id, row hash, required relationships, and source node uid.
Remaining hardening: make all seven CQs the selected-row retrieval policy.
Candidate rows are not promoted to proof.
4
CoverageCells Are Built

The suite target becomes structured cells, not one vague prompt. A cell binds AC, workflow path, runtime interface, fault/regression pattern, execution mode, and expected oracle.

One generation packet per target cell.
Stable cell ids support replay and comparison.
5
Prompt Envelope Is Rendered

The model receives a small, cell-scoped prompt: the explicit AC list, selected CQ rows, target CoverageCell, required oracle, QEFix bucket, and generation contract.

Required facts are proof/manual first.
Candidate/support context is labeled or excluded from required assertions.
6
Oracle And Rubric Guide The Test

The prompt carries test-quality guidance from QEFix, FIRST, IEEE-style quality expectations, IBM/Facts-style traceability, and explicit oracle requirements.

Observable assertions beat setup-only tests.
Runtime behavior, error boundary, cleanup, and regression checks are preferred.
7
Generated Rows Stay Non-Proof

The LLM can declare coverage_cell_uid, but that only creates GENERATED_FOR_CELL process lineage. It does not prove the behavior is covered.

Invalid rows are filtered before save and judge dispatch.
Unknown cell ids are contained and measured.
8
Verifier Produces Proof, Bridge Records Evidence State

Static seeded-fault rules or human review can promote a generated row to COVERS_CELL. The proof edge requires verifier-shaped evidence, not model claims. The bridge then emits the cross-tenant evidence state.

target_cell_proof_ratio is the measurable lift signal.
Judge wins are supporting diagnostics, not proof by themselves.
Bridge emits evidence_state; safe_to_present stays
false
regardless of how positive the evidence becomes — it is a human-governance gate.
What Baseline Already Has
A vertical test-generation prompt, not a generic chat prompt.
Story text, app overview, explicit ACs, and bucket framing.
Structured output expectations and quality guidance.
Enough prompt engineering to generate useful tests on one repo.
What KG Injects
Explicit ACs plus source/hash.
CQ rows with provenance.
CoverageCell target and oracle.
Runtime surfaces: service, endpoint, file, test history.
Prior incident/outcome facts when proof-backed.
What RQ / Rubric Adds
QEFix bucket alignment.
FIRST test-quality checks.
IEEE-style traceability and repeatability expectations.
Oracle quality: observable assertion, boundary, cleanup, and regression signal.
What We Refuse To Claim
Candidate/vector/lexical rows are not proof.
Diagnostic packets do not count as headline AC coverage.
Positive packet scorecards are not product-wide KG lift.
KG is not being compared against a weak generic prompt.
Model-declared coverage is not COVERS_CELL.
Sonnet scorecards stay historical; the current claim-path judge is gpt-4.1 with calibration status exposed.
Evidence threshold met. Three public tenants, 9 packets, 51 judged pairs, 48 KG wins, aggregate KG win rate 94.1%, repeatability 9/9. Judge is claim-preferred gpt-4.1, calibration-floor-passed at point estimate (18/24, zero margin). Sonnet-4-6 missed the floor at 16/24 and remains historical only. Click's 100.0% is real but small-sample: 6 judged pairs, so it should not be read as a stronger tenant than HTTP Core or Airflow by itself.

Strong-baseline caveat. The baseline is not a weak "write some tests" prompt. It is already a product-shaped, vertical prompt with story context, app overview, acceptance criteria, bucket framing, and test-quality guidance. The measured result is therefore KG lift over a strong structured generation baseline. The honest product claim is: KG adds graph-grounded context, provenance, CoverageCells, selected CQ evidence, and verifier-backed constraints on top of an already competent prompt-engineered baseline.

Attribution caveat. The 51-pair aggregate is mode-mixed: 48 pairs are kg_graphlit_active, 2 are kg_only, and 1 is kg_graphlit_timeout. Phase C answers attribution on the original 6-packet HTTP Core + Airflow subset, not on all 9 public packets. It found Graphlit below the additive threshold: delta -2.3 percentage points, CI [-12.2pp, +7.6pp].

Authorization gate crossed for RQ1. RQ1 is safe_to_present=true only because a signed governance authorization matches the frozen headline evidence hash and claim template. RQ2 and RQ3 remain safe_to_present=false. In plain English: the measured test-quality lift number is approved for customer-facing use; the traceability and proof-boundary rows stay internal diagnostics until they have their own claim wording and sign-off.

Data-handling caveat. OrangePro KG does not persist ingested raw repository source files. It stores structural code metadata, source-system text used for grounding such as Jira/Confluence/PR excerpts, graph relationships, audit artifacts, and generated or repaired test-case bodies produced by the system. Credentials and tenant integration secrets are not shown on this proof hub.
ENTERPRISE SECURITY POSTURE
What We Tell Customers About Data, Encryption, And SOC 2

This proof hub is evidence for KG lift, not a security attestation. The customer-facing security framing is still useful here because procurement will ask what data is stored, how access is audited, and what is live versus roadmap.

Current
Data surface
No Raw Ingested Repo Source, But Derivative Tests Are Sensitive

KG stores structural code metadata, source-system text from Jira/Confluence/PRs/issues/ACs, graph relationships, embeddings, audit artifacts, and generated or repaired test bodies. Generated and repaired tests can reveal API shape, fixtures, identifiers, and workflows, so we treat them as confidential customer data.

Current
Access controls
Secrets Stay Out Of The Proof Surface

Tenant integration secrets are handled outside the KG proof hub and are not rendered in evidence pages. KG access audit logs record tenant, actor hash, route template, purpose, outcome, and data surface without raw bearer tokens, payloads, Cypher text, parameters, source IPs, or generated test bodies.

Readiness
SOC 2
SOC 2 Work Has Started, Certification Is Not Claimed

Access logging, signed claim authorization, write-only secret handling, and fail-closed proof gates are SOC 2-shaped controls. We should not claim SOC 2 Type II, external audit completion, or certified controls until the audit program and report exist.

Roadmap
Encryption
Encryption Is A Deployment Control, Not A Proof Claim

The target enterprise answer is TLS in transit, verified encryption at rest for each managed store, and clear retention/deletion policy. Customer-managed keys, customer-held keys, brokered retrieval, and private customer-cloud data planes are enterprise options under design, not claims this proof hub treats as already complete.

RETRIEVAL PROVIDER BOUNDARY
KG Owns Truth. Graphlit Is Below The Additive Threshold In Phase C.

The KG is the only source of entities, relationships, proof, and identifiers. Graphlit currently provides supplementary text retrieval. Phase C compared kg_only and kg_graphlit_active on the original 6 public packets. The validator-compliant decision is graphlit_neutral: useful to measure, not required for the current KG claim path.

Live
Retrieval Mode Capture

Every new GenerationRun records a retrieval_provider_mode from a fixed five-value enum. The bridge surfaces per-packet mode counts. Historical pre-instrumentation runs stay unspecified; the public-tenant aggregate is not contaminated.

kg_only · kg_graphlit_active · kg_graphlit_timeout
kg_graphlit_error · kg_graphlit_disabled
Live
Prompt Precedence

The assembled LLM prompt places the KG block before any retrieval block. KG content carries an explicit KG authority rule: supplementary retrieval may add background but must not override KG-provided identifiers, endpoints, services, acceptance criteria, coverage cells, or test names.

Hosted smoke: KG marker at byte 299; RAG block at byte 4012; supplementary label at byte 4059.
Conflict and non-conflict snapshot tests in place.
Live
kg_only Request Override

A request-level override forces the runtime path to skip Graphlit entirely while keeping KG enrichment active. This makes the A/B's kg_only arm a controlled comparison, not a silent Graphlit-disabled or Graphlit-failed run.

Smoke job dcfc6af2-551d-4219-aa40-256fa490d973 (BeautyCo synthetic).
Persisted retrieval_provider_mode=kg_only; no RAG path involved.
Gate proof only. Not Phase C. Not lift evidence.
Live
Phase C Preflight Validator

The Phase C artifact contract is frozen before any A/B result exists. The validator computes the decision branch from delta and CI bounds and refuses artifacts where the declared decision does not match. Replay/supersession protocol requires explicit chain plus reason.

Decision rule: additive (≥+0.03 and CI>0), neutral, dilutive (≤-0.03 and CI<0).
Per-packet mode homogeneity, judge-model = gpt-4.1, calibration artifact required.
Validated
Phase C: 6-Packet Retrieval A/B

Same 6 packets, same baselines, same claim-preferred gpt-4.1 judge. The matched subset produced kg_only 41/43 = 95.3% versus kg_graphlit_active 40/43 = 93.0%. Delta = -2.3 percentage points with CI [-12.2pp, +7.6pp]. By the pre-committed rule this is graphlit_neutral: Graphlit's effect is below this sample's power to resolve, not proven equal.

SCOPE

HTTP Core + Airflow only: 6 packets, 43 matched judged pairs. Click is not part of Phase C.

ARTIFACT

evals/retrieval_provider/kg_only_vs_kg_graphlit_2026-05-12.json validates.

BOUNDARY

Phase C answers retrieval attribution only. It does not auto-flip safe_to_present.

MEETING CHECKLIST
What We Fixed Versus What Still Blocks Proof

This is the short operating ledger: product-level fixes are separated from proof gates. Green means implemented in the product path; amber means usable but still being hardened; red means still blocking a broad KG-lift claim.

Done
AC parity
Acceptance Criteria Are Shared

Baseline and KG receive the same explicit AC list. AC source/hash metadata is forwarded to KG writeback, and source-backed public issue criteria can be human-reviewed without pretending messy issue prose is formal AC.

Done
Source AC gate
Required Signals Come From The Formal Contract

For formal AC-backed public packets, required contract identifiers are now filtered against the AC text. Reproduction-snippet locals such as helper function names or temporary variables stay as context, not headline-blocking required signals.

Done
Prompt hygiene
Prompt Drift And Tenant Leakage Removed

HTTP/2 and FX-style hardcoded branches were moved into data/structural rules. Invalid rows are filtered before save and judge dispatch, and reused-state guidance no longer fires on unrelated performance language such as thread lock duration or remaining bytes.

Hardened
CQ injection
CQ Rows Now Enter The Runtime Path

Generation records CQ row handles, row hashes, required relationships, and source node ids. Available story-scoped CQs run before prompt construction and feed CoverageCell packets. Remaining hardening: make all seven CQs the primary retrieval router with selected-row policy.

Done
Per-cell generation
CoverageCells Replace One Big Prompt

Target cells have stable ids, one LLM call per cell, prompt hashes, cell uid propagation, and non-proof GENERATED_FOR_CELL lineage. Model output no longer pretends to be coverage proof.

Done
Verifier proof
COVERS_CELL Requires Verifier Evidence

The proof edge is blocked from model-declared targets. Static seeded-fault detection or human review can produce verifier-shaped writeback, and target_cell_proof_ratio is the measurable cell-coverage signal.

Done
Public packets
HTTP Core, Airflow, And Click Are Positive

Three public tenants now pass the packet-scorecard repeatability bar under claim-preferred gpt-4.1 judging. HTTP Core: 3 packets, 24 judged pairs, KG win rate 91.7%. Airflow: 3 packets, 21 judged pairs, KG win rate 95.2%. Click: 3 packets, 6 judged pairs, KG win rate 100.0%. Click's result is n-small and has a wide confidence interval, so it strengthens generalization without proving Click is the strongest tenant. Combined bridge aggregate: 9 packets, 51 pairs, 48 KG wins, KG win rate 94.1%. The judge label is calibration-backed at the point estimate; the public claim still stays gated.

Done
Scorecard gate
Pair Floor Scales To Source AC Count

Public proof packets with fewer formal ACs are no longer forced through an arbitrary 5-pair minimum. The pass bar now uses the smaller of five pairs or the source-backed AC count, while still requiring KG win rate and low-confidence controls.

Done
Repeatability
Repeatability Cleared Per Public Tenant

The previous repeatability blocker is cleared for HTTP Core and Airflow. Each tenant is now packet_scorecard_positive_repeatability_ready. Diagnostic messy issues still do not count toward headline AC coverage.

Done
Identifier audit
Generated Tests Now Get KG Identifier Scrutiny

The new verifier audits emitted endpoints, AC ids, services, and sparse code identifiers after writeback. Live replay covered 45 public-proof KG tests: 13 unknown endpoint identifiers on HTTP Core, zero AC-id drift, zero service fabrication, and zero wrong-relation findings.

Claim gate
Product lift
The Product-Wide Claim Is Authorized But Bounded

The data aggregate is queryable, calibrated, preferred by the bridge, and now authorized for RQ1 by signed governance. The honest statement is strong three-public-tenant evidence, not unrestricted "works on any repo" language.

FOUNDATION CLOSEOUT
KG Foundation Is Closed For Engineering Review

Public claim wording is now authorized for the RQ1 generated-test lift claim through a signed governance row. Deeper seven-CQ routing is deferred as the first post-foundation feature, not a blocker to this foundation closeout.

Done
Evidence
Cross-Tenant Lift Evidence Is Queryable

Bridge output now shows 3 tenants, 9 packets, 51 judged pairs, 48 KG wins, 94.1% KG win rate, 9/9 repeatability, and no data blockers. This is the measured evidence package, with retrieval-mode mix disclosed separately.

Done
Retrieval attribution
Graphlit Is Measured, But Not Needed For The Claim Path

Phase C returned graphlit_neutral on the original 6-packet subset: KG-only 95.3%, KG+Graphlit 93.0%, delta -2.3pp with CI [-12.2pp, +7.6pp]. That means Graphlit's contribution is below this sample's noise floor, not proven equal.

Done
Audit pack
Freeze The Review Pack

The audit manifest freezes packet counts, judge artifacts, verdict exports, calibration checks, Phase C result, SHA-256 checksums, and verification commands. Reviewers can replay why each row was counted.

Recorded
Governance
Public RQ1 Wording Is Authorized

The bridge now reports safe_to_present=true for RQ1 only when the signed governance row matches the frozen headline evidence hash and claim template. RQ2/RQ3 remain false.

Deferred
CQ router
Seven-CQ Routing Moves To Post-Foundation

CQ rows already enter runtime context. The full seven-CQ selected-row retrieval policy is explicitly deferred as the first post-foundation feature, not counted as missing foundation proof.

Future
New features
Everything After That Is Product Expansion

Repair loop, memory store, more tenants, fixture endpoint classification, richer PR intelligence, and Graphlit/RAG experiments become feature work. They can improve the product, but they should not be framed as blockers to the current KG lift foundation.

JUDGED PAIR EVIDENCE
All 51 Judged Pairs

Static rendering of every baseline-vs-KG judgment behind the 94.1% aggregate: full test bodies, judge winner, confidence, rationale, and all eight rubric dimensions.

Best for governance review before public wording authorization.
Shows the strong structured baseline beside the KG-generated test.
Includes data-handling, strong-baseline, and authorization-gate caveats.
Open Judged Pairs
ARCHITECTURE RESET
KG Lift Architecture Reset

Current truth table for the KG lift effort: what is product-level, what is overfit risk, where SHACL fits, how messy tenant data should be handled, and what must be fixed before broad claims.

Best for deciding what to build next.
Separates one-packet proof from product-level lift.
Shows target architecture with CQ router, SHACL gate, CoverageCells, and suite metrics.
Open Architecture Reset
ARCHITECTURE STORY
KG Proof Kernel Process Visual

Non-technical visual walkthrough of the five-stage KG process, where ontology enters, why the proof-kernel relationships exist, and how QEFix/FIRST/IEEE/IBM/Facts map into the model.

Best for architecture explanation.
Shows ontology and relationship rationale.
Useful before discussing current HTTP Core evidence.
Open Architecture Visual
PROOF STATUS DETAIL
HTTP Core KG First Proof Status

Current public proof-status page with HTTP Core detail, archived diagnostics, and the same three-tenant 51-pair aggregate used by the proof hub headline.

Best for HTTP Core/Airflow/Click proof details and judged-pair examples.
Shows the current aggregate: 9 packets, 51 judged pairs, 48 KG wins.
States the RQ1 authorization boundary and keeps broader product claims bounded.
Open HTTP Core Status