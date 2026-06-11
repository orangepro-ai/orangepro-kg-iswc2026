#!/usr/bin/env python3
"""
reproduce_results.py — ISWC 2026 replication script

Usage:
    python scripts/reproduce_results.py --input data/verdicts_51pairs.json

Expected output:
    KG win rate: 48/51 = 94.1%
"""
import json, argparse, sys

def compute_win_rate(verdicts_path):
    with open(verdicts_path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "verdicts" in data:
        pairs = data["verdicts"]
        total = len(pairs)
        kg_wins = sum(1 for p in pairs if p.get("kg_won") is True)
        baseline_wins = sum(1 for p in pairs if p.get("kg_won") is False)
        ties = total - kg_wins - baseline_wins
    elif isinstance(data, dict) and "aggregate" in data:
        agg = data["aggregate"]
        total = agg.get("pairs", 0)
        kg_wins = agg.get("kg_wins", 0)
        baseline_wins = agg.get("baseline_wins", 0)
        ties = agg.get("ties", 0)
    elif isinstance(data, list):
        pairs = data
        total = len(pairs)
        kg_wins = sum(1 for p in pairs if p.get("kg_won") is True or p.get("kg_preferred") is True)
        baseline_wins = total - kg_wins
        ties = 0
    else:
        print("ERROR: Unrecognised verdicts format."); sys.exit(1)
    win_rate = kg_wins / total if total > 0 else 0
    print(f"\n=== Evaluation Results ===")
    print(f"Total judged pairs : {total}")
    print(f"KG-preferred       : {kg_wins}")
    print(f"Baseline-preferred : {baseline_wins}")
    print(f"Ties               : {ties}")
    print(f"KG win rate        : {kg_wins}/{total} = {win_rate:.1%}")
    print(f"\nExpected: 48/51 = 94.1%")
    print(f"Result: {'MATCHES' if abs(win_rate - 0.941) < 0.005 else 'DIFFERS'}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    compute_win_rate(p.parse_args().input)
