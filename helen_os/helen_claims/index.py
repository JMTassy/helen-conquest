# lifecycle: CANDIDATE
"""JSONL index over classified KNOWLEDGE_ENTRY artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

INDEX_PATH = Path(__file__).parent / "index.jsonl"


def append(entry: dict) -> None:
    """Append one classification entry to index.jsonl. Atomic per-line."""
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def iter_entries() -> Iterator[dict]:
    """Stream all index entries. Yields nothing if index does not exist."""
    if not INDEX_PATH.exists():
        return
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
