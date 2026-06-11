# OrangePro

## Knowledge Graph Specification
**Classification:** Confidential — Engineering Due Diligence Distribution Only
**Audience:** Engineering teams conducting technical due diligence
**Companion Document:** OrangePro Architecture Document

---

## Purpose and Scope

This document is the technical companion to the OrangePro Architecture Document. It provides engineering-level detail on the knowledge graph schema, the proof-kernel ontology, the SHACL-equivalent validation gates, the deterministic competency questions with Cypher evidence, and the CoverageCell dispatch mechanism.

The Architecture Document describes what OrangePro does and why the design decisions were made. This document describes how the knowledge graph is structured, how it is queried, and how its correctness is validated.

---

## Table of Contents

1. Ontological Foundation: The Deterministic Proof Kernel
2. The Three Epistemic Tiers
3. Full Node Property Schemas
4. The 18 Proof-Kernel Relationships
5. SHACL-Equivalent Validation Gates
6. Competency Questions: Full Catalog with Cypher Evidence
7. CoverageCell Dispatch Mechanism
8. Graph Quality Lifecycle
9. GeneratedTestCase Output Schema
10. QEFix Taxonomy: 16 Buckets with Standards Mapping
11. Design Principles
12. Privacy-First Pipeline: Technical Detail
13. Risk Scoring: Formula Derivation
A. Appendix A — Cypher DDL (Indexes and Constraints)
B. Appendix B — Proof Hub Validation Results
C. Appendix C — Seven-CQ Router Deferral
D. Appendix D — Audit Pack and Freeze Protocol
E. Appendix E — Architecture Evolution Log
F. Appendix F — Document Revision History

---

## 1. Ontological Foundation: The Deterministic Proof Kernel

### 1.1 Design Foundation: The 5-Pillar Framework

The OrangePro knowledge graph is ontologically-driven, not merely a knowledge graph solution. The core principle: "Ontology has to have deterministic ground truth." Confidence scores never appear in the proof traversal path. Architecturally, this constitutes a neuro-symbolic design: the proof kernel provides symbolic, deterministic guarantees while LLM-proposed relationships and generated outputs are quarantined in candidate tiers until they satisfy formal promotion criteria defined by the validation gates below.

The specific failure mode that the architecture prevents: multi-hop queries across probabilistic edges compound errors exponentially. A 3-hop query with 0.8 confidence at each hop yields 0.51 at the output. The design principle: "Be right up to 2-3 hops with certainty, then use probability beyond the proof boundary."

The graph is structured around a 5-pillar ontological framework:

| Pillar | What It Means | OrangePro Implementation |
|--------|--------------|---------------------------|
| RQ (Research Questions) | Business requirements that justify the KG | 5 RQs — every node/edge must trace to at least one |
| CQ (Competency Questions) | Deterministically answerable — rows, not scores | 5 CQs with Cypher, return rows |
| Query (Justify why KG) | Prove multi-hop traversal can't be done with SQL | 5 queries requiring 3+ hops across heterogeneous types |
| KGE (Embeddings validation) | Validate relationship types are structurally sound | TransE evaluation on proof-kernel edges |
| Remove Noise Nodes | If node fails RQ + CQ + KGE → remove | 3-tier boundary, proof kernel bounded to 18 |

### 1.2 The 13 Axioms

Every node type, edge type, and CQ in the KG is derivable from one or more of 13 ontological axioms. These axioms are derived from:
- 20 years of enterprise QA practice (Oracle, Ford/Autonomic, Salesforce, ServiceNow)
- Empirical validation from Ford/Autonomic production data
- IBM ODC v5.2 (Chillarege 1992) and IEEE 1044-2009

The axioms are documented in full in the companion document "OrangePro Ontological Axioms v1.0." The key structural axioms for the KG schema:

1. Every production bug has a code change that introduced it → IMPLEMENTED_BY, PR_CHANGES edges are mandatory
2. Every escaped bug had a test that should have existed but did not → CoverageCell is a first-class entity
3. Every test case covers exactly the behavior described in its parent AC → COVERS_CRITERION is a hard constraint
4. QA gaps compound across sprints → CoverageCell state persists across GenerationRuns

### 1.3 Why a Knowledge Graph (Not SQL)

The following queries justify the KG architecture — they require multi-hop traversal across heterogeneous node types that cannot be expressed as SQL JOINs without a schema that changes per tenant:

| Query | Hops | Node Types Traversed |
|-------|------|---------------------|
| "Find all stories affected if this one file changes" | 4 | File → PullRequest → Story → AcceptanceCriterion → Endpoint |
| "What is the minimum test set covering all high-risk changes in this sprint?" | 3 | Story → CoverageCell → GeneratedTestCase (graph optimization) |
| "Which past incidents share the same root cause pattern as this PR?" | 4 | PullRequest → File → Story → Incident → Story (pattern match) |
| "Trace from a generated test back to the requirement it satisfies" | 3 | GeneratedTestCase → CoverageCell → AcceptanceCriterion → Story |
| "Which endpoints have no acceptance criterion and no test?" | 3 | Endpoint ← REQUIRES_INTERFACE ← AcceptanceCriterion ← Story |

---

## 2. The Three Epistemic Tiers

### 2.1 Architecture

The graph is partitioned into three epistemic tiers. The partition is enforced at the application layer through the SHACL-equivalent gates (Section 5).

```
┌─────────────────────────────────────────────────────────────────┐
│ WEAK/SUPPORT — Never enters proof paths                         │
│ Vector similarity, KGE predictions, process metadata            │
│ Useful for exploration only                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CANDIDATE — Visible but excluded from proof traversal       │ │
│ │ LLM-proposed edges, heuristic matches, unreviewed mappings  │ │
│ │ Promotion requires evidence review                          │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ PROOF KERNEL — Deterministic CQs traverse only here     │ │ │
│ │ │ 18 relationships, evidence-contracted, gate-validated    │ │ │
│ │ │ This is the bounded claim layer                         │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Tier Promotion Rules

| From | To | Requirement |
|------|-----|-------------|
| Weak → Candidate | Evidence review by system or human | At least one deterministic signal (file path, branch name, API spec) |
| Candidate → Proof | Gate validation + evidence contract | Must pass Relationship Gate (Gate 2) + have method field populated |
| Proof → Candidate (demotion) | Evidence invalidated | Source artifact deleted, renamed, or contradicted by newer evidence |

### 2.3 Why Three Tiers (Not Two)

A two-layer model (deterministic core + probabilistic intake) creates a cliff problem: the boundary between "confirmed" and "unconfirmed" becomes a single confidence threshold (e.g., 0.8). Edges at 0.79 are treated identically to edges at 0.1.

The three-tier model provides graduated epistemic commitment: strong enough for proof (kernel), plausible enough for exploration (candidate), and too weak for anything but retrieval (weak). This prevents the cliff effect and gives the system a clear promotion path.

---

## 3. Full Node Property Schemas

The OrangePro knowledge graph contains **24 core ontology labels** organized into three semantic tiers, plus 12 operational labels (graph maintenance and feedback loop) and 2 proprietary labels (QEFix domain taxonomy). Only the 24 core ontology labels participate in proof-kernel traversal.

### 3.1 Tier 1 — Requirements Nodes

**Story**
```
{
  id: string (required) — unique identifier from Jira
  title: string (required) — story title
  description: string — full story text
  source: string (required) — "jira" | "github_issue" | "manual"
  tenant_id: string (required) — tenant scope
  repo: string — repository identifier
  status: string — "open" | "in_progress" | "done"
  created_at: datetime (required)
  updated_at: datetime
}
```

**AcceptanceCriterion**
```
{
  id: string (required) — unique identifier
  text: string (required) — the criterion text
  story_id: string (required) — parent story reference
  testable: boolean — whether this AC is testable
  tenant_id: string (required)
}
```

**BusinessRule**
```
{
  id: string (required)
  description: string (required)
  domain: string — business domain this rule belongs to
  tenant_id: string (required)
}
```

**UserFlow**
```
{
  id: string (required)
  name: string (required)
  steps: list[string] — ordered list of flow steps
  services_involved: list[string] — services this flow touches
  tenant_id: string (required)
}
```

**Capability**
```
{
  id: string (required)
  name: string (required)
  description: string
  stories: list[string] — story IDs in this capability
  proof_ready: boolean — whether all stories have sufficient context
  tenant_id: string (required)
}
```

**Tenant**
```
{
  id: string (required) — unique tenant identifier
  name: string (required) — display name
  slug: string (required) — URL-safe identifier
  plan: string — "free" | "pro" | "enterprise"
  created_at: datetime (required)
}
```

**JiraTicket**
```
{
  id: string (required) — Jira issue key (e.g., PROJ-123)
  title: string (required)
  type: string — "story" | "bug" | "task" | "epic"
  status: string — raw Jira status
  tenant_id: string (required)
  synced_at: datetime (required)
}
```

### 3.2 Tier 2 — Implementation Nodes

**PullRequest**
```
{
  id: string (required) — GitHub PR number + repo
  title: string (required)
  body: string — PR description
  author: string
  branch: string — source branch name
  base_branch: string — target branch
  repo: string (required)
  state: string — "open" | "merged" | "closed"
  merged_at: datetime
  tenant_id: string (required)
}
```

**File**
```
{
  path: string (required) — full file path in repo
  repo: string (required)
  language: string — detected programming language
  last_modified: datetime
  tenant_id: string (required)
}
```

**TestFile**
```
{
  path: string (required) — full file path
  repo: string (required)
  framework: string — "pytest" | "jest" | "junit" | etc.
  test_count: integer — number of test cases in file
  tenant_id: string (required)
}
```

**CodeSymbol**
```
{
  id: string (required) — fully qualified name
  name: string (required) — short name
  type: string — "function" | "class" | "method"
  file_path: string (required)
  repo: string (required)
  tenant_id: string (required)
}
```

**Service**
```
{
  id: string (required)
  name: string (required)
  repo: string
  endpoints: list[string] — endpoint IDs owned by this service
  tenant_id: string (required)
}
```

**Endpoint**
```
{
  id: string (required)
  path: string (required) — URL path
  method: string (required) — HTTP method
  service: string (required) — owning service
  tenant_id: string (required)
}
```

**APIContract**
```
{
  id: string (required)
  spec_url: string — OpenAPI/Swagger spec URL
  version: string — API version
  service_id: string (required) — owning service
  tenant_id: string (required)
}
```

**Team**
```
{
  id: string (required)
  name: string (required)
  members: list[string] — team member identifiers
  services_owned: list[string] — service IDs this team owns
  tenant_id: string (required)
}
```
### 3.3 Tier 3 — Validation & Generation Nodes

**TestCase**
```
{
  id: string (required)
  name: string (required) — test function/method name
  file_path: string (required) — path to test file
  repo: string (required)
  framework: string
  tenant_id: string (required)
}
```

**GeneratedTestCase**
```
{
  id: string (required) — UUID
  title: string (required)
  description: string (required)
  steps: list[object] — ordered test steps
  expected_result: string (required)
  qefix_category: string (required) — one of 16 buckets
  coverage_cell_uid: string (required) — which cell this fills
  generation_run_id: string (required)
  judge_score: float — composite judge score (0-5)
  judge_verdict: string — "accepted" | "rejected" | "needs_edit"
  anchor_story_id: string (required) — lineage trace
  context_ac_id: string (required) — lineage trace
  tenant_id: string (required)
  created_at: datetime (required)
}
```

**GenerationRun**
```
{
  id: string (required) — UUID
  trigger: string — "pr_webhook" | "manual" | "scheduled"
  trigger_pr_id: string — the PR that triggered this run
  plan: object — the generation plan (cells to fill)
  status: string — "planning" | "generating" | "judging" | "complete"
  cells_planned: integer
  cells_filled: integer
  tenant_id: string (required)
  started_at: datetime (required)
  completed_at: datetime
}
```

**CoverageCell**
```
{
  uid: string (required) — deterministic hash of (story_id, ac_id, qefix_bucket)
  story_id: string (required)
  acceptance_criterion_id: string (required)
  qefix_category: string (required)
  status: string — "gap" | "covered" | "stale"
  covered_by: string — GeneratedTestCase ID that fills this cell
  last_evaluated: datetime
  tenant_id: string (required)
}
```

**JudgeRun**
```
{
  id: string (required) — UUID
  generation_run_id: string (required) — which GenerationRun this judges
  mode: string — "single" | "dual" | "consensus"
  model_primary: string — "o3-mini" | "claude-3.5-sonnet" | "gpt-4o"
  model_secondary: string — (null for single mode)
  dimensions_scored: list[string] — ["relevance", "completeness", "atomicity", "clarity", "traceability"]
  verdict: string — "accepted" | "rejected" | "needs_edit"
  composite_score: float — average across 5 dimensions (0-5)
  is_lift_comparison: boolean — whether this was a KG-vs-baseline blind comparison
  lift_verdict: string — "kg_preferred" | "baseline_preferred" | "tie" (only if is_lift_comparison)
  test_case_id: string (required) — GeneratedTestCase being judged
  tenant_id: string (required)
  judged_at: datetime (required)
}
```

**LearningWeight**
```
{
  id: string (required)
  relationship_type: string — which of the 18 relationships this weight applies to
  source_node_type: string
  target_node_type: string
  weight: float — current weight (0.0 to 1.0)
  adjustment_reason: string — "developer_accept" | "developer_reject" | "incident_correlation" | "judge_feedback"
  adjustment_count: integer — how many times this weight has been updated
  tenant_id: string (required)
  last_updated: datetime (required)
}
```

**Incident**
```
{
  id: string (required)
  title: string (required)
  severity: string — "critical" | "high" | "medium" | "low"
  source: string — "pagerduty" | "jira" | "servicenow"
  services_affected: list[string]
  root_cause_pr: string — PR that introduced the issue (if known)
  tenant_id: string (required)
  created_at: datetime (required)
}
```

**RepairContract**
```
{
  id: string (required) — UUID
  generated_test_id: string (required) — the failing test to repair
  failure_reason: string (required) — why the test failed
  repair_strategy: string — "regenerate" | "patch" | "split"
  max_attempts: integer — retry budget
  tenant_id: string (required)
  created_at: datetime (required)
}
```

**RepairOutcome**
```
{
  id: string (required) — UUID
  contract_id: string (required) — parent RepairContract
  attempt: integer (required) — attempt number
  success: boolean (required)
  repaired_test_id: string — new GeneratedTestCase if successful
  tenant_id: string (required)
  completed_at: datetime (required)
}
```

**OutcomeEvent**
```
{
  id: string (required) — UUID
  event_type: string (required) — "generation_complete" | "repair_complete" | "judge_complete" | "feedback_received"
  entity_id: string (required) — the node this event relates to
  entity_type: string (required) — node label of the entity
  metadata: object — event-specific payload
  tenant_id: string (required)
  occurred_at: datetime (required)
}
```

### 3.4 Operational Labels (Graph Maintenance & Feedback Loop)

These labels support the self-improving data flywheel but do not participate in proof-kernel traversal:

| Label | Role |
|-------|------|
| `SyncRun` | Tracks connector synchronization executions |
| `SyncSourceStatus` | Records per-source sync health |
| `ConnectorCheckpoint` | Watermark for incremental connector pulls |
| `ReconciliationRun` | Drift detection and reconciliation execution |
| `DraftInput` | Staged input before graph commit |
| `GroundingResolveCache` | Cached grounding resolution for performance |
| `LearningWeight` | Feedback-adjusted weights for generation tuning |
| `JudgeRun` | Execution of the LLM judge evaluation |
| `JudgePairVerdict` | Individual A/B verdict from a judge run |
| `GenerationFeedback` | User or system feedback on generated tests |
| `GraphNormalizationJob` | Background job for graph consistency maintenance |
| `AcceptanceCriteriaProjectionJob` | Background job for AC extraction and projection |

### 3.5 Proprietary Labels (OrangePro Domain Taxonomy)

| Label | Role |
|-------|------|
| `QEFixBucket` | Top-level defect category in the QEFix taxonomy |
| `QEFixLabel` | Fine-grained defect label within a QEFix bucket |

---

## 4. The 18 Proof-Kernel Relationships

### 4.1 Relationship Contracts

Every proof-kernel relationship carries an evidence contract:

```
{
  type: string — relationship type name
  from_label: string — source node label
  to_label: string — target node label
  method: string — how this edge was established
  evidence_source: string — what system provided the evidence
  gate_passed: string — which SHACL gate validated this edge
  created_at: datetime
  tier: "proof" — always "proof" for kernel edges
}
```

### 4.2 Complete Relationship Catalog

**Group 1: Requirements Structure**

| # | Type | From → To | Method | Cardinality |
|---|------|-----------|--------|-------------|
| 1 | HAS_ACCEPTANCE_CRITERION | Story → AcceptanceCriterion | Jira API extraction | 1:N |
| 2 | PART_OF_CAPABILITY | Story → Capability | Semantic clustering + review | N:1 |

**Group 2: Implementation Traceability**

| # | Type | From → To | Method | Cardinality |
|---|------|-----------|--------|-------------|
| 3 | IMPLEMENTED_BY | Story → PullRequest | Branch naming convention + PR body | 1:N |
| 4 | PR_CHANGES | PullRequest → File | Git diff (deterministic) | 1:N |
| 5 | MODIFIES | PullRequest → CodeSymbol | AST analysis | 1:N |
| 6 | REQUIRES_INTERFACE | AcceptanceCriterion → Endpoint | API spec + route analysis | N:N |
| 7 | OWNS | Service → Endpoint | Route registration | 1:N |

**Group 3: Test Coverage**

| # | Type | From → To | Method | Cardinality |
|---|------|-----------|--------|-------------|
| 8 | TESTED_BY | Story → TestCase | Test file path + import analysis | 1:N |
| 9 | CONTAINS_TEST | TestFile → TestCase | AST extraction | 1:N |
| 10 | COVERS_CRITERION | TestCase → AcceptanceCriterion | Test-to-AC mapping | N:N |
| 11 | COVERS_CELL | GeneratedTestCase → CoverageCell | CoverageCell dispatch | 1:1 |

**Group 4: Generation Lineage**

| # | Type | From → To | Method | Cardinality |
|---|------|-----------|--------|-------------|
| 12 | USED_ANCHOR | GenerationRun → Story | Pipeline lineage | N:N |
| 13 | USED_CONTEXT | GenerationRun → AcceptanceCriterion | Pipeline lineage | N:N |
| 14 | PRODUCED_TEST | GenerationRun → GeneratedTestCase | Pipeline lineage | 1:N |
| 15 | GENERATED_FOR_CAPABILITY | GeneratedTestCase → Capability | Pipeline dispatch | N:1 |
| 16 | GENERATED_FOR_CRITERION | GeneratedTestCase → AcceptanceCriterion | Pipeline dispatch | N:1 |
| 17 | GENERATED_FOR_FLOW | GeneratedTestCase → UserFlow | Pipeline dispatch | N:1 |

**Group 5: Production Evidence**

| # | Type | From → To | Method | Cardinality |
|---|------|-----------|--------|-------------|
| 18 | REGRESSION_EVIDENCE_FOR | Incident → Story | Incident-to-story trace | N:N |

### 4.3 Relationships Excluded from Proof Kernel

The following relationship types are excluded from the proof kernel by design:

| Relationship | Reason Excluded |
|-----------------|----------------|
| COVERS (generic) | Too broad — replaced by specific COVERS_CRITERION and COVERS_CELL |
| TRIGGERED_BY | Ambiguous semantics — replaced by REGRESSION_EVIDENCE_FOR |
| LINKED_TO | Too vague — lives in candidate tier only |
| CLASSIFIED_AS | QEFix classification is a node property, not an edge |
| EXPOSES | Replaced by OWNS (clearer domain/range) |
| GENERATED_FOR (generic) | Split into 3 specific edges: _CAPABILITY, _CRITERION, _FLOW |

---

## 5. SHACL-Equivalent Validation Gates

### 5.1 Architecture

OrangePro implements SHACL-equivalent validation through four application-layer gates. The gates are enforced in the FastAPI ingestion and writeback services. They are hard rejections, not advisory warnings.

### 5.2 Gate Specifications

**Gate 1: Ingestion Gate (Node Shapes)**

| Constraint | SHACL Equivalent | Implementation |
|-----------|------------------|----------------|
| Required properties | sh:minCount 1 | Pydantic model validation |
| Data type enforcement | sh:datatype | Pydantic type annotations |
| Allowed values | sh:in | Enum validation |
| String patterns | sh:pattern | Regex validation |

Rejection response:
```json
{
  "gate": "ingestion",
  "violation": "missing_required_field",
  "node_type": "Story",
  "field": "id",
  "message": "Story node requires 'id' field"
}
```

**Gate 2: Relationship Gate (Domain/Range Contracts)**

| Constraint | SHACL Equivalent | Implementation |
|-----------|------------------|----------------|
| Source node type | sh:class (subject) | Label check before edge creation |
| Target node type | sh:class (object) | Label check before edge creation |
| Allowed relationship types per node | sh:property | Whitelist per node label |
| Cardinality | sh:maxCount / sh:minCount | Count check on existing edges |

Rejection response:
```json
{
  "gate": "relationship",
  "violation": "invalid_domain",
  "relationship": "HAS_ACCEPTANCE_CRITERION",
  "from_label": "File",
  "expected_from": "Story",
  "message": "HAS_ACCEPTANCE_CRITERION can only originate from Story nodes"
}
```

**Gate 3: Pre-Generation Gate (Proof-Valid Context Only)**

| Constraint | SHACL Equivalent | Implementation |
|-----------|------------------|----------------|
| Only proof-kernel edges in context | sh:closed true | Tier filter on context query |
| No candidate edges in generation prompt | sh:ignoredProperties | Explicit exclusion list |
| Minimum context completeness | sh:qualifiedMinCount | At least 1 anchor + 1 context required |

**Gate 4: Writeback Gate (Lineage Validation)**

| Constraint | SHACL Equivalent | Implementation |
|-----------|------------------|----------------|
| Must have USED_ANCHOR | sh:qualifiedMinCount 1 | Edge existence check |
| Must have USED_CONTEXT | sh:qualifiedMinCount 1 | Edge existence check |
| Must have coverage_cell_uid | sh:minCount 1 | Property existence check |
| Must have generation_run_id | sh:minCount 1 | Property existence check |

---

## 6. Competency Questions: Full Catalog with Cypher Evidence

### 6.1 Design Principles for CQs

Each CQ in the OrangePro system follows these design rules:

1. **Deterministic** — returns rows, not scores. The answer is a result set, not a probability.
2. **Bounded hops** — max 3 hops within the proof kernel. Beyond 3 hops, error compounds.
3. **Traces to RQ** — every CQ must justify its existence by serving at least one business requirement.
4. **Proves shape** — the CQ validates that the graph has a particular structure, not just that data exists.
5. **Non-negation preferred** — CQs prove why the graph works, not what's missing (though gap detection CQs are an exception by design).

### 6.2 The 5 Deterministic CQs

**CQ-01: Which stories have no test coverage?**

Traces to: RQ-01
Hops: 1
Shape proved: Every Story should have at least one TESTED_BY edge

```cypher
MATCH (s:Story {tenant_id: $tenant_id})
WHERE NOT (s)<-[:TESTED_BY]-(:TestCase)
  AND NOT (s)<-[:GENERATED_FOR_CRITERION]-(:GeneratedTestCase)
RETURN s.id AS story_id, s.title AS story_title
ORDER BY s.created_at DESC
```

Why deterministic: TESTED_BY edge either exists or does not. Binary.

**CQ-02: What is the full evidence chain for a given PR?**

Traces to: RQ-03
Hops: 3 (PR → Story → AC → TestCase)
Shape proved: The traceability chain is complete from code change to test

```cypher
MATCH (pr:PullRequest {id: $pr_id})-[:IMPLEMENTED_BY]-(s:Story)
MATCH (pr)-[:PR_CHANGES]->(f:File)
OPTIONAL MATCH (s)-[:HAS_ACCEPTANCE_CRITERION]->(ac:AcceptanceCriterion)
OPTIONAL MATCH (ac)<-[:COVERS_CRITERION]-(tc:TestCase)
OPTIONAL MATCH (ac)<-[:GENERATED_FOR_CRITERION]-(gtc:GeneratedTestCase)
RETURN s.id, s.title, f.path, ac.id, ac.text, 
       collect(DISTINCT tc.name) AS existing_tests,
       collect(DISTINCT gtc.title) AS generated_tests
```

Why deterministic: Path traversal — chain exists or has gaps. No scoring.

**CQ-03: Which acceptance criteria have no covering test?**

Traces to: RQ-01, RQ-05
Hops: 2 (Story → AC → TestCase)
Shape proved: Every AC should have at least one COVERS_CRITERION edge

```cypher
MATCH (s:Story {tenant_id: $tenant_id})-[:HAS_ACCEPTANCE_CRITERION]->(ac:AcceptanceCriterion)
WHERE NOT (ac)<-[:COVERS_CRITERION]-(:TestCase)
  AND NOT (ac)<-[:GENERATED_FOR_CRITERION]-(:GeneratedTestCase)
RETURN s.id AS story_id, ac.id AS ac_id, ac.text AS criterion_text
ORDER BY s.created_at DESC
```

Why deterministic: Edge existence check. Binary result.

**CQ-04: Which endpoints have no acceptance criterion linked?**

Traces to: RQ-02
Hops: 1
Shape proved: Every Endpoint should have at least one REQUIRES_INTERFACE edge from an AC

```cypher
MATCH (e:Endpoint {tenant_id: $tenant_id})
WHERE NOT (e)<-[:REQUIRES_INTERFACE]-(:AcceptanceCriterion)
RETURN e.path AS endpoint_path, e.method AS http_method, e.service AS service_name
```

Why deterministic: Structural gap — edge exists or does not.

**CQ-05: Which incidents are regression evidence for untested stories?**

Traces to: RQ-03
Hops: 2 (Incident → Story → TestCase)
Shape proved: Incidents should not exist for stories with no test coverage

```cypher
MATCH (i:Incident)-[:REGRESSION_EVIDENCE_FOR]->(s:Story {tenant_id: $tenant_id})
WHERE NOT (s)<-[:TESTED_BY]-(:TestCase)
RETURN i.id AS incident_id, i.severity, s.id AS story_id, s.title AS story_title
ORDER BY i.severity DESC, i.created_at DESC
```

Why deterministic: Traversal returns rows, not scores.

### 6.3 Authorized Results

| Metric | Value | Evidence |
|--------|-------|----------|
| KG Lift (win rate) | 94.1% (48/51 pairs) | Judged pairs across 3 tenants |
| Tenants validated | httpcore, FastAPI, Pydantic | Public OSS repos |
| RQ-01 status | Authorized (bounded claim) | CQ-01 and CQ-03 return correct results |
| False claim rate | 0/51 | No human override needed |

---

## 7. CoverageCell Dispatch Mechanism

### 7.1 What Is a CoverageCell

A CoverageCell is the atomic unit of coverage in the OrangePro system. It represents a specific coverage obligation: the intersection of a Story, an AcceptanceCriterion, and a QEFix bucket.

```
CoverageCell.uid = hash(story_id + ac_id + qefix_category)
```

### 7.2 Cell States

| State | Meaning |
|-------|---------|
| `gap` | No test case (existing or generated) covers this cell |
| `covered` | At least one test case with passing judge score covers this cell |
| `stale` | A covering test existed but the source artifact changed (AC modified, story split) |

### 7.3 Dispatch Logic

When a GenerationRun is triggered:

1. Query all CoverageCells for the affected stories where `status = "gap"`
2. Order by gap priority (derived from: incident count for the story, recency of code changes, QEFix category weight)
3. Dispatch generation requests to cells in priority order
4. Each generated test carries `coverage_cell_uid` — the cell it was created to fill
5. On successful judge evaluation (score > threshold), cell status transitions from `gap` to `covered`

### 7.4 Why CoverageCells (Not Stories)

Stories are too coarse for targeted generation. A single story might have 5 acceptance criteria across 3 QEFix categories = 15 CoverageCells. Generating "a test for this story" is spray-and-pray. Generating "a test for this specific AC in this specific QEFix bucket" is targeted and traceable.

---

## 8. Graph Quality Lifecycle

### 8.1 The Six Stages

Before the generation pipeline can run, the knowledge graph must be in a proof-ready state. The graph quality lifecycle transforms messy customer data into a clean, proof-ready graph:

1. **Readiness Report** — Automated scan identifying missing links, stale edges, nodes with insufficient context.
2. **Sanitization Report** — Detailed analysis of data quality issues: duplicates, conflicts, orphans, normalization inconsistencies.
3. **Normalization Plan** — Proposed graph mutations to resolve issues. Presented for review before execution.
4. **Reviewed Normalization Job** — Approved plan becomes a tracked job with full audit trail.
5. **Proof-Ready Capability Cluster** — After normalization, affected stories are re-evaluated. Capability nodes are created for coherent groups with sufficient context.
6. **Comparison Run** — Baseline-vs-KG comparison validates the quality of the graph.

### 8.2 Stage Detail: Readiness Report

The readiness report is generated by the `KGReadinessService`. It scans the tenant graph and produces a structured report with:

- Coverage completeness: percentage of stories with at least one active TestCase
- Traceability completeness: percentage of stories with at least one linked PullRequest
- Stale edge count: number of COVERS_CRITERION edges where the source TestCase has been deprecated
- Orphaned node count: nodes with no relationships
- Proof-ready capability count: Capability nodes with `proof_ready=true`

### 8.3 Stage Detail: Sanitization Report

The sanitization report identifies specific data quality issues:

- Duplicate nodes: Stories with the same Jira key, Files with the same path
- Conflicting relationships: Multiple IMPLEMENTED_BY edges from the same PR to different Stories with conflicting signals
- Orphaned AcceptanceCriteria: Criteria nodes not linked to any Story
- Missing service links: Endpoints with no OWNS relationship to a Service
- Stale COVERS_CRITERION edges: Relationships where the source TestCase has been deprecated

### 8.4 Stage Detail: Normalization Plan

The normalization plan is a proposed set of graph mutations in JSON format:

```json
{
  "plan_id": "norm-plan-abc123",
  "tenant_id": "beautyco",
  "mutations": [
    {
      "type": "MERGE_DUPLICATE_NODES",
      "node_type": "Story",
      "node_ids": ["story-001", "story-002"],
      "keep_id": "story-001",
      "reason": "Same Jira key PROJ-456"
    },
    {
      "type": "MARK_EDGE_STALE",
      "relationship_type": "COVERS_CRITERION",
      "from_id": "test-case-789",
      "to_id": "ac-003",
      "reason": "TestCase deprecated in commit abc123"
    }
  ],
  "estimated_impact": {
    "nodes_affected": 12,
    "edges_affected": 8,
    "proof_ready_delta": "+3 capabilities"
  }
}
```

### 8.5 Stage Detail: Reviewed Normalization Job

The normalization plan, reviewed and approved by the tenant admin, becomes a tracked job. The job is executed atomically with rollback capability. The audit trail records:

- Who approved the job
- When it was executed
- Which mutations were applied
- The before/after state of affected nodes and relationships

### 8.6 Stage Detail: Proof-Ready Capability

After normalization, the `CapabilityService` re-evaluates the affected stories. A Capability is created for each semantically coherent group of stories that meets the proof-readiness criteria:

- At least one linked PullRequest (implementation evidence)
- At least one AcceptanceCriterion (testability evidence)
- No stale COVERS_CRITERION edges (clean coverage state)
- GapPriority score above the tenant's configured threshold

### 8.7 Gate Enforcement in the Lifecycle

The SHACL-equivalent gates are enforced at every stage:
- Stage 1-2: Gate 1 (Ingestion) validates incoming nodes
- Stage 3-4: Gate 2 (Relationship) validates proposed mutations
- Stage 5: Gate 3 (Pre-Generation) validates proof-readiness
- Stage 6: Gate 4 (Writeback) validates comparison run outputs

---

## 9. GeneratedTestCase Output Schema

Every generated test case produced by the pipeline follows this schema:

```json
{
  "id": "uuid-v4",
  "title": "Verify login fails with expired token",
  "description": "Validates that the authentication endpoint returns 401 when presented with an expired JWT token",
  "preconditions": ["User has a previously valid JWT token", "Token expiry time has passed"],
  "steps": [
    {"step": 1, "action": "Send GET /api/v1/profile with expired token in Authorization header", "expected": "Response status 401"},
    {"step": 2, "action": "Check response body", "expected": "Error message indicates token expiration"}
  ],
  "expected_result": "Authentication fails gracefully with clear error message",
  "qefix_category": "SECURITY",
  "coverage_cell_uid": "hash-of-story-ac-category",
  "generation_run_id": "uuid-of-run",
  "anchor_story_id": "JIRA-123",
  "context_ac_id": "AC-456",
  "model_used": "claude-3.5-sonnet",
  "judge_score": 4.2,
  "judge_verdict": "accepted",
  "judge_dimensions": {
    "relevance": 4.5,
    "completeness": 4.0,
    "atomicity": 4.5,
    "clarity": 4.0,
    "traceability": 4.0
  },
  "lineage": {
    "used_anchor": "JIRA-123",
    "used_context": "AC-456",
    "generated_for_capability": "CAP-auth",
    "generated_for_criterion": "AC-456",
    "covers_cell": "hash-of-story-ac-category"
  },
  "tenant_id": "tenant-xyz",
  "created_at": "2026-06-01T14:30:00Z"
}
```

---

## 10. QEFix Taxonomy: 16 Buckets with Standards Mapping

### 10.1 The 16 Categories

| # | Category | Description | IBM ODC | IEEE 1044 | Axiom Source |
|---|----------|-------------|---------|-----------|--------------|
| 1 | FUNCTIONAL | Incorrect behavior relative to spec | Function | Functional | Axiom 2 |
| 2 | INTEGRATION | Failures at service/component boundaries | Interface | Interface | Axiom 4 |
| 3 | PERFORMANCE | Latency, throughput, resource issues | Algorithm | Performance | Axiom 5 |
| 4 | SECURITY | Auth, authz, data exposure | Checking | Security | Axiom 10 |
| 5 | DATA_INTEGRITY | Incorrect data transformation/storage | Assignment | Data | Axiom 1 |
| 6 | UI_UX | Interface behavior, accessibility | Function | Usability | Axiom 2 |
| 7 | CONFIGURATION | Environment, deployment failures | Build/Package | Configuration | Axiom 6 |
| 8 | CONCURRENCY | Race conditions, deadlocks | Timing/Serial | Concurrency | Axiom 4 |
| 9 | ERROR_HANDLING | Missing/incorrect error handling | Checking | Exception | Axiom 8 |
| 10 | COMPATIBILITY | Cross-version, cross-platform issues | Interface | Compatibility | Axiom 4 |
| 11 | REGRESSION | Previously working behavior broken | — | Regression | Axiom 12 |
| 12 | MIGRATION | Migration-specific defects | Build/Package | Migration | Axiom 6 |
| 13 | OBSERVABILITY | Monitoring/alerting gaps | — | Monitoring | Axiom 8 |
| 14 | STATE_MANAGEMENT | Incorrect state transitions | Algorithm | State | Axiom 1 |
| 15 | AUTHORIZATION | Permission/access control failures | Checking | Access Control | Axiom 10 |
| 16 | CONTRACT_VIOLATION | API contract breaches | Interface | Contract | Axiom 4 |

### 10.2 Why 16 (Not 8, Not 50)

The taxonomy uses 16 categories because empirical evidence shows that fewer categories (e.g., 8) are too coarse for CoverageCell dispatch. A single "FUNCTIONAL" bucket covers too many distinct failure modes, making targeted generation impossible.

The upper bound is governed by the axiom derivation rule: every category must be derivable from at least one of the 13 axioms. Categories that cannot be derived are excluded. This prevents taxonomy bloat.

---

## 11. Design Principles

1. **Determinism in the proof path.** No confidence scores, no probability, no "maybe" in the proof kernel. Edges are facts. CQs return rows.

2. **Bounded claims.** We do not claim the graph is complete. We claim that what is in the proof kernel is correct. Completeness is a metric tracked over time, not a guarantee.

3. **Evidence contracts on every edge.** Every proof-kernel edge must answer: how was this established? What system provided the evidence? Which gate validated it? When?

4. **Noise removal over noise tolerance.** A smaller, cleaner graph with 18 proof relationships is more defensible than a large graph with 50 probabilistic relationships. Remove what cannot be proven.

5. **CQs prove shape, not data.** Competency questions validate that the ontology is correctly instantiated — that the graph has the right structure — not that it contains specific data values.

6. **Axiom derivation.** Every node type, edge type, and QEFix category must trace to at least one of the 13 ontological axioms. If it cannot be derived, it does not belong in the core.

---

## 12. Privacy-First Pipeline: Technical Detail

### 12.1 Architecture Overview

OrangePro never stores raw source code, full story text, or full PR descriptions. The privacy-first pipeline processes data through four stages:

```
STAGE 1 — TRANSIENT INGESTION
  Raw Payload (PR diff, Story text, Incident description)
  Held in memory ONLY — never written to disk or database
  TTL: 60 seconds max
        ↓
STAGE 2 — METADATA EXTRACTION
  Structured Metadata (Node IDs, Relationship signals,
  Risk indicators, Coverage gaps)
  Raw payload PURGED after extraction
        ↓
STAGE 3 — IN-MEMORY GENERATION
  Subgraph Context (Serialized metadata only, never raw code or text)
  LLM Generation (Operates on structured metadata)
        ↓
STAGE 4 — SELECTIVE PERSISTENCE
  ✅ STORED IN GRAPH: Node IDs and typed relationships,
     Risk scores, Trace matrices, Generated test metadata,
     Judge scores, Feedback events
  ❌ NEVER STORED: Source code, Full story text,
     Full PR description, Full incident description
```

### 12.2 What Is and Is Not Stored

| Data Type | Stored | Notes |
|-----------|--------|-------|
| Source code (raw) | ❌ Never | Only file paths and code symbol names |
| Story text (full) | ❌ Never | Only title and description summary (first 200 chars) |
| PR description (full) | ❌ Never | Only title and description summary |
| Incident description (full) | ❌ Never | Only description summary |
| Node IDs and relationships | ✅ Yes | The graph structure |
| Risk scores | ✅ Yes | Derived metrics only |
| Generated test cases | ✅ Yes | Full metadata including trace matrix |
| Judge scores | ✅ Yes | Evaluation results |
| Feedback events | ✅ Yes | Accept/Modify/Reject with timestamp |

This architecture means OrangePro can be deployed in environments with strict data residency requirements (SOC 2, ISO 27001, HIPAA) without requiring access to raw source code at rest.

---

## 13. Risk Scoring: Formula Derivation

### 13.1 GapPriority (Node-Level)

```
GapPriority = Impact × (1 - Coverage) × Time_Decay × Detection
```

**Impact** is derived from four graph signals:
- Story business priority (Jira priority field): CRITICAL=1.0, HIGH=0.8, MEDIUM=0.5, LOW=0.2
- Linked production incidents: each linked Incident adds 0.1 (capped at 0.5)
- Service criticality: CRITICAL=1.0, HIGH=0.8, MEDIUM=0.5, LOW=0.2
- Endpoint exposure: public-facing endpoints receive a 1.2 multiplier

**Coverage** is the ratio of AcceptanceCriterion nodes for the story that have at least one active, non-stale COVERS_CRITERION relationship to a TestCase.

**Time_Decay** is a decay function applied to historical risk signals:

```
Time_Decay = 1.0 - (days_since_last_incident / 365) × 0.5
```

Minimum value: 0.5 (historical incidents never decay to zero relevance).

**Detection** is inversely proportional to the quality of existing test coverage:

```
Detection = 1.0 - (active_test_count × avg_test_quality_score) / max_expected_tests
```

Where `avg_test_quality_score` is the average judge score of existing test cases for the story.

### 13.2 RiskScore (Test Case Level)

```
RiskScore = (Severity × Occurrence) / Detection × Coverage_Gap × Time_Decay
```

**Severity** — From linked Incident nodes: CRITICAL=1.0, HIGH=0.8, MEDIUM=0.5, LOW=0.2. If no linked incidents, defaults to the story's impact score.

**Occurrence** — From code churn on linked File nodes (lines changed in last 30 days), normalized to 0.0–1.0 range across the tenant.

**Detection** — Inversely proportional to the count and quality of TestCase nodes covering the linked stories. Low detection = high risk.

**Coverage_Gap** — Proportion of AcceptanceCriterion nodes for the story with no active COVERS_CRITERION relationship.

**Time_Decay** — Same formula as GapPriority.

---

## Appendix A — Cypher DDL (Indexes and Constraints)

```cypher
// Node uniqueness constraints
CREATE CONSTRAINT story_id IF NOT EXISTS FOR (s:Story) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT ac_id IF NOT EXISTS FOR (ac:AcceptanceCriterion) REQUIRE ac.id IS UNIQUE;
CREATE CONSTRAINT pr_id IF NOT EXISTS FOR (pr:PullRequest) REQUIRE pr.id IS UNIQUE;
CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE (f.path, f.repo) IS UNIQUE;
CREATE CONSTRAINT testfile_path IF NOT EXISTS FOR (tf:TestFile) REQUIRE (tf.path, tf.repo) IS UNIQUE;
CREATE CONSTRAINT testcase_id IF NOT EXISTS FOR (tc:TestCase) REQUIRE tc.id IS UNIQUE;
CREATE CONSTRAINT gen_testcase_id IF NOT EXISTS FOR (gtc:GeneratedTestCase) REQUIRE gtc.id IS UNIQUE;
CREATE CONSTRAINT gen_run_id IF NOT EXISTS FOR (gr:GenerationRun) REQUIRE gr.id IS UNIQUE;
CREATE CONSTRAINT coverage_cell_uid IF NOT EXISTS FOR (cc:CoverageCell) REQUIRE cc.uid IS UNIQUE;
CREATE CONSTRAINT endpoint_id IF NOT EXISTS FOR (e:Endpoint) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT service_id IF NOT EXISTS FOR (svc:Service) REQUIRE svc.id IS UNIQUE;
CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT capability_id IF NOT EXISTS FOR (cap:Capability) REQUIRE cap.id IS UNIQUE;

// Indexes for CQ performance
CREATE INDEX story_tenant IF NOT EXISTS FOR (s:Story) ON (s.tenant_id);
CREATE INDEX story_created IF NOT EXISTS FOR (s:Story) ON (s.created_at);
CREATE INDEX pr_tenant IF NOT EXISTS FOR (pr:PullRequest) ON (pr.tenant_id);
CREATE INDEX file_modified IF NOT EXISTS FOR (f:File) ON (f.last_modified);
CREATE INDEX incident_severity IF NOT EXISTS FOR (i:Incident) ON (i.severity);
CREATE INDEX coverage_cell_status IF NOT EXISTS FOR (cc:CoverageCell) ON (cc.status);
CREATE INDEX gen_run_status IF NOT EXISTS FOR (gr:GenerationRun) ON (gr.status);
```

---

## Appendix B — Proof Hub Validation Results

The OrangePro KG Proof Hub (https://orangepro-kg-proof-hub.onrender.com/) provides live evidence of the proof-kernel architecture in production:

| Metric | Value | Method |
|--------|-------|--------|
| Judged pairs | 51 | Baseline-vs-KG paired comparison |
| KG-preferred verdicts | 48/51 (94.1%) | Independent LLM judge |
| Baseline-preferred | 3/51 (5.9%) | — |
| Tenants validated | 3 (httpcore, FastAPI, Pydantic) | Public OSS repos |
| RQ-01 authorization | Bounded claim authorized | CQ-01 + CQ-03 correct |
| Proof-kernel relationships active | 18 | Gate-validated |
| SHACL gates passing | 4/4 | Application-layer enforcement |
| CoverageCell dispatch | Active | Per-cell generation with uid tracking |

---

## Appendix C — Seven-CQ Router Deferral

The current proof kernel operates with 5 deterministic competency questions. The full design calls for 7 CQs with a semantic router that dispatches incoming queries to the appropriate CQ based on intent classification.

The router is explicitly deferred — not missing. The decision rationale:

1. The 5 foundation CQs cover the critical proof path (coverage gap detection, traceability validation, regression evidence, cross-story dependency, incident-to-requirement mapping)
2. CQ-06 ("What is the blast radius of this code change?") and CQ-07 ("Which user flows are affected by this incident?") require the LINKED_TO cross-story relationship to be fully populated across tenants
3. The router itself requires intent classification that introduces a non-deterministic component — acceptable only after the deterministic foundation is proven stable

Deferral timeline: Post-foundation. The 5 CQs must demonstrate stable production results across 5+ tenants before the router is introduced. The router will use a deterministic dispatch table (not ML classification) for the first implementation, with semantic fallback only for ambiguous queries.

This is documented here to prevent the deferral from being interpreted as an architectural gap during due diligence. It is a sequencing decision, not a missing capability.

---

## Appendix D — Audit Pack and Freeze Protocol

Every governance-authorized claim is backed by a frozen evidence artifact that can be independently verified. The audit pack contains:

**Frozen Evidence Hash:**
```
SHA-256 of the aggregate evidence JSON at the moment of governance authorization.
If any packet is added, removed, or re-judged, the hash breaks and re-authorization is required.
```

**Replay Commands:**

Any authorized claim can be reproduced by replaying the exact judge configuration against the frozen packet set:

```bash
# Replay the RQ1 evidence for verification
orangepro-evidence replay \
  --evidence-hash <frozen_hash> \
  --judge-model gpt-4.1 \
  --calibration-set v2024-06 \
  --output-format json

# Verify aggregate matches authorized claim
orangepro-evidence verify \
  --evidence-hash <frozen_hash> \
  --expected-win-rate 0.941 \
  --expected-n 51 \
  --tolerance 0.001
```

**What the audit pack includes:**

| Artifact | Purpose |
|----------|--------|
| `evidence_aggregate.json` | Full per-pair verdicts with judge reasoning |
| `governance_row.json` | Authorization record: who, when, what hash, what claim template |
| `calibration_result.json` | Judge calibration scores against known-quality pairs |
| `mode_disclosure.json` | Per-pair retrieval_provider_mode breakdown |
| `phase_c_attribution.json` | Graphlit A/B results for the attribution question |
| `tenant_manifest.json` | Tenant identities, packet counts, date ranges |
| `baseline_prompt.txt` | The exact baseline prompt used (proving it is not a strawman) |
| `kg_prompt_template.txt` | The KG-enriched prompt template (proving what context was added) |

**Freeze Protocol:**

1. Evidence bridge emits aggregate state
2. Human reviews and determines `safe_to_present` status
3. If authorizing: SHA-256 hash is computed over the aggregate JSON
4. Governance row is created with: hash, claim template, authorizer, timestamp
5. The evidence JSON is frozen — no mutations allowed without breaking the hash
6. Any subsequent change (new packets, new judge, new tenants) creates a new aggregate that requires fresh authorization

The freeze protocol ensures that the 94.1% number presented today is the same 94.1% that was measured, not a number that has drifted through incremental additions. This is the difference between "our system says 94.1%" and "here is the cryptographically frozen evidence artifact proving 94.1% at this specific point in time."

---

## Appendix E — Architecture Evolution Log

This appendix documents the natural evolution of the knowledge graph architecture for engineering due diligence purposes.

### The Deterministic Proof Kernel Evolution

The knowledge graph architecture evolved through a natural engineering maturation process. The original design used confidence scores throughout the graph traversal path. As the system scaled, a formal ontology review (conducted by M. Bilal Ashfaq, TU Wien) identified the fundamental weakness: probabilistic multi-hop traversal produces exponential error propagation.

The engineering team executed a disciplined architectural reset, restructuring the graph around a deterministic proof kernel using Bilal's 5-pillar framework. The key changes:

- Confidence scores removed from the proof path entirely
- Three epistemic tiers introduced (proof, candidate, weak) replacing a binary threshold model
- Proof-kernel relationships bounded to 18 (from a larger, less disciplined set)
- SHACL-equivalent gates enforced at write time, not advisory
- QEFix taxonomy expanded from 8 to 16 categories based on empirical dispatch requirements

### Why This Matters for Due Diligence

This evolution demonstrates:

- **Self-awareness:** The team identified the weakness through formal internal review, not customer failure
- **Engineering rigor:** The fix was architectural (redesign the proof model) rather than tactical (tune thresholds)
- **External validation:** The reset was guided by a formal ontology expert with academic credentials (TU Wien)
- **Bounded claims culture:** The team chose to reduce the system's claim surface rather than ship probabilistic results

The deterministic proof kernel is now the foundational architectural commitment.

---

## Appendix F — Document Revision History

| Version | Key Changes |
|---------|-------------|
| v2 | Initial KG specification. Hybrid ontology with confidence thresholds throughout the graph. Linking Engine as named component. Probabilistic multi-hop traversal. Companion to Architecture Document v6. |
| v3.0 | Complete architectural reset to deterministic proof kernel. Confidence removed from proof path (exists only at intake boundary). Three epistemic tiers (proof, candidate, weak). 18 bounded proof-kernel relationships. SHACL-equivalent validation gates. Competency questions with Cypher evidence. CoverageCell dispatch mechanism. 4 appendices (Cypher DDL, Proof Hub Results, Seven-CQ Router Deferral, Audit Pack). |
| v3.1 | Added Privacy-First Pipeline technical detail. Added Risk Scoring formula derivation. Added Architecture Evolution Log appendix. Upgraded to full branded format with cover page. Removed version history from main body. |
| v3.2 | Confirmed 24 core ontology node labels with 3-tier taxonomy (core, operational, proprietary). Added missing node schemas (Tenant, JiraTicket, APIContract, Team, RepairContract, RepairOutcome, OutcomeEvent). Removed all date references. Present-tense narrative throughout. |

---

*End of document.*
