#!/usr/bin/env python3
"""
Generate deterministic intake manifest for Bibliothèque inbox.

Pure receipts only: hashes raw bytes from untrusted inbox folder.
Does NOT parse, interpret, or mutate content.
Does NOT write to oracle_town/memory/bibliotheque/ directly.

Output: receipts/bibliotheque_intake_manifest.json
  - List of all files in inbox
  - SHA256 of each file (raw bytes)
  - Canonical manifest hash
  - No file mutations, no policy changes, no schema enforcement

Usage:
  python3 scripts/bibliotheque_manifest.py

The manifest proves:
  ✓ What was offered for intake
  ✓ When (timestamp)
  ✓ Exact content (SHA256)
  ✓ Nothing was modified during receipt

Next step: Human + CI review. Bot proposes PR (not autonomous).
"""

import json
import hashlib
import os
import sys
import time
from pathlib import Path
from datetime import datetime


def sha256_bytes(b: bytes) -> str:
    """Compute SHA256 of raw bytes."""
    return hashlib.sha256(b).hexdigest()


def collect_inbox_items(inbox_dir: Path) -> list:
    """Collect all files from inbox, NO interpretation."""
    items = []

    if not inbox_dir.exists():
        return items

    # Recursively find all files in inbox (except REQUESTS.json)
    for root, dirs, files in os.walk(inbox_dir):
        for filename in sorted(files):
            # Skip the requests file itself
            if filename == "REQUESTS.json":
                continue

            filepath = Path(root) / filename
            try:
                with open(filepath, "rb") as f:
                    raw = f.read()

                rel_path = filepath.relative_to(inbox_dir)
                items.append({
                    "path": str(rel_path),
                    "full_path": str(filepath),
                    "size_bytes": len(raw),
                    "sha256": sha256_bytes(raw),
                    "mtime_epoch": int(filepath.stat().st_mtime),
                })
            except (IOError, OSError) as e:
                print(f"Warning: could not read {filepath}: {e}", file=sys.stderr)

    return sorted(items, key=lambda x: x["path"])


def generate_manifest(inbox_dir: str = None, output_path: str = None) -> dict:
    """Generate intake manifest (receipts only, no mutations)."""
    if inbox_dir is None:
        inbox_dir = "oracle_town/inbox"

    if output_path is None:
        output_path = "receipts/bibliotheque_intake_manifest.json"

    root = Path.cwd()
    inbox_path = root / inbox_dir

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Collect items (pure inventory, no interpretation)
    items = collect_inbox_items(inbox_path)

    # Create manifest
    manifest = {
        "schema_version": "bibliotheque_intake_manifest_v1",
        "generated_at_epoch": int(time.time()),
        "generated_at_iso": datetime.utcnow().isoformat() + "Z",
        "inbox_dir": str(inbox_dir),
        "items_count": len(items),
        "items": items,
    }

    # Canonical manifest hash
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_sha256"] = sha256_bytes(canonical)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    return manifest


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate intake manifest for Bibliothèque inbox (receipts only)"
    )
    parser.add_argument("--inbox", default="oracle_town/inbox",
                       help="Inbox directory to manifest")
    parser.add_argument("--output", default="receipts/bibliotheque_intake_manifest.json",
                       help="Output manifest path")

    args = parser.parse_args()

    try:
        manifest = generate_manifest(inbox_dir=args.inbox, output_path=args.output)

        print(f"✅ Intake manifest generated: {args.output}")
        print(f"   Items in inbox: {manifest['items_count']}")
        print(f"   Manifest SHA256: {manifest['manifest_sha256']}")
        print()
        print("Next steps:")
        print("  1. Review items in oracle_town/inbox/")
        print("  2. Human + CI validate content")
        print("  3. Bot proposes integration PR (with manifest)")
        print("  4. Tribunal merges if receipts valid")

        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
