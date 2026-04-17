#!/usr/bin/env python3
# Validate payload_hash + cum_hash chain for EVENT_V1 NDJSON.

import json
import sys
from pathlib import Path

from canon import canon, sha256_hex, sha256_hex_bytes


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_hash_chain.py <ledger.ndjson>")
        return 2
    path = Path(sys.argv[1])
    prev = "0" * 64
    idx = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        payload = ev.get("payload")
        if payload is None:
            print(f"Line {idx}: missing payload")
            return 1
        expected_payload_hash = sha256_hex(canon(payload))
        if ev.get("payload_hash") != expected_payload_hash:
            print(f"Line {idx}: payload_hash mismatch")
            return 1
        if ev.get("prev_cum_hash") != prev:
            print(f"Line {idx}: prev_cum_hash mismatch")
            return 1
        expected_cum = sha256_hex_bytes(bytes.fromhex(prev) + bytes.fromhex(expected_payload_hash))
        if ev.get("cum_hash") != expected_cum:
            print(f"Line {idx}: cum_hash mismatch")
            return 1
        prev = expected_cum
        idx += 1
    print("HASH_CHAIN_VALIDATE: PASS")
    print(f" events={idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
