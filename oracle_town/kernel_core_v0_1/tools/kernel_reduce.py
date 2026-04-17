#!/usr/bin/env python3
# Minimal deterministic kernel reducer (v0.1)
# Input: event.json (turn payload), output: PASS/BLOCK decision only.

import json
import sys


def reduce_turn(turn_payload: dict) -> dict:
    hal = turn_payload.get("hal", {})
    verdict = hal.get("verdict", "BLOCK")
    ship = True if verdict == "PASS" else False
    return {"ship": ship, "verdict": verdict}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: kernel_reduce.py <turn_payload.json>")
        return 2
    payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
    out = reduce_turn(payload)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["ship"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
