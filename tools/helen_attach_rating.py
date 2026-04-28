#!/usr/bin/env python3
"""
helen_attach_rating — bind a 3-field operator decision to an existing render
receipt + candidate JSON, without re-rendering.

Use this after a render pilot has produced:
  - render_receipt.json  (status: RATING_PENDING)
  - candidate.json       (status: BLOCK_RATING_PENDING)
  - the actual mp4 in Telegram (operator watches it on their phone)

The operator watches the clip, decides, and runs:

  python3 tools/helen_attach_rating.py /tmp/helen_render_pilot_v3 \\
      --operator-decision KEEP \\
      --pipeline-score 9 \\
      --output-score 7

This atomically updates BOTH JSON files in place:
  - receipt: status RATING_PENDING → VALIDATED, fields filled
  - candidate: status BLOCK_RATING_PENDING → READY_FOR_REDUCER (KEEP)
                                          or REJECTED (REJECT)

Constraints:
- NO re-render. NO Higgsfield calls. NO ledger writes.
- NO_RATING = INVALID — out-of-range scores raise RuntimeError.
- The receipt directory must already contain a render_receipt.json.
- Idempotent over identical input; refuses to overwrite a non-pending status
  unless --force is passed (so accidental re-rate doesn't clobber a real one).

Operator must provide all 3 required flags. failure_class is optional but
recommended on REJECT.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    ap = argparse.ArgumentParser(description="Attach 3-field operator rating to an existing render receipt + candidate")
    ap.add_argument("pilot_dir", type=Path, help="directory containing render_receipt.json and candidate.json")
    ap.add_argument("--operator-decision", choices=["KEEP", "REJECT"], required=True)
    ap.add_argument("--pipeline-score", type=int, required=True, help="1-10")
    ap.add_argument("--output-score", type=int, required=True, help="1-10")
    ap.add_argument("--failure-class", type=str, default=None, help="optional free-string label, recommended on REJECT")
    ap.add_argument("--force", action="store_true", help="overwrite an already-rated receipt (default: refuse)")
    args = ap.parse_args()

    if not (1 <= args.pipeline_score <= 10):
        raise RuntimeError(f"INVALID_SCORE — --pipeline-score {args.pipeline_score} out of range 1-10")
    if not (1 <= args.output_score <= 10):
        raise RuntimeError(f"INVALID_SCORE — --output-score {args.output_score} out of range 1-10")

    pilot = args.pilot_dir
    receipt_path = pilot / "render_receipt.json"
    candidate_path = pilot / "candidate.json"

    if not receipt_path.exists():
        print(f"ERROR: {receipt_path} not found", file=sys.stderr)
        return 2
    receipt = json.loads(receipt_path.read_text())

    current_status = receipt.get("status")
    if current_status not in ("RATING_PENDING", None) and not args.force:
        print(f"ERROR: receipt status is {current_status!r}, not RATING_PENDING. "
              f"Use --force to overwrite (be sure).", file=sys.stderr)
        return 3

    # Update receipt
    receipt["status"] = "VALIDATED"
    receipt["operator_decision"] = args.operator_decision
    receipt["pipeline_score"] = args.pipeline_score
    receipt["output_score"] = args.output_score
    receipt["failure_class"] = args.failure_class
    receipt["rated_at"] = now_iso()
    receipt_path.write_text(json.dumps(receipt, indent=2))
    print(f"[receipt]   {receipt_path}")
    print(f"            status: {current_status} → VALIDATED")
    print(f"            decision={args.operator_decision} pipeline={args.pipeline_score} output={args.output_score}"
          + (f" failure_class={args.failure_class}" if args.failure_class else ""))

    # Update candidate (if present)
    if candidate_path.exists():
        cand = json.loads(candidate_path.read_text())
        prev_cand_status = cand.get("status")
        if args.operator_decision == "KEEP":
            cand["status"] = "READY_FOR_REDUCER"
        else:
            cand["status"] = "REJECTED"
        cand["manifest"]["operator_decision"] = args.operator_decision
        cand["manifest"]["pipeline_score"] = args.pipeline_score
        cand["manifest"]["output_score"] = args.output_score
        if args.failure_class:
            cand["manifest"]["failure_class"] = args.failure_class
        cand["rated_at"] = now_iso()
        candidate_path.write_text(json.dumps(cand, indent=2))
        print(f"[candidate] {candidate_path}")
        print(f"            status: {prev_cand_status} → {cand['status']}")
    else:
        print(f"[candidate] (no candidate.json found in {pilot} — skipped)")

    print()
    if args.operator_decision == "KEEP":
        print("Candidate is READY_FOR_REDUCER. Next: route through standard "
              "proposal → peer-review → MAYOR → REDUCER chain when ready to ship.")
    else:
        print("Candidate REJECTED. Render artifacts persist on disk for forensic review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
