#!/usr/bin/env python3
"""
Add a lesson to HELEN's wisdom.

Usage:
  python3 scripts/helen_add_lesson.py --lesson "lesson text" --evidence "evidence text" [--kind rule|lesson] [--status ACTIVE|DRAFT]

Example:
  python3 scripts/helen_add_lesson.py \
    --lesson "When cached greetings exist, CLI tests must filter non-cached dialogue" \
    --evidence "Street1 memory test fixed with (!msg.cached) filter" \
    --kind lesson \
    --status ACTIVE
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIS = ROOT / "helen_wisdom.ndjson"

def add_lesson(lesson, evidence, kind="lesson", status="ACTIVE"):
    """Append a lesson to helen_wisdom.ndjson"""
    entry = {
        "t": datetime.now().strftime("%Y-%m-%d"),
        "kind": kind,
        "lesson": lesson,
        "evidence": evidence,
        "status": status
    }

    # Append to NDJSON file
    with open(WIS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"✓ Added lesson: {lesson}")
    print(f"  Evidence: {evidence}")
    print(f"  Kind: {kind}, Status: {status}")

def main():
    parser = argparse.ArgumentParser(
        description="Add a lesson to HELEN's wisdom",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--lesson",
        required=True,
        help="The lesson text (the rule or insight)"
    )
    parser.add_argument(
        "--evidence",
        required=True,
        help="Evidence or context where this lesson came from"
    )
    parser.add_argument(
        "--kind",
        choices=["rule", "lesson"],
        default="lesson",
        help="Type of wisdom: 'rule' (general principle) or 'lesson' (specific fix)"
    )
    parser.add_argument(
        "--status",
        choices=["ACTIVE", "DRAFT"],
        default="ACTIVE",
        help="Status of the wisdom entry"
    )

    args = parser.parse_args()
    add_lesson(args.lesson, args.evidence, args.kind, args.status)

if __name__ == "__main__":
    main()
