#!/usr/bin/env python3
# lifecycle: CANDIDATE
"""helen_claims CLI entry point.

Usage:
    python -m helen_claims classify <source>... [--limit N] [--no-dry-run]
    python -m helen_claims query <substring>
    python -m helen_claims validate [<path>]

Defaults:
    classify is dry-run by default. Pass --no-dry-run to actually write.
    classify hard-cap is 20 sources per invocation (--limit, default 5).
    PDF sources are refused in v0.1; pre-convert to .txt.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .classify import classify
from .query import query
from .validate import validate


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="helen_claims",
        description=f"helen_claims v{__version__} (CANDIDATE) — KNOWLEDGE_ENTRY classifier for HELEN #plugin corpus.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("classify", help="Read source(s), emit DRAFT KNOWLEDGE_ENTRY scaffold.")
    c.add_argument("sources", nargs="+", help="Source file path(s). PDFs refused in v0.1.")
    c.add_argument("--limit", type=int, default=5, help="Hard cap on sources per invocation (default 5, max 20).")
    c.add_argument("--no-dry-run", dest="dry_run", action="store_false",
                   help="Actually write files. Default is dry-run.")
    c.set_defaults(dry_run=True)

    q = sub.add_parser("query", help="Substring search over the index.")
    q.add_argument("needle", help="Substring to match against preserved_tag/domain/keyword/out_path.")

    v = sub.add_parser("validate", help="Lint a classified entry (or all entries).")
    v.add_argument("path", nargs="?", default="", help="Optional path to a single classified .md.")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "classify":
        if args.limit > 20:
            print("REFUSED: --limit hard-capped at 20 (operator-locked anti-bulk discipline)", file=sys.stderr)
            return 2
        return classify(args)
    if args.cmd == "query":
        return query(args)
    if args.cmd == "validate":
        return validate(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
