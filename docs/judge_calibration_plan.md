# Judge Calibration Plan

## Purpose

This plan defines the minimum calibration work required before the provider-backed LLM judge can be cited as reliable measurement infrastructure in:

- provisional patent evidence packages
- diligence reviews
- production-grade internal quality claims

The goal is not to prove that the judge is universally correct. The goal is to prove that each provider agrees with blinded human labels often enough to be trusted as a comparative measurement tool for OrangePro's matched-pair test evaluation workflow.

## Scope

Calibration covers:

- per-provider agreement rate with blinded human labels
- the current judge providers:
  - OpenAI
  - Anthropic
- the current matched-pair evaluation shape:
  - one KG-generated option
  - one baseline option
  - one winner label:
    - `A`
    - `B`
    - `tie`

Calibration does not cover:

- proving absolute testcase quality across all future domains
- replacing human QA signoff
- proving the downstream EWGG or shape-signature claims
- token-cost benchmarking

## Why This Exists

The provider-backed judge is measurement infrastructure, not the moat itself.

Without calibration, the system can say:

- "the provider returned verdicts"

It cannot yet say:

- "the provider is trustworthy enough for us to cite its verdicts as evidence"

Calibration closes that gap.

## Gold Set Design

### Minimum Viable Set

- `20` blinded human-labeled pairs
- source tenant:
  - BeautyCo

This is the minimum acceptable set for first-pass calibration and internal branch confidence.

### Target Set

- `50` blinded human-labeled pairs
- source tenants:
  - BeautyCo
  - FreightFlow

This is the preferred set before citing provider-backed judge numbers in external diligence or patent-supporting evidence.

### Pair Composition Rules

The gold set should include a mix of:

- clear KG wins
- clear baseline wins
- plausible ties
- functional buckets
- edge-case buckets
- integration buckets
- security buckets where available

Avoid a gold set made only of easy wins. The set must include borderline cases so agreement rates mean something.

### File Location

Planned location:

- `evals/judge_calibration/beautyco-judge-gold.json`
- `evals/judge_calibration/beautyco-freightflow-judge-gold.json`

### Suggested Gold Record Shape

Each item should capture:

- `pair_uid`
- `packet_title`
- `story_text`
- `acceptance_criteria`
- `bucket_name`
- `option_a_title`
- `option_a_body`
- `option_b_title`
- `option_b_body`
- `human_winner`
- `human_labeler`
- `human_rationale_short`
- `labeled_at`

Critical rule:

- the gold set must never include fields the judge does not see
- do not store tenant ids, repo ids, KG-side labels, or source-side labels in the runtime gold packet

If adjudication metadata is needed, keep it in a separate reviewer log, not in the blinded gold packet that the calibration runner consumes.

## Labeling Protocol

### Human Labeling Mode

Labeling must be blinded.

That means the human labeler sees:

- `Option A`
- `Option B`
- the story text
- acceptance criteria
- bucket context

The labeler must not see:

- which side is KG
- tenant scoring internals
- prior provider verdicts
- model/provider identity

### Labelers

Recommended MVP:

- `2` human labelers for each pair

Preferred:

- one product/QA-aligned reviewer
- one engineering reviewer

### Resolution Rule

If both labelers agree:

- that label becomes the gold verdict

If labelers disagree:

- send the pair to a third adjudicator
- adjudicator reviews the same blinded packet
- adjudicator sets the final gold verdict
- disagreement and adjudication notes are persisted

### What Counts As Blinded Human Labeling

Blinded human labeling means:

- the labeler is evaluating only the content quality of the two options
- the labeler does not know which option came from KG
- the labeler does not know which model/provider later judged the same pair
- the labeler does not see system-generated metadata that could reveal source identity

If any of those are violated, the pair must not be counted in the calibration gold set.

## Agreement Metric

### MVP Metric

Use:

- simple agreement rate

Formula:

- `agreement_rate = matching_gold_verdicts / total_pairs`

Why this is the MVP choice:

- easy to explain
- easy to audit
- sufficient at `N=20-50`
- appropriate for a first calibration pass

### Deferred Metric

For the non-provisional or later diligence work, add:

- Cohen's kappa

Reason:

- kappa is better for correcting for chance agreement
- but it adds explanation overhead that is unnecessary for the MVP branch milestone

Current decision:

- MVP uses simple agreement rate
- kappa is deferred to the next calibration maturity pass

## Pass Threshold

Per-provider pass threshold:

- `75%` agreement with human gold labels

This threshold applies independently to:

- OpenAI
- Anthropic

The deterministic rubric provider is not the target of this calibration threshold. It exists as an internal baseline and fallback, not as the judge we intend to cite externally.

## Failure Mode

If a provider falls below `75%` agreement:

- mark the provider as unreliable in `docs/operations/kg-llm-judge-readiness-checklist.md`
- do not cite that provider's verdict-derived results in the provisional package
- do not present that provider as diligence-grade measurement infrastructure
- document the gap and likely failure pattern
- keep the provider available only for internal experimentation unless a product decision explicitly says otherwise

Examples of likely failure pattern buckets to document:

- too many false KG wins
- too many false baseline wins
- excessive tie rates
- weak performance on security or integration buckets
- weak performance on long acceptance-criteria packets

## Deliverables

The calibration workstream should produce:

1. gold calibration set JSON
2. calibration runner script:
   - `scripts/calibrate_judge.py`
3. provider agreement report with:
   - total pairs
   - agreement rate
   - disagreement count
   - tie handling summary
4. readiness checklist update
5. branch state update in `.paul/STATE.md`

## Output Expectations

The calibration runner should report, per provider:

- provider name
- model
- total evaluated pairs
- agreement rate
- number of mismatches
- tie count
- below-threshold flag

It should also produce a final outcome:

- `calibrated`
- `partially_calibrated`
- `not_calibrated`

## Non-Goals

This plan does not require:

- production UI work
- CI integration
- token-accurate billing
- multi-label rubric scoring by humans
- claim-language changes in `docs/ip-proof/05-DRAFT-CLAIM-LANGUAGE.md`

## Current Branch Gate

As of this plan:

- provider-backed judge infrastructure exists
- audit durability exists
- drift protection exists
- reproducibility seed exists
- cost guardrails exist
- calibration is the last major judge reliability gap before the judge can be cited as dependable measurement infrastructure

## Exit Criteria

This plan is complete when:

- at least one gold set with `>= 20` blinded human-labeled pairs exists
- `scripts/calibrate_judge.py` runs against the gold set
- OpenAI and Anthropic each report agreement against the gold set
- each provider is explicitly marked pass/fail against the `75%` threshold
- readiness checklist reflects the calibration result
- `.paul/STATE.md` records the outcome and remaining gaps, if any
