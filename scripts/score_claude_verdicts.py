#!/usr/bin/env python3
"""
score_claude_verdicts.py
Cross-reference Claude's judge output with the reference verdicts to compute KG win rate.

Usage:
    python scripts/score_claude_verdicts.py --claude claude_verdicts.json --reference data/verdicts_51pairs.json

Claude's output should be a JSON array like:
    [{"pair_number": 1, "winner": "A", "confidence": 0.88, "rationale_short": "..."}, ...]

The script maps each winner (A or B) to kg_side in the reference file to determine if KG won.
"""

import json
import argparse
import sys


def load_reference(path: str) -> list:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "verdicts" in data:
        return data["verdicts"]
    raise ValueError(f"Unrecognised reference format in {path}")


def load_claude_output(path: str) -> list:
    with open(path) as f:
        raw = f.read().strip()
    # Handle case where Claude wraps JSON in markdown code block
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw)


def score(claude_path: str, reference_path: str) -> None:
    reference = load_reference(reference_path)
    claude = load_claude_output(claude_path)

    if len(claude) != len(reference):
        print(f"WARNING: Claude returned {len(claude)} verdicts but reference has {len(reference)} pairs.")
        print("Scoring will match by pair_number where available, otherwise by position.")

    # Build reference lookup by position (1-based)
    ref_by_pos = {i + 1: v for i, v in enumerate(reference)}

    kg_wins = 0
    baseline_wins = 0
    ties = 0
    errors = 0

    print(f"\n{'Pair':<6} {'Claude Winner':<15} {'KG Side':<10} {'KG Won?':<10} {'Confidence':<12} Rationale")
    print("-" * 90)

    for item in claude:
        pair_num = item.get("pair_number", None)
        winner = str(item.get("winner", "")).strip().upper()
        confidence = item.get("confidence", "?")
        rationale = str(item.get("rationale_short", ""))[:60]

        ref = ref_by_pos.get(pair_num)
        if ref is None:
            print(f"{pair_num:<6} {'ERROR':<15} {'?':<10} {'?':<10} {str(confidence):<12} Reference pair not found")
            errors += 1
            continue

        kg_side = str(ref.get("kg_side", "")).strip().upper()

        if winner == "tie":
            ties += 1
            kg_won_str = "tie"
        elif not kg_side:
            # No kg_side field — fall back to kg_won if available
            kg_won = ref.get("kg_won")
            if kg_won is True:
                kg_wins += 1
                kg_won_str = "YES (from kg_won)"
            elif kg_won is False:
                baseline_wins += 1
                kg_won_str = "NO (from kg_won)"
            else:
                errors += 1
                kg_won_str = "UNKNOWN"
        else:
            if winner == kg_side:
                kg_wins += 1
                kg_won_str = "YES"
            else:
                baseline_wins += 1
                kg_won_str = "NO"

        print(f"{pair_num:<6} {winner:<15} {kg_side:<10} {kg_won_str:<10} {str(confidence):<12} {rationale}")

    total = kg_wins + baseline_wins + ties
    win_rate = kg_wins / total if total > 0 else 0

    print("-" * 90)
    print(f"\n=== Claude Replication Results ===")
    print(f"Total pairs scored : {total}")
    print(f"KG won             : {kg_wins}")
    print(f"Baseline won       : {baseline_wins}")
    print(f"Ties               : {ties}")
    if errors:
        print(f"Errors/skipped     : {errors}")
    print(f"KG win rate        : {kg_wins}/{total} = {win_rate:.1%}")
    print(f"\nOriginal paper result: 48/51 = 94.1%")
    diff = abs(win_rate - 0.941)
    if diff <= 0.04:
        print(f"Result: REPLICATES (within ±4% tolerance for LLM stochasticity)")
    else:
        print(f"Result: DIFFERS by {diff:.1%} — investigate outlier pairs above")


def main():
    parser = argparse.ArgumentParser(
        description="Score Claude's judge output against the reference verdicts to compute KG win rate."
    )
    parser.add_argument("--claude", required=True, help="Path to Claude's JSON output file")
    parser.add_argument("--reference", required=True, help="Path to reference verdicts JSON file")
    args = parser.parse_args()
    score(args.claude, args.reference)


if __name__ == "__main__":
    main()
