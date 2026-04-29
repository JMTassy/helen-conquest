#!/usr/bin/env python3
"""helen_video_cli.py — RAI video admissibility CLI.

Subcommands:
  render   — candidate + gate + ledger append (one clip pipeline)
  export   — print accepted clips as a replayable export manifest
  status   — ledger stats + chain integrity check
  verify   — re-verify chain integrity only

Usage:
  python experiments/helen_video/helen_video_cli.py render \\
    --prompt "HELEN in Oracle Town" \\
    --model kling-v1 \\
    --content-hash sha256:abc123 \\
    --visual-coherence 0.85 \\
    --temporal-alignment 0.72 \\
    --ledger artifacts/video_ledger.ndjson

  python experiments/helen_video/helen_video_cli.py export \\
    --ledger artifacts/video_ledger.ndjson

  python experiments/helen_video/helen_video_cli.py status \\
    --ledger artifacts/video_ledger.ndjson

Canonical invariant:
  Nothing enters the timeline because it looks good.
  It enters only if it survives admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from helen_video.admissibility_gate import (
    PIPELINE_SALT,
    evaluate,
    verify_receipt_binding,
)
from helen_video.ralph_generator import generate_candidate
from helen_video.video_ledger import VideoLedger

_GATE_TO_LEDGER = {"ACCEPT": "ACCEPTED", "REJECT": "REJECTED", "PENDING": "PENDING"}


# ── helpers ───────────────────────────────────────────────────────────────────

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _build_receipt(
    content_hash: str,
    model: str,
    visual_coherence: float | None,
    temporal_alignment: float | None,
    state_hash: str | None,
) -> dict:
    pipeline_hash = _sha256(content_hash + PIPELINE_SALT)
    receipt: dict = {
        "content_hash": content_hash,
        "pipeline_hash": pipeline_hash,
        "model_signature": model,
    }
    if state_hash:
        receipt["state_hash"] = state_hash
    if visual_coherence is not None:
        receipt["visual_coherence"] = visual_coherence
    if temporal_alignment is not None:
        receipt["temporal_alignment"] = temporal_alignment
    return receipt


def _print_json(obj: dict) -> None:
    print(json.dumps(obj, indent=2, default=str))


# ── subcommands ───────────────────────────────────────────────────────────────

def cmd_render(args: argparse.Namespace) -> int:
    ledger = VideoLedger(args.ledger)

    candidate = generate_candidate(
        prompt=args.prompt,
        model=args.model,
        ralph_iteration_id=args.ralph_iteration_id,
    )

    receipt = _build_receipt(
        content_hash=args.content_hash,
        model=args.model,
        visual_coherence=args.visual_coherence,
        temporal_alignment=args.temporal_alignment,
        state_hash=args.state_hash,
    )

    verdict = evaluate(candidate, receipt)

    entry = ledger.append(
        video_id=candidate["candidate_id"],
        status=_GATE_TO_LEDGER[verdict.decision],
        receipt=receipt,
        decision_reason=verdict.reason,
        ralph_iteration_id=args.ralph_iteration_id,
    )

    result = {
        "candidate_id": candidate["candidate_id"],
        "prompt": args.prompt,
        "model": args.model,
        "decision": verdict.decision,
        "reason": verdict.reason,
        "entry_hash": entry["entry_hash"],
        "ledger": str(args.ledger),
    }
    _print_json(result)

    return 0 if verdict.decision == "ACCEPT" else 1


def cmd_export(args: argparse.Namespace) -> int:
    ledger = VideoLedger(args.ledger)
    accepted = ledger.accepted()

    if not accepted:
        print(json.dumps({"status": "empty", "accepted_count": 0}))
        return 0

    clip_hashes = [e["receipt"]["content_hash"] for e in accepted if e.get("receipt")]
    timeline_hash = _sha256("|".join(clip_hashes))

    manifest = {
        "export_ts": datetime.now(timezone.utc).isoformat(),
        "ledger": str(args.ledger),
        "accepted_count": len(accepted),
        "timeline_hash": timeline_hash,
        "clips": [
            {
                "video_id": e["video_id"],
                "content_hash": e.get("receipt", {}).get("content_hash"),
                "model": e.get("receipt", {}).get("model_signature"),
                "ts": e.get("ts"),
                "entry_hash": e["entry_hash"],
            }
            for e in accepted
        ],
    }
    _print_json(manifest)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ledger = VideoLedger(args.ledger)
    entries = ledger._read_all()
    chain_ok = ledger.verify_chain()

    counts: dict[str, int] = {}
    for e in entries:
        counts[e["status"]] = counts.get(e["status"], 0) + 1

    status = {
        "ledger": str(args.ledger),
        "total_entries": len(entries),
        "chain_valid": chain_ok,
        "by_status": counts,
        "accepted_count": counts.get("ACCEPTED", 0),
    }
    _print_json(status)
    return 0 if chain_ok else 2


def cmd_verify(args: argparse.Namespace) -> int:
    ledger = VideoLedger(args.ledger)
    ok = ledger.verify_chain()
    print(json.dumps({"chain_valid": ok, "ledger": str(args.ledger)}))
    return 0 if ok else 2


# ── main ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helen_video",
        description="RAI video admissibility pipeline",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # render
    r = sub.add_parser("render", help="candidate → gate → ledger")
    r.add_argument("--prompt", required=True)
    r.add_argument("--model", default="helen-core")
    r.add_argument("--content-hash", required=True, dest="content_hash")
    r.add_argument("--visual-coherence", type=float, default=None, dest="visual_coherence")
    r.add_argument("--temporal-alignment", type=float, default=None, dest="temporal_alignment")
    r.add_argument("--state-hash", default=None, dest="state_hash")
    r.add_argument("--ralph-iteration-id", default=None, dest="ralph_iteration_id")
    r.add_argument("--ledger", default="artifacts/video_ledger.ndjson", type=Path)

    # export
    e = sub.add_parser("export", help="print accepted clips as export manifest")
    e.add_argument("--ledger", default="artifacts/video_ledger.ndjson", type=Path)

    # status
    s = sub.add_parser("status", help="ledger stats + chain integrity")
    s.add_argument("--ledger", default="artifacts/video_ledger.ndjson", type=Path)

    # verify
    v = sub.add_parser("verify", help="re-verify chain integrity only")
    v.add_argument("--ledger", default="artifacts/video_ledger.ndjson", type=Path)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"render": cmd_render, "export": cmd_export,
                "status": cmd_status, "verify": cmd_verify}
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
