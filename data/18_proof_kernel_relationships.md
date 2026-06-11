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
