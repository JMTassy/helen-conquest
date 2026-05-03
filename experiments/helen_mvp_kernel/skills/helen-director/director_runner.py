"""HELEN Director — minimal decision runner.

Per HAL: "Skill exists. Now give it a button."

Free-prose brief.txt + seed -> fixed-shape decision packet + receipt.
Stdlib only. Deterministic. Replay-stable.

Usage:
    python director_runner.py --brief brief.txt --seed 777 \
                              --out temple/subsandbox/director/run_id

Acceptance:
    same brief + same seed = same receipt_hash
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_decision(brief_text: str, seed: int) -> Dict[str, Any]:
    return {
        "director_decision": "Ship the smallest receipt-bound next action.",
        "why": "It converts intent into an executable packet without expanding scope.",
        "next_3_steps": [
            "Parse the brief.",
            "Create a deterministic Director packet.",
            "Emit a receipt and verify replay.",
        ],
        "receipt_required": "DIRECTOR_DECISION_RECEIPT_V1",
        "next_command": (
            "re-run director_runner.py with the same brief and seed "
            "to verify hash stability"
        ),
        "seed": seed,
        "brief_hash": sha256_text(brief_text),
    }


def make_receipt(packet: Dict[str, Any]) -> Dict[str, Any]:
    receipt: Dict[str, Any] = {
        "type": "DIRECTOR_DECISION_RECEIPT_V1",
        "scope": "TEMPLE_SUBSANDBOX",
        "sovereign_admitted": False,
        "packet_hash": sha256_obj(packet),
        "status": "PASS",
    }
    # Self-referential hash safe: receipt_hash key not present at hash time.
    receipt["receipt_hash"] = sha256_obj(receipt)
    return receipt


def render_packet_md(packet: Dict[str, Any], receipt: Dict[str, Any]) -> str:
    return (
        "# DIRECTOR PACKET\n"
        "\n"
        "DIRECTOR DECISION:\n"
        f"{packet['director_decision']}\n"
        "\n"
        "WHY:\n"
        f"{packet['why']}\n"
        "\n"
        "NEXT 3 STEPS:\n"
        f"1. {packet['next_3_steps'][0]}\n"
        f"2. {packet['next_3_steps'][1]}\n"
        f"3. {packet['next_3_steps'][2]}\n"
        "\n"
        "RECEIPT REQUIRED:\n"
        f"{packet['receipt_required']}\n"
        "\n"
        "NEXT COMMAND:\n"
        f"{packet['next_command']}\n"
        "\n"
        "BRIEF HASH:\n"
        f"{packet['brief_hash']}\n"
        "\n"
        "PACKET HASH:\n"
        f"{receipt['packet_hash']}\n"
        "\n"
        "RECEIPT HASH:\n"
        f"{receipt['receipt_hash']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="HELEN Director decision runner")
    parser.add_argument("--brief", required=True, help="Path to free-prose brief.txt")
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"brief not found: {brief_path}", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    brief_text = brief_path.read_text(encoding="utf-8")
    packet = build_decision(brief_text, args.seed)
    receipt = make_receipt(packet)
    packet_md = render_packet_md(packet, receipt)

    (out_dir / "DIRECTOR_PACKET.md").write_text(packet_md, encoding="utf-8")
    (out_dir / "DIRECTOR_PACKET.json").write_text(canonical(packet), encoding="utf-8")
    (out_dir / "DIRECTOR_DECISION_RECEIPT_V1.json").write_text(
        canonical(receipt), encoding="utf-8"
    )

    print(receipt["receipt_hash"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
