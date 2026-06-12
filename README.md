# Reproducibility Package: Ontology-Governed Test Generation

**Paper:** Ontology-Governed Test Generation: A Neo4j-Native Approach to Shape-Validated Knowledge Graphs for Enterprise QA

**Authors:** Aamir Siddiqui, Vaibhav Shrivastava, M. Bilal Ashfaq

**Venue:** ISWC 2026 Industry Track

**Zenodo DOI:** 10.5281/zenodo.20634981

## Package Contents

### /data/

| File | Description |
|------|-------------|
| `verdicts_51pairs.json` | Full 51 judged pairs across 3 tenants (HTTP Core, Airflow, Click) with test bodies, judge scores, and verdicts |
| `verdicts_calibration_24pairs.json` | 24-pair calibration subset (HTTP Core tenant) used for judge calibration |
| `zenodo_bundle.json` | Complete reproducibility bundle with source commits and SHA256 hashes |
| `baseline_pinned.json` | Pinned baseline metrics definition |
| `baseline_prompt_template.txt` | The structured baseline prompt used to generate comparison tests (without KG context) |
| `judge_scoring_prompt.txt` | Exact scoring rubric and prompt given to LLM judges for evaluation |
| `competency_questions_cypher.md` | 5 deterministic Competency Questions with full Cypher implementations |
| `18_proof_kernel_relationships.md` | Full specification of the 18 proof-kernel relationships |
| `shacl_equivalent_gates.md` | 4 SHACL-equivalent validation gate specifications |
| `proof_hub_judged_pairs_metadata.md` | Proof Hub aggregate judged pairs metadata |
| `proof_hub_overview.md` | Proof Hub aggregate statistics overview |

### /scripts/

| File | Description |
|------|-------------|
| `reproduce_results.py` | Replication script: loads verdicts JSON and computes the 94.1% win rate |
| `llm_judge.py` | LLM judge service implementation |
| `calibrate_judge.py` | Judge calibration script |

### /docs/

| File | Description |
|------|-------------|
| `KG_Specification_v3.md` | Full KG specification (24 node labels, 18 relationships, gates, CQs) |
| `judge_calibration_plan.md` | Judge calibration methodology |
| `baseline_pinning_review.md` | How the baseline was defined and pinned |

---

## Replication Instructions

### Prerequisites

- Python 3.10+ (standard library only — no additional packages required)
- No Neo4j access required — all graph evidence is frozen in the verdicts JSON
- **LLM API key is NOT required** for the main replication command below. An LLM API (GPT-4.1, Claude 3.5 Sonnet, or Gemini 2.5 Pro) is only needed if you want to re-run the judge scoring from scratch (see "Steps to Replicate Judge Scoring" below)

### Steps to Reproduce the 94.1% Result

```bash
python scripts/reproduce_results.py --input data/verdicts_51pairs.json
```

Expected output: `KG win rate: 48/51 = 94.12%`

### Manual Verification

1. Load `data/verdicts_51pairs.json`
2. For each pair, check `kg_preferred == true`
3. Compute: `win_rate = kg_preferred_count / total_pairs`
4. Expected: 48/51 = 94.1%

### Steps to Replicate Judge Scoring (Optional)

This is an optional methodology audit. It does not change the 94.1% result — that is already verified by `reproduce_results.py` above.

**Step 1 — Generate the judge prompt:**

```bash
# For the calibration set (24 pairs — recommended starting point):
python scripts/generate_judge_prompt.py --input data/verdicts_calibration_24pairs.json --output judge_prompt.txt

# For the full evaluation set (51 pairs):
python scripts/generate_judge_prompt.py --input data/verdicts_51pairs.json --output judge_prompt.txt
``
---
## Note on LLM Stochasticity and Reproducibility

LLM judges are stochastic by nature. Even with `temperature=0`, exact verdict replication is not guaranteed across model versions, API updates, or provider-side changes. This is expected and by design.

The primary reproducibility claim of this paper is not “run the judge and get exactly 48/51” — it is: the frozen verdict dataset is publicly available, SHA256-hashed, and independently verifiable. The 94.1% figure is a fact about that specific frozen dataset, not a live benchmark.

The `reproduce_results.py` script reads the pre-computed verdicts directly from `verdicts_51pairs.json` without making any LLM API calls. This is the correct replication path.

If you choose to re-run the judge scoring using `llm_judge.py`, treat it as a methodology audit — you are verifying that the rubric and prompt produce qualitatively similar preferences, not that you will recover exactly 48 wins. Minor variance (±2 pairs) is expected and acceptable given LLM stochasticity. The calibration artifact (`verdicts_calibration_24pairs.json`) provides a reference subset for this purpose.

This approach follows established practice in LLM evaluation research, where frozen evaluation sets with cryptographic hashes serve as the reproducibility anchor.


---

## Schema Summary

| Component | Count |
|-----------|-------|
| Node Labels (core ontology) | 24 |
| Node Labels (operational) | 12 |
| Proof-Kernel Relationships | 18 |
| Epistemic Tiers | 3 (Proof → Candidate → Weak) |
| Validation Gates | 4 |
| Competency Questions | 5 |
| QEFix Taxonomy Buckets | 16 |

---

## Evaluation Summary

| Metric | Value |
|--------|-------|
| Total judged pairs | 51 |
| KG-preferred verdicts | 48 |
| Baseline-preferred verdicts | 3 |
| KG win rate | **94.1%** |
| Tenants evaluated | 3 (HTTP Core, Airflow, Click) |

---

## License

Data: CC-BY-4.0 | Code: Apache-2.0

---

## Citation

```bibtex
@inproceedings{siddiqui2026ontology,
  title={Ontology-Governed Test Generation: A Neo4j-Native Approach to Shape-Validated Knowledge Graphs for Enterprise QA},
  author={Siddiqui, Aamir and Shrivastava, Vaibhav and Ashfaq, M. Bilal},
  booktitle={Proceedings of the International Semantic Web Conference (ISWC), Industry Track},
  year={2026},
  publisher={Springer},
  doi={10.5281/zenodo.20634981}
}
```
