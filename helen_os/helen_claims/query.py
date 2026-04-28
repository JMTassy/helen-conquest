# lifecycle: CANDIDATE
"""query subcommand — substring search over index entries."""
from __future__ import annotations

from .index import iter_entries


def query(args) -> int:
    needle = args.needle
    if not needle:
        print("REFUSED: query needle is empty")
        return 2
    needle_l = needle.lower()
    hits = 0
    for entry in iter_entries():
        haystack = " ".join(
            str(entry.get(k, "")) for k in ("preserved_tag", "domain", "keyword", "out_path")
        ).lower()
        if needle_l in haystack:
            hits += 1
            tag = entry.get("preserved_tag", "?")
            domain = entry.get("domain", "?")
            out_path = entry.get("out_path", "?")
            print(f"{tag}  [{domain}]  -> {out_path}")
    if hits == 0:
        print(f"TAG_NOT_FOUND: no entries match '{needle}'")
        return 1
    print(f"--- {hits} match(es)")
    return 0
