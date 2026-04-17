#!/usr/bin/env python3
"""
Street1 Rollup: L0 → L2 (Event Log → Summary Snapshot)

Reads: runs/street1/events.ndjson (source of truth)
Emits: runs/street1/summary.json (derived facts + receipt_sha)

No external dependencies. Deterministic replay. Idempotent.

Schema: street1_summary.v1.schema.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# ─── Config ───────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = REPO_ROOT / "runs" / "street1" / "events.ndjson"
SUMMARY_PATH = REPO_ROOT / "runs" / "street1" / "summary.json"

SUMMARY_SCHEMA_VERSION = "STREET1_SUMMARY_V1"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def die(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(1)

def parse_ndjson(p: Path) -> List[Dict[str, Any]]:
    """Read NDJSON file line-by-line, parse each JSON."""
    if not p.exists():
        return []
    lines: List[Dict[str, Any]] = []
    for line_text in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line_text.strip():
            continue
        try:
            lines.append(json.loads(line_text))
        except json.JSONDecodeError:
            # Skip malformed lines, keep determinism
            continue
    return lines

# ─── Rollup Logic ─────────────────────────────────────────────────────────────

def compute_receipt_sha(events_path: Path) -> str:
    """Compute SHA256 of events.ndjson for receipt."""
    if not events_path.exists():
        return None
    content = events_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]  # 16-char truncated hash

def rollup_events(events: List[Dict[str, Any]], events_path: Path | None = None) -> Dict[str, Any]:
    """
    Scan event stream and extract derived facts.
    Pure function: same events → same output.
    """

    summary: Dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "event_count": len(events),
        "run_id": None,
        "seed": None,
        "session_start": None,
        "session_end": None,
        "facts_extracted": [],
        "npc_replies": [],
        "npc_npc_interactions": [],
        "final_positions": {},
        "receipt_sha": compute_receipt_sha(events_path) if events_path else None,
    }

    # Scan events
    for ev in events:
        ev_type = ev.get("type")

        # ── OBS: session_start ─────────────────────────────────────────────
        if ev_type == "OBS" and ev.get("sub_type") == "session_start":
            summary["run_id"] = ev.get("run_id")
            summary["seed"] = ev.get("seed")
            summary["session_start"] = ev.get("ts")

        # ── BND: memory_extraction → collect facts ────────────────────────
        elif ev_type == "BND" and ev.get("sub_type") == "memory_extraction":
            facts = ev.get("facts", [])
            for fact in facts:
                summary["facts_extracted"].append({
                    "fact": fact,
                    "t": ev.get("t"),
                    "npc_id": ev.get("npc_id"),
                })

        # ── OBS: npc_reply → collect reply trace ───────────────────────────
        elif ev_type == "OBS" and ev.get("sub_type") == "npc_reply":
            summary["npc_replies"].append({
                "npc_id": ev.get("actor"),
                "t": ev.get("t"),
                "text": ev.get("text", "")[:200],
                "source": ev.get("source"),
            })

        # ── OBS: npc_npc_trigger ──────────────────────────────────────────
        elif ev_type == "OBS" and ev.get("sub_type") == "npc_npc_trigger":
            summary["npc_npc_interactions"].append({
                "t": ev.get("t"),
                "npc1": ev.get("npc1"),
                "npc2": ev.get("npc2"),
                "dialogue": ev.get("dialogue", "")[:100],
            })

        # ── OBS: world_delta (sample: last positions) ──────────────────────
        elif ev_type == "OBS" and ev.get("sub_type") == "world_delta":
            positions = ev.get("positions", {})
            summary["final_positions"] = positions

        # ── END: session_end + receipt_sha ────────────────────────────────
        elif ev_type == "END" and ev.get("sub_type") == "session_end":
            summary["session_end"] = ev.get("ts")
            summary["receipt_sha"] = ev.get("_sha")  # receipt hash from END event

    return summary

# ─── Validators ───────────────────────────────────────────────────────────────

def validate_summary(summary: Dict[str, Any]) -> tuple[bool, str]:
    """
    Quick sanity check.
    Returns (is_valid, error_msg_if_invalid)
    """
    if not summary.get("run_id"):
        return False, "missing run_id"
    if summary.get("event_count", 0) < 2:
        return False, "event_count < 2 (incomplete run)"
    if not summary.get("receipt_sha"):
        return False, "missing receipt_sha (cannot hash events)"
    return True, ""

# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Street1 Rollup: convert events.ndjson → summary.json (deterministic)"
    )
    parser.add_argument(
        "--events",
        type=Path,
        default=EVENTS_PATH,
        help=f"Event log path (default: {EVENTS_PATH})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=SUMMARY_PATH,
        help=f"Output summary path (default: {SUMMARY_PATH})",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate summary and exit with code 0 (valid) or 1 (invalid)",
    )

    args = parser.parse_args()

    # ── Load events ────────────────────────────────────────────────────────
    if not args.events.exists():
        die(f"events file not found: {args.events}")

    events = parse_ndjson(args.events)
    if not events:
        die("no events found (empty or malformed)")

    print(f"[Rollup] Loaded {len(events)} events from {args.events}")

    # ── Rollup to summary ──────────────────────────────────────────────────
    summary = rollup_events(events, events_path=args.events)

    # ── Validate ───────────────────────────────────────────────────────────
    valid, err_msg = validate_summary(summary)
    if not valid:
        if args.validate:
            print(f"[Validate] FAIL: {err_msg}")
            raise SystemExit(1)
        else:
            print(f"[Rollup] WARNING: {err_msg}")

    # ── Write summary ──────────────────────────────────────────────────────
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(f"[Rollup] Summary written to {args.out}")

    # ── Verify ─────────────────────────────────────────────────────────────
    if args.validate:
        print(f"[Validate] PASS")
        print(f"  run_id        : {summary.get('run_id')}")
        print(f"  event_count   : {summary.get('event_count')}")
        print(f"  facts         : {len(summary.get('facts_extracted', []))}")
        print(f"  replies       : {len(summary.get('npc_replies', []))}")
        print(f"  receipt_sha   : {summary.get('receipt_sha')}")
    else:
        print(f"[Rollup] Done")
        print(f"  facts extracted  : {len(summary.get('facts_extracted', []))}")
        print(f"  NPC replies      : {len(summary.get('npc_replies', []))}")
        print(f"  receipt_sha      : {summary.get('receipt_sha')}")

if __name__ == "__main__":
    main()
