#!/usr/bin/env python3
"""
ORACLE TOWN — State Normalizer (Canonical Format)
Loads a JSON state file and rewrites it with canonical formatting:
- Sorted keys (stable diffs)
- 2-space indents
- Trailing newline
- UTF-8 encoding

Usage:
  python3 oracle_town/normalize_state.py <input.json>
  python3 oracle_town/normalize_state.py --in oracle_town/state/city_current.json --out oracle_town/state/city_current.json
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

MODULE_ORDER = ["OBS", "INS", "BRF", "TRI", "PUB", "MEM", "EVO"]


class CanonicalEncoder(json.JSONEncoder):
    """JSON encoder that sorts all keys except modules (which use fixed MODULE_ORDER)."""

    def encode(self, o):
        # Override to sort top-level keys
        if isinstance(o, dict):
            o = self._sort_dict(o)
        return super().encode(o)

    def iterencode(self, o, _one_shot=False):
        # Override for pretty printing to sort keys at each level
        if isinstance(o, dict):
            o = self._sort_dict(o)
        return super().iterencode(o, _one_shot)

    def _sort_dict(self, d):
        """Sort dict keys, except modules which use fixed order."""
        result = {}
        for key in sorted(d.keys()):
            value = d[key]
            if key == "modules" and isinstance(value, dict):
                # Preserve MODULE_ORDER for modules
                modules = {}
                for m in MODULE_ORDER:
                    if m in value:
                        modules[m] = value[m]
                result[key] = modules
            elif isinstance(value, dict):
                result[key] = self._sort_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self._sort_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


def normalize_json(data: dict) -> str:
    """Serialize to canonical JSON format (sorted keys, 2-space indent, trailing newline).

    Special handling: preserve MODULE_ORDER for the modules dict (I5 invariant).
    """
    return json.dumps(
        data, cls=CanonicalEncoder, indent=2, ensure_ascii=True
    ) + "\n"


def normalize_file(input_path: Path, output_path: Path | None = None) -> None:
    """Load JSON, normalize, and write back (or to new location)."""
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    # Load original JSON
    try:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Write normalized version
    output = output_path or input_path
    canonical = normalize_json(data)
    with output.open("w", encoding="utf-8") as f:
        f.write(canonical)

    # Report
    if output == input_path:
        print(f"✓ Normalized (in-place): {input_path}")
    else:
        print(f"✓ Normalized: {input_path} → {output}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Normalize JSON state files to canonical format"
    )
    ap.add_argument(
        "input",
        nargs="?",
        help="Input JSON file (if no --in given)",
    )
    ap.add_argument(
        "--in",
        dest="in_file",
        help="Input JSON file (explicit option)",
    )
    ap.add_argument(
        "--out",
        dest="out_file",
        help="Output JSON file (default: overwrite input)",
    )
    args = ap.parse_args()

    # Determine input path
    input_arg = args.in_file or args.input
    if not input_arg:
        ap.print_help()
        sys.exit(1)

    input_path = Path(input_arg)
    output_path = Path(args.out_file) if args.out_file else None

    normalize_file(input_path, output_path)


if __name__ == "__main__":
    main()
