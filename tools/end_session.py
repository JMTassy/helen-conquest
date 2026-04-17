#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.ndjson_writer import NDJSONWriter

def main():
    if len(sys.argv) < 6:
        raise SystemExit("Usage: tools/end_session.py <ledger_path> <run_id> <kernel_hash> <policy_hash> [SHIP|ABORT] [reason_code,...]")

    ledger_path, run_id, kernel_hash, policy_hash = sys.argv[1:5]
    outcome = sys.argv[5] if len(sys.argv) >= 6 else "SHIP"
    reasons = sys.argv[6].split(",") if len(sys.argv) >= 7 else ["SESSION_CLOSED"]
    reasons = sorted([r.strip() for r in reasons if r.strip()])

    # Scan existing ledger to get last seq and cum_hash
    seq = 0
    prev = "0" * 64
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                seq = obj["seq"] + 1
                prev = obj["cum_hash"]
    except FileNotFoundError:
        pass

    w = NDJSONWriter(path=ledger_path, seq=seq, prev_cum_hash=prev)

    payload = {
        "schema": "SEAL_V1",
        "outcome": outcome,
        "reason_codes": reasons,
        "refs": {
            "run_id": run_id,
            "kernel_hash": kernel_hash,
            "policy_hash": policy_hash,
            "final_ledger_cum_hash": prev,
        },
    }
    meta = {"note": "session end", "timestamp_utc": "wallclock_ok_meta_only"}

    w.append_event("seal", payload, meta)
    print(f"[OK] sealed {outcome} at {ledger_path}")

if __name__ == "__main__":
    main()
