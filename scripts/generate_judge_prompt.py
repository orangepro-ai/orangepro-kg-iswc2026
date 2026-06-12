#!/usr/bin/env python3
"""
generate_judge_prompt.py
Generate a ready-to-paste LLM judge prompt from a verdicts JSON file.

Usage:
    # Generate prompt for calibration set (24 pairs):
    python scripts/generate_judge_prompt.py --input data/verdicts_calibration_24pairs.json

    # Generate prompt for main evaluation set (51 pairs):
    python scripts/generate_judge_prompt.py --input data/verdicts_51pairs.json

    # Save to a file instead of printing:
    python scripts/generate_judge_prompt.py --input data/verdicts_calibration_24pairs.json --output judge_prompt.txt

The generated prompt can be pasted directly into Claude, ChatGPT, or any LLM.
The LLM should return a JSON array with one verdict per pair.

Expected output format from the LLM:
    [
      {"pair_number": 1, "winner": "A", "confidence": 0.87, "rationale_short": "..."},
      ...
    ]

Note on stochasticity: LLMs are non-deterministic. Minor variance (±2 pairs) from
the recorded consensus_winner values is expected and acceptable. See README for details.
"""

import json
import argparse
import sys

SYSTEM_PROMPT = (
    "You are a blinded software test judge. Compare Option A and Option B without "
    "assuming either side is preferred. Return only strict JSON with keys: winner, "
    "confidence, scores, rationale_short, flags. winner must be one of A, B, tie. "
    "confidence must be raw uncalibrated judge confidence from 0.0-1.0. scores must "
    "contain option_a and option_b objects, each scored 0.0-1.0 on exactly these "
    "dimensions: relevance, completeness, accuracy, context_awareness, "
    "domain_specificity, traceability, gap_coverage, non_redundancy. Treat confidence "
    "and scores as diagnostic preference metadata only, not proof."
)


def load_pairs(path: str) -> list:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "verdicts" in data:
        return data["verdicts"]
    raise ValueError(f"Unrecognised verdicts format in {path}")


def build_prompt(pairs: list) -> str:
    lines = []
    lines.append("SYSTEM INSTRUCTIONS:")
    lines.append(SYSTEM_PROMPT)
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"TASK: Judge all {len(pairs)} pairs below. For each pair, return a JSON object.")
    lines.append(f"Return your response as a JSON array of {len(pairs)} objects, one per pair.")
    lines.append("Each object must include: pair_number, winner, confidence, rationale_short")
    lines.append("=" * 80)
    lines.append("")

    for i, v in enumerate(pairs, 1):
        lines.append(f"--- PAIR {i} ---")
        lines.append(f"Packet title: {str(v.get('packet_title', '')).strip()}")
        lines.append(f"Bucket: {str(v.get('bucket_name', '')).strip()}")
        lines.append(f"Story: {str(v.get('story_text', '')).strip()}")

        ac = v.get("acceptance_criteria", [])
        if ac and isinstance(ac, list) and len(ac) > 0:
            lines.append(f"Acceptance criteria: {'; '.join(str(x) for x in ac)}")
        else:
            lines.append("Acceptance criteria: (none provided)")

        lines.append("")
        # Handle two field name schemas: calibration set uses option_a_body, main set uses option_a_test_body
        a_title = v.get('option_a_title') or v.get('option_a_test_title', '')
        a_body  = v.get('option_a_body')  or v.get('option_a_test_body', '')
        b_title = v.get('option_b_title') or v.get('option_b_test_title', '')
        b_body  = v.get('option_b_body')  or v.get('option_b_test_body', '')
        lines.append(f"Option A title: {str(a_title).strip()}")
        lines.append(f"Option A body:\n{str(a_body).strip()}")
        lines.append("")
        lines.append(f"Option B title: {str(b_title).strip()}")
        lines.append(f"Option B body:\n{str(b_body).strip()}")
        lines.append("")

    lines.append("=" * 80)
    lines.append(f"Return a JSON array of {len(pairs)} objects. Format:")
    lines.append('[{"pair_number": 1, "winner": "A", "confidence": 0.85, "rationale_short": "..."}, ...]')
    lines.append("Return JSON only. No explanation outside the JSON.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a ready-to-paste LLM judge prompt from a verdicts JSON file."
    )
    parser.add_argument("--input", required=True, help="Path to verdicts JSON file")
    parser.add_argument("--output", default=None, help="Output file path (default: print to stdout)")
    args = parser.parse_args()

    pairs = load_pairs(args.input)
    prompt = build_prompt(pairs)

    if args.output:
        with open(args.output, "w") as f:
            f.write(prompt)
        print(f"Prompt written to: {args.output}")
        print(f"  Pairs: {len(pairs)}")
        print(f"  Characters: {len(prompt):,}")
        print(f"  Lines: {len(prompt.splitlines())}")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
