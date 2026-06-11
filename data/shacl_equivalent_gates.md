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
