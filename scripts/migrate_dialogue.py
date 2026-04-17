#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate Dialogue Events: Old Format → Canonical Format

Reads old-style dialogue.ndjson and produces new canonical events with:
  - Payload/meta split
  - Cumulative hashing
  - Deterministic reason codes
  - Full hash chain from genesis

Usage:
    python3 migrate_dialogue.py old_dialogue.ndjson output_dialogue.ndjson
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from dialogue_writer import DialogueWriter, create_turn_payload, create_hal_verdict


def migrate_event(old_event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert old format event to new canonical payload/meta split."""
    # Extract old fields
    turn = old_event.get("turn", 0)
    hal_parsed = old_event.get("hal_parsed", {})
    text = old_event.get("text", "")
    timestamp_utc = old_event.get("timestamp_utc", "")

    # Normalize HAL to ensure reasons_codes and required_fixes are sorted
    hal = {
        "verdict": hal_parsed.get("verdict", "BLOCK"),
        "reasons_codes": sorted(hal_parsed.get("reasons_codes", hal_parsed.get("reasons", []))),
        "required_fixes": sorted(hal_parsed.get("required_fixes", [])),
        "certificates": sorted(hal_parsed.get("certificates", [])),
        "refs": hal_parsed.get("refs", {}),
        "mutations": hal_parsed.get("mutations", []),
    }

    # Build new payload
    payload = {
        "turn": turn,
        "channel_contract": "HER_HAL_V1",
        "hal": hal,
    }

    # Build meta (timestamp, raw text, etc.)
    meta = {}
    if timestamp_utc:
        meta["timestamp_utc"] = timestamp_utc
    if text:
        meta["raw_text"] = text

    return {
        "payload": payload,
        "meta": meta,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 migrate_dialogue.py <input.ndjson> <output.ndjson>")
        print("\nExamples:")
        print("  python3 migrate_dialogue.py old_dialogue.ndjson new_dialogue.ndjson")
        print("  python3 migrate_dialogue.py town/dialogue.ndjson town/dialogue.canonical.ndjson")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)

    print(f"\n📝 Migrating Dialogue Events\n")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}\n")

    # Read old events
    old_content = input_path.read_text(encoding="utf-8")
    old_lines = [l for l in old_content.split("\n") if l.strip()]

    if not old_lines:
        print("⚠️  No events in input file")
        sys.exit(0)

    print(f"Found {len(old_lines)} old events\n")

    # Create writer
    writer = DialogueWriter(str(output_path))

    # Migrate events
    migrated = 0
    errors = []

    for line_num, line in enumerate(old_lines):
        try:
            old_event = json.loads(line)

            # Migrate
            new_data = migrate_event(old_event)

            # Append using writer (this computes hashes)
            event = writer.append(
                type_="turn",
                payload=new_data["payload"],
                meta=new_data["meta"],
            )

            migrated += 1
            if migrated % max(1, len(old_lines) // 10) == 0 or migrated == len(old_lines):
                print(f"  ✓ {migrated}/{len(old_lines)} events migrated...")

        except json.JSONDecodeError as e:
            errors.append(f"Line {line_num}: JSON parse error: {e}")
        except Exception as e:
            errors.append(f"Line {line_num}: {e}")

    print(f"\n✅ Migration complete")
    print(f"  Migrated: {migrated}")
    print(f"  Errors: {len(errors)}")

    if errors:
        print(f"\n⚠️  Migration errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"\n📊 Output statistics:")
    # Read output to show stats
    output_content = output_path.read_text(encoding="utf-8")
    output_lines = [l for l in output_content.split("\n") if l.strip()]

    if output_lines:
        first = json.loads(output_lines[0])
        last = json.loads(output_lines[-1])
        print(f"  Events in output: {len(output_lines)}")
        print(f"  First seq: {first.get('seq')}")
        print(f"  Last seq: {last.get('seq')}")
        print(f"  Final cum_hash: {last.get('cum_hash', '')[:16]}...")

    print(f"\n✅ Migration successful. Run validator:")
    print(f"  python3 scripts/validate_dialogue.py")


if __name__ == "__main__":
    main()
