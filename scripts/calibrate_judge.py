"""
Run provider agreement calibration against a blinded human-labeled judge gold set.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.nodes import JudgeProvider
from app.services.judge_calibration import JudgeCalibrationService, load_gold_set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate judge providers against blinded human labels")
    parser.add_argument(
        "--pack",
        default="evals/judge_calibration/beautyco-judge-gold.json",
        help="Path to judge calibration gold JSON",
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=[provider.value for provider in JudgeProvider],
        required=True,
        help="Provider to calibrate; pass more than once to compare multiple providers",
    )
    parser.add_argument("--live", action="store_true", help="Allow live provider-backed API calls")
    parser.add_argument("--threshold", type=float, default=0.75, help="Pass threshold for agreement rate")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    return parser.parse_args()


def print_summary(result: dict) -> None:
    print()
    print(f"Pack: {result['pack_path']}")
    print(f"Threshold: {result['threshold']}")
    print()
    print(f"{'provider':<15} {'pairs':>5} {'agreements':>11} {'ties':>5} {'agreement_rate':>15} {'threshold_pass':>15}")
    for row in result["provider_summaries"]:
        print(
            f"{row['provider']:<15} {row['pairs']:>5} {row['agreements']:>11} "
            f"{row['ties']:>5} {row['agreement_rate']:>15.4f} {str(row['threshold_pass']):>15}"
        )


async def main() -> int:
    args = parse_args()
    providers = [JudgeProvider(provider) for provider in args.provider]
    gold_set = load_gold_set(args.pack)
    service = JudgeCalibrationService()
    try:
        result = await service.calibrate(
            gold_set=gold_set,
            providers=providers,
            threshold=args.threshold,
            live=args.live,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    payload = result.model_dump()
    payload["pack_path"] = args.pack
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_summary(payload)

    if any(not row["threshold_pass"] for row in payload["provider_summaries"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
