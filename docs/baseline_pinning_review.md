# Review — commit `6d93795` — Pre-Phase-23 Grounding Baseline Pinning

**Date:** 2026-04-11
**Reviewer:** Terminal A (review mode)
**Branch:** `feature/18-01-hybrid-retrieval-resolution`
**Commit category:** measurement infrastructure (fixture), not patent-bearing
**Companion commit under review:** `745f918 docs(ip): log deterministic baseline pinning`

---

## Round 1

### Commits under review

| SHA | Type | Scope |
|---|---|---|
| `6d93795` | `docs(eval)` | engineering artifact: `evals/baselines/pinned.json`, readiness checklist addendum, `.paul/STATE.md` state bullet |
| `745f918` | `docs(ip)` | ledger-only: adds row `16c` dashboard entry, appends new per-commit ledger entry, updates summary arithmetic from 25 → 26 |

Review posture note: this is the first adversarial review on a **baseline fixture** (not an evaluator), so the standard 8-point measurement-infrastructure checklist has been adapted. Four checks are out of scope, four apply with modified wording, and four new fixture-specific checks are added (F1–F4).

### What the commits actually add

- `evals/baselines/pinned.json` — new 52-line fixture. Contains `last_updated`, `measurement_source_commit`, `baseline_type`, three-bullet `notes`, and a `pinned` block with two packs:
  - `beautyco-max-core`: `top1_accuracy`, `top3_accuracy`, `service_recall`, `incident_recall`, `historical_test_recall`, `avg_top1_confidence`
  - `beautyco-max-broad`: `top1_accuracy`, `top3_accuracy`, `avg_top1_confidence`
  - Each metric has `value` and `tolerance`.
- `docs/operations/kg-llm-judge-readiness-checklist.md` — adds a new "Pre-Phase-23 Grounding Floor" paragraph with a three-bullet warning that the floor is grounding, not judge calibration.
- `.paul/STATE.md` — updates "Last activity" line and adds a new bullet block under the Stage 3 judge section recording the grounding-floor pin.
- `docs/ip-proof/07-CAPABILITY-LEDGER.md` (via `745f918`) — adds row `16c` in the dashboard table, appends a new per-commit ledger entry dated 2026-04-11, updates summary counts from `25 total / 16 PROVEN` to `26 total / 17 PROVEN`, and updates the "Next entry expected" tail note.

### Adapted checklist

| # | Original check (from REVIEW-TERMINAL-HANDOFF §4) | Applies? | Result |
|---|---|---|---|
| 1 | Blinding | OUT OF SCOPE | A fixture cannot cheat on labels. |
| 2 | Tie / null handling | APPLIES (adapted) | PARTIAL — see Finding 3. |
| 3 | Multi-provider schema | OUT OF SCOPE | No provider involved. |
| 4 | Drift detection | APPLIES (critical) | PARTIAL — see Finding 2. |
| 5 | Cost and rate limit | OUT OF SCOPE | No API calls. |
| 6 | Reproducibility seed | APPLIES (adapted) | subsumed into Finding 2. |
| 7 | Verdict durability | APPLIES | PASS — file committed, parses cleanly. |
| 8 | Judge-of-judges calibration | OUT OF SCOPE | Not a judge. |

| # | New fixture-specific check | Result |
|---|---|---|
| F1 | Scope labeling / disclosure discipline | PASS. |
| F2 | Schema alignment with runner output | sanity-PASS on metric names; incomplete on shape semantics — see Finding 3. |
| F3 | Consumer or enforcer wired to the fixture | **MISSING (MEDIUM)** — see Finding 1. |
| F4 | Tolerance semantics and suspicious values | PARTIAL — see Finding 4. |

### Findings

#### Finding 1 — MEDIUM — No consumer or enforcer reads `pinned.json` (check F3)

**Evidence:**

- `grep -r "pinned.json\|baselines/pinned" --include="*.py"` on the full tree returns zero matches.
- `grep -r "pinned\|baselines" tests/` returns zero matches.
- No `.github/` or CI references to the file.
- `scripts/eval_grounding_pack.py` does not import `pinned.json`, does not load it, and does not compare its output against it.
- `app/services/grounding_eval.py::GroundingEvalService.evaluate_pack` produces a metrics dict but has no symmetric "assert within pinned tolerance" counterpart.

**Impact:** The fixture exists on disk and parses cleanly, but nothing on this branch reads it. A regression in `app/services/grounding_resolution.py` that pushes `beautyco-max-core top1_accuracy` from `1.0` to `0.8` would not fail any test, gate, or commit hook. The "floor" is aspirational documentation, not an enforced gate. This is the single biggest gap in the commit.

**Why this is Medium, not High:** the commit is correctly labeled as a `docs(eval)` commit and the artifact is honest about what it is. The failure mode is not "overclaim in code" — it is "ledger state overclaim" (see Finding 5). An engineer who reads the file and runs a pack by hand can still compare manually. The capability is delivered as a file, just not as an enforced floor.

**Recommended fix (small engineering task, Codex-owned):**

- Add a new script — `scripts/check_grounding_baselines.py` — that:
  1. Loads `evals/baselines/pinned.json`.
  2. For each pack listed under `pinned`, runs the same evaluation path `scripts/eval_grounding_pack.py` uses (via `GroundingEvalService.evaluate_pack`).
  3. For each pinned metric, loads the runner value and asserts `|runner_value - pinned_value| <= tolerance` (semantics per Finding 4).
  4. Exits non-zero on any regression, logs a table of pinned vs actual vs delta.
- Add a pytest wrapper — `tests/test_grounding_baselines.py` — that marks the regression check as a pytest marker so it can be opted into or skipped in a local-only Neo4j context.
- Document the enforcer location in `docs/operations/kg-llm-judge-readiness-checklist.md` immediately under the new "Pre-Phase-23 Grounding Floor" paragraph.
- Effort: ~1–2 hours. Not blocking for Phase 23 Slice A kickoff, but should land before Phase 23 Slice B so any shape-signature-driven drift is caught.

#### Finding 2 — MEDIUM — Drift protection: no environment capture in `pinned.json` (check #4)

**Evidence:** `pinned.json` records `measurement_source_commit: af3c7af` and `last_updated: 2026-04-11`, which is good intent. It does not record:

- Neo4j server version or Docker image tag used to produce the measurements.
- Tenant ingestion source: which `beautyco-max-seed` snapshot was loaded, what synthetic or curated state the graph was in at measurement time.
- Python runtime version or `requirements.txt` lockfile hash.
- The commit SHA of `scripts/eval_grounding_pack.py` and `app/services/grounding_eval.py` at measurement time — `measurement_source_commit: af3c7af` is a proxy but does not identify which files it refers to.
- The content hash or commit SHA of the grounding pack files themselves. If `evals/grounding/beautyco-max-core.json` or `evals/grounding/beautyco-max-broad.json` is edited later without re-pinning, the pinned numbers silently refer to a different pack.

**Impact:** A re-measurement on a different day, a different workstation, or a different Neo4j snapshot will produce deltas that cannot be distinguished between:

- code drift (grounding resolver changed),
- data drift (tenant graph state changed),
- environment drift (Neo4j or dependency version changed), or
- pack drift (the input pack file itself was edited).

For a "regression floor" in the audit sense used in `docs/ip-proof/`, this distinction is load-bearing. A DD reviewer asked "how do you know these numbers are reproducible?" cannot answer from `pinned.json` alone today.

**Recommended fix (small, fixture-only, Codex-owned):**

Extend `pinned.json` with a `measurement_environment` block. Illustrative shape:

```json
"measurement_environment": {
  "measurement_source_commit": "af3c7af",
  "measured_at_utc": "2026-04-11T08:01:45Z",
  "pinned_by": "Codex",
  "neo4j_image": "neo4j:5.x-community",
  "tenant_ingest_source": "beautyco-max-seed",
  "tenant_ingest_sha": "<git-sha-or-dir-hash>",
  "pack_hashes": {
    "beautyco-max-core": "<sha256 of evals/grounding/beautyco-max-core.json>",
    "beautyco-max-broad": "<sha256 of evals/grounding/beautyco-max-broad.json>"
  },
  "python": "3.11.x"
}
```

The enforcer from Finding 1 should warn (not hard-fail) on environment drift, and should hard-fail on pack-hash drift without an explicit re-pin. This preserves reproducibility in the audit sense without making the enforcer brittle.

#### Finding 3 — LOW — Null handling is correctly implemented in the runner but not reflected in the fixture schema (check #2)

**Evidence:** `app/services/grounding_eval.py` lines 73–80 return `None` for `service_recall`, `incident_recall`, and `historical_test_recall` when the pack has zero cases expecting that dimension:

```python
"service_recall": round(service_hits / service_cases, 4) if service_cases else None,
```

`beautyco-max-broad` in `pinned.json` does not pin these three metrics — this is internally consistent with the runner behavior because the broad pack has no `expected_services` / `expected_incident_terms` / `expected_test_terms` on any case. The omission is correct.

**Gap:** `pinned.json` silently allows a metric to be absent and treats that as "do not check." There is no explicit `intentionally_unpinned` array or comment that distinguishes "we measured it and it was None" from "we forgot to pin it" from "this metric is deliberately excluded for this pack." Silent baseline accretion drift is possible — if a future iteration of `beautyco-max-broad.json` adds `expected_services` to some cases, `service_recall` becomes a real number in the runner output but no pinned entry exists to catch regressions on it.

**Impact:** Low. The runner returns valid values today and the omission is consistent. The gap is latent, not active. It becomes relevant when Phase 23 extends the packs or when shape-signature scoring adds new metrics that need to be pinned.

**Recommended fix (tiny, Codex-owned):**

- Add an `intentionally_unpinned` array per pack in `pinned.json` listing metrics that are deliberately excluded, with a one-line reason per entry:

```json
"beautyco-max-broad": {
  "top1_accuracy": { "value": 1.0, "tolerance": 0.0 },
  "top3_accuracy": { "value": 1.0, "tolerance": 0.0 },
  "avg_top1_confidence": { "value": 0.9422, "tolerance": 0.01 },
  "intentionally_unpinned": [
    { "metric": "service_recall", "reason": "broad pack has no service expectations" },
    { "metric": "incident_recall", "reason": "broad pack has no incident expectations" },
    { "metric": "historical_test_recall", "reason": "broad pack has no test expectations" }
  ]
}
```

- The enforcer from Finding 1 should flag any runner metric that is neither in `pinned` nor in `intentionally_unpinned`.
- Effort: ~15 minutes.

#### Finding 4 — LOW — Tolerance semantics undefined; one pinned value is mathematically degenerate (check F4)

**Evidence:**

1. `beautyco-max-core.avg_top1_confidence = {"value": 1.0, "tolerance": 0.01}`. The runner computes `confidence_total / total` rounded to 4 decimals. For this value to be exactly `1.0`, every case in `beautyco-max-core` must currently return `top1_confidence = 1.0`. If the resolver scorer caps confidence at `1.0`, upward drift is mathematically impossible, so `tolerance: 0.01` is asymmetric by construction — only downward drift is meaningful.
2. `top1_accuracy`, `top3_accuracy`, `service_recall`, `incident_recall`, `historical_test_recall` all use `tolerance: 0.0`. A tolerance of exactly zero on a floating-point `round(..., 4)` value is brittle: any tie-breaker change in the resolver that shifts a single case by one rank will read as a regression, even if overall quality is unchanged.
3. There is no top-level `tolerance_semantics` field in `pinned.json`. Whether `tolerance: 0.01` means `|current - pinned| <= 0.01` (symmetric absolute) or `current >= pinned - 0.01` (one-sided lower bound) is undefined. An enforcer cannot be written unambiguously today.
4. The saturated values on the core pack (`top1 = 1.0`, `top3 = 1.0`, `historical_test_recall = 1.0`, `avg_top1_confidence = 1.0`) mean the curated pack currently has no discriminatory power at the top of the range. This is not a regression but is worth flagging for the Phase 23 plan: shape-signature lift on a saturated curated pack is not measurable at the top metric. The broader pack (`avg_top1_confidence = 0.9422`) still has headroom.

**Impact:** Low for the commit itself — the values are factually correct measurements and the commit does not claim they mean anything more than "these are today's numbers." The finding matters for the enforcer (Finding 1) and for the Phase 23 measurement posture (any lift claim that says "shape signature moved X from 1.0 to 1.0" is not a valid lift claim).

**Recommended fix (tiny, Codex-owned):**

- Add a top-level `tolerance_semantics` field to `pinned.json`: `"tolerance_semantics": "absolute_symmetric"` (or `"one_sided_lower_bound"` if that becomes the preferred semantics).
- For the saturated `avg_top1_confidence = 1.0` on `beautyco-max-core`, explicitly document the one-sided interpretation in the `notes` array.
- In the Phase 23 plan (`.paul/phases/23-predicted-shape-signature-extractor/23-01-PLAN.md`, when review lands), include a "baseline discriminatory power" check — any claim of shape-signature lift must be measured against a pack with headroom, not against `beautyco-max-core` at saturation.

#### Finding 5 — MEDIUM — Capability ledger row `16c` at 🟢 PROVEN overclaims the capability (check F3 tie-in)

**Evidence:** `docs/ip-proof/07-CAPABILITY-LEDGER.md` row 16c as committed in `745f918`:

```
| 16c | Pre-Phase-23 deterministic grounding baselines pinned | 🟢 PROVEN
  | `evals/baselines/pinned.json` with current BeautyCo core/broad metrics re-measured on this branch | `6d93795` |
```

The ledger legend (lines 29–41 of the ledger) defines 🟢 PROVEN as:

> Implemented, tested with real tests, evidence attached, verifiable by re-running on this branch.

And the honesty rule:

> never upgrade a state without new evidence on this branch. If a capability regresses, add a new dated entry that corrects the record. Never mutate prior entries.

The capability name is "baselines *pinned*." On a strict reading, a pinned fixture simply exists, which is true. On the reading implied by neighboring rows — all of which (10–16a) are backed by pytest tests that verify the capability works when invoked — row 16c is not of that kind. There is no test, no enforcer, and no automated invocation. The fixture is inert.

Per REVIEW-TERMINAL-HANDOFF §8 rule 5 ("Never overclaim state") and rule 6 ("Append-only ledger entries"), the correct posture is:

1. Do not mutate the existing row 16c or the existing 2026-04-11 ledger entry. They stand as the Codex record.
2. Append a new dated entry that corrects the record by splitting row 16c into two sub-rows, the same pattern used for row 16 → 16a/16b after Round 4 of the judge review.
3. Specifically:
   - **Row 16c-i — Pre-Phase-23 deterministic grounding baseline fixture** — 🟢 PROVEN. Evidence: `evals/baselines/pinned.json` parses cleanly, measurement values match `scripts/eval_grounding_pack.py` output on local Neo4j as of `6d93795`.
   - **Row 16c-ii — Grounding baseline regression enforcement** — 🔴 NOT STARTED. No enforcer reads `pinned.json`; no test asserts pinned tolerance; no CI gate blocks regression. Blocking work is the small enforcer described in Finding 1.

**Impact:** Medium — this is the exact overclaim pattern the honesty rule was written to prevent. The fix is an append-only ledger update that costs nothing and preserves the integrity of the running dashboard for counsel and DD.

**Recommended fix (this review round):**

Append a new ledger entry dated `2026-04-11 — review round 1 correction on 6d93795` describing the split. Update the dashboard summary arithmetic from `26 total / 17 PROVEN-or-STRUCTURAL-PROVEN / 1 PARTIAL / 8 NOT STARTED` to `27 total / 17 PROVEN-or-STRUCTURAL-PROVEN / 1 PARTIAL / 9 NOT STARTED`. Do not mutate the prior 2026-04-11 entry on `6d93795` — the split is expressed as a new append.

### Positive drift — what Codex delivered beyond the ask

1. **Scope labeling discipline is exemplary.** Four independent surfaces all carry the same message — `baseline_type: pre_phase_23_deterministic_grounding_floor` in `pinned.json`, the three-bullet `notes` array, the readiness-checklist warning paragraph, the STATE.md bullet, and the ledger entry's "Not patent-bearing. Measurement infrastructure only." line. A DD reader cannot accidentally confuse this fixture with a judge-calibration claim. This is the strongest disclosure posture in any single commit on this branch so far.

2. **Two-commit split preserves territory.** `6d93795` (engineering artifact) and `745f918` (ledger entry) are cleanly separated — Codex wrote the engineering side, the ledger entry followed. This matches the review-terminal / engineering-terminal lane discipline and keeps the audit trail clean for counsel.

3. **`measurement_source_commit: af3c7af` is the correct reproducibility marker.** The pinning commit is `6d93795`, but the measurements were taken while the code was at `af3c7af`. Recording the state-at-measurement rather than the state-at-pin is the honest thing to do and matches the drift-protection intent of the judge review Round 2 `system_fingerprint` pattern.

4. **Readiness checklist integration is append-only.** The existing "limitations" section was not mutated — the new grounding-floor paragraph is appended immediately below, so the prior limitations (calibration threshold, gold-set expansion blocked) are not diluted.

5. **STATE.md update is internally consistent.** The "Last activity" line and the new Stage 3 block bullet are aligned with the commit scope and correctly distinguish the grounding floor from the judge-calibration blocker above it.

### Verdict

**Commit is factually clean and disclosure-safe.** The fixture, the readiness-checklist addendum, and the STATE.md update are all correct and well-scoped. The review findings are concentrated in two places:

1. **Ledger state overclaim** (Finding 5) — correctable in this review round by an append-only ledger split. This is the only finding that this review round will fix.
2. **Enforcer + environment + tolerance semantics gap** (Findings 1, 2, 4) — all small engineering tasks that Codex can resolve in a single follow-up commit before Phase 23 Slice B. Finding 3 is a 15-minute follow-up.

**Is this a blocker for Phase 23 Slice A?** No. The baseline fixture is complete enough to serve as a directional floor. Slice A can proceed in parallel. The enforcer should land before Slice B so that any shape-signature-driven regression is caught automatically.

**Is this a blocker for counsel or DD?** No. The disclosure discipline is strong. The only concern a DD reviewer might raise is "how do you know these numbers are reproducible?" — which is addressable by the environment-capture fix in Finding 2 during normal follow-up work.

### Round 1 summary table

| Check | Scope | Result |
|---|---|---|
| #1 Blinding | OUT OF SCOPE | — |
| #2 Tie / null handling | APPLIES | PARTIAL (Finding 3, LOW) |
| #3 Multi-provider schema | OUT OF SCOPE | — |
| #4 Drift detection | APPLIES | PARTIAL (Finding 2, MEDIUM) |
| #5 Cost and rate limit | OUT OF SCOPE | — |
| #6 Reproducibility seed | APPLIES | subsumed into Finding 2 |
| #7 Durability | APPLIES | PASS |
| #8 Calibration | OUT OF SCOPE | — |
| F1 Scope labeling | NEW | PASS |
| F2 Schema alignment | NEW | PASS (names match) |
| F3 Consumer / enforcer | NEW | **MISSING (Finding 1, MEDIUM)** |
| F4 Tolerance semantics | NEW | PARTIAL (Finding 4, LOW) |
| Ledger state accuracy | NEW | **OVERCLAIM (Finding 5, MEDIUM)** |

**Round verdict:** Commit accepted as-is. Ledger correction applied in the same docs commit as this review file. Three follow-up items handed back to Codex for a single consolidated `docs(eval)` or `feat(eval)` commit before Phase 23 Slice B:

1. Add `scripts/check_grounding_baselines.py` + `tests/test_grounding_baselines.py` enforcer (Finding 1).
2. Extend `pinned.json` with `measurement_environment`, `tolerance_semantics`, and `intentionally_unpinned` fields (Findings 2, 3, 4).
3. Document the enforcer in `docs/operations/kg-llm-judge-readiness-checklist.md`.

### Next expected review target

Phase 23 Slice A — `ShapeSignature` contract in `app/models/nodes.py`. When that commit lands, this review file is not reopened; a new file `docs/ip-proof/reviews/<date>-phase-23-slice-a-review.md` will be created with the **patent-bearing checklist** instead of the measurement-infrastructure checklist, mapping the commit against Claim Family A in `docs/ip-proof/05-DRAFT-CLAIM-LANGUAGE.md`.

---

*Review file created: 2026-04-11*
*Reviewer: Terminal A*
*File author role: adversarial reviewer, not engineer, not teacher*
*Review SOP reference: `docs/ip-proof/REVIEW-TERMINAL-HANDOFF.md` §9*
