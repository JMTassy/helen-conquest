"""Append-only NDJSON event log."""
from __future__ import annotations

import json
import os
from pathlib import Path

from helen_os.ledger.hash_chain import canonical_json


def append_event(path: str | os.PathLike, event: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(canonical_json(event).decode("utf-8") + "\n")


def read_events(path: str | os.PathLike) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out
