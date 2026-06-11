#!/usr/bin/env python3
"""
reproduce_results.py
Replication script for: "Ontology-Governed Test Generation: A Neo4j-Native Approach
to Shape-Validated Knowledge Graphs for Enterprise QA" (ISWC 2026)

Usage:
    python reproduce_results.py --input data/verdicts_51pairs.json

Expected output:
    KG win rate: 48/51 = 94.12%
"""

import json
import argparse
import sys


def compute_win_rate(verdicts_path: str) -> None:
    with open(verdicts_path, "r") as f:
        data = json.load(f)

    # Support both list format (per-pair) and dict format (aggregate bundle)
    if isinstance(data, list):
        pairs = data
        total = len(pairs)
        kg_wins = sum(1 for p in pairs if p.get("kg_preferred") is True)
        baseline_wins = sum(1 for p in pairs if p.get("kg_preferred") is False)
        ties = total - kg_wins - baseline_wins
    elif isinstance(data, dict) and "aggregate" in data:
        agg = data["aggregate"]
        total = agg.get("total_pairs", 0)
        kg_wins = agg.get("kg_preferred_count", 0)
        baseline_wins = agg.get("baseline_preferred_count", 0)
        ties = agg.get("tie_count", 0)
    elif isinstance(data, dict) and "pairs" in data:
        pairs = data["pairs"]
        total = len(pairs)
        kg_wins = sum(1 for p in pairs if p.get("kg_preferred") is True)
        baseline_wins = sum(1 for p in pairs if p.get("kg_preferred") is False)
        ties = total - kg_wins - baseline_wins
    else:
        print("ERROR: Unrecognised verdicts format.")
        sys.exit(1)

    win_rate = kg_wins / total if total > 0 else 0

    print(f"\n=== Evaluation Results ===")
    print(f"Total judged pairs : {total}")
    print(f"KG-preferred       : {kg_wins}")
    print(f"Baseline-preferred : {baseline_wins}")
    print(f"Ties               : {ties}")
    print(f"KG win rate        : {kg_wins}/{total} = {win_rate:.1%}")
    print(f"\nExpected: 48/51 = 94.1%")
    match = "MATCHES" if abs(win_rate - 0.941) < 0.005 else "DIFFERS"
    print(f"Result: {match}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reproduce the 94.1% KG win rate from the ISWC 2026 paper."
    )
    parser.add_argument("--input", required=True, help="Path to verdicts JSON file")
    args = parser.parse_args()
    compute_win_rate(args.input)
