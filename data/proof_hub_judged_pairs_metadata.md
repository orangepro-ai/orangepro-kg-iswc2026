# All 51 Judged Pairs

**URL:** https://orangepro-kg-proof-hub.onrender.com/judged-pairs/

---

Proof hub / All judged pairs
All 51 Judged Pairs

Static rendering of every baseline-vs-KG verdict behind the public 94.1% aggregate: complete test bodies, judge winner, confidence, rationale, and all eight rubric dimensions.

KG WIN RATE
94.1%
KG WINS
48 / 51
JUDGED PAIRS
51
PACKETS
9
TENANTS
3
BASELINE WINS
3

Strong-baseline caveat. The baseline is not a weak "write some tests" prompt. It is already a product-shaped, vertical prompt with story context, app overview, acceptance criteria, bucket framing, and test-quality guidance. The measured result is therefore KG lift over a strong structured generation baseline.

Authorization gate crossed for RQ1. RQ1 is safe_to_present=true only because a signed governance authorization matches the frozen headline evidence hash and claim template. RQ2/RQ3 remain safe_to_present=false. In plain English: the measured test-quality lift number is approved for customer-facing use; the traceability and proof-boundary rows stay internal diagnostics until they have their own claim wording and sign-off.

Data-handling caveat. OrangePro KG does not persist ingested raw repository source files. It stores structural code metadata, source-system text used for grounding such as Jira/Confluence/PR excerpts, graph relationships, audit artifacts, and generated or repaired test-case bodies produced by the system. Credentials and tenant integration secrets are not shown on this proof hub.

Airflow OSS

airflow_oss_20260511

21 judged pairs · 3 packets · 20 KG wins · 1 baseline wins

Open full judged pairs
Click OSS

click_oss_20260513b

6 judged pairs · 3 packets · 6 KG wins · 0 baseline wins

Open full judged pairs
HTTP Core OSS

httpcore_oss_20260503

24 judged pairs · 3 packets · 22 KG wins · 2 baseline wins

Open full judged pairs

Static evidence surface. These pages are generated at commit time from the verdict JSON and do not fetch verdict data at runtime. Per-tenant pages contain the full judged-pair evidence.

Source verdict JSON: docs/reviews/data/public-aggregate-verdicts-2026-05-12.json

Verdict JSON SHA256: 5fe48b8384220dee172f2a05e1adecfa68feb328ea751abcc5d567f01252637c

Build script: scripts/build_proof_hub.py · version proof-hub-judged-pairs-v1 · command python scripts/build_proof_hub.py