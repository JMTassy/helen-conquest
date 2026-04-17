#!/usr/bin/env python3
# Append a single EVENT_V1 record with canonical payload hashing.

import json
import sys
from pathlib import Path

from canon import canon, sha256_hex, sha256_hex_bytes


def read_last_cum_hash(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "0" * 64
    last = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    if not last:
        return "0" * 64
    return last["cum_hash"]


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: ndjson_append.py <ledger.ndjson> <event.json>")
        return 2
    ledger_path = Path(sys.argv[1])
    event_path = Path(sys.argv[2])
    event = json.loads(event_path.read_text(encoding="utf-8"))

    payload = event.get("payload")
    if payload is None:
        print("ERROR: event missing payload", file=sys.stderr)
        return 1

    payload_hash = sha256_hex(canon(payload))
    prev_cum = read_last_cum_hash(ledger_path)
    cum_hash = sha256_hex_bytes(bytes.fromhex(prev_cum) + bytes.fromhex(payload_hash))

    event["payload_hash"] = payload_hash
    event["prev_cum_hash"] = prev_cum
    event["cum_hash"] = cum_hash

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
