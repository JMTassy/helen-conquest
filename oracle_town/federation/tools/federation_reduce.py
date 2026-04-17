#!/usr/bin/env python3
# Deterministic federation reducer (v0.1).
# Input: treaty.json, link.json, optional receipt.json
# Output: PASS/BLOCK with reason strings (no side-effects).

import json
import sys
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def reduce(treaty, link, receipt=None):
    reasons = []
    town_ids = {t["town_id"] for t in treaty["towns"]}
    if link["from_town"] not in town_ids:
        reasons.append("from_town_not_in_treaty")
    if link["to_town"] not in town_ids:
        reasons.append("to_town_not_in_treaty")
    if treaty["policies"].get("receipt_required") and receipt is None:
        reasons.append("receipt_required_missing")
    if receipt is not None:
        if receipt.get("treaty_id") != treaty.get("treaty_id"):
            reasons.append("receipt_treaty_mismatch")
        if receipt.get("link_id") != link.get("link_id"):
            reasons.append("receipt_link_mismatch")
        if receipt.get("verdict") != "PASS":
            reasons.append("receipt_verdict_not_pass")
    verdict = "PASS" if not reasons else "BLOCK"
    return {"verdict": verdict, "reasons": reasons}


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("Usage: federation_reduce.py <treaty.json> <link.json> [receipt.json]")
        return 2
    treaty = load(Path(sys.argv[1]))
    link = load(Path(sys.argv[2]))
    receipt = load(Path(sys.argv[3])) if len(sys.argv) == 4 else None
    out = reduce(treaty, link, receipt)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
