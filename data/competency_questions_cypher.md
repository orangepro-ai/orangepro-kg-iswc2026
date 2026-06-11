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
