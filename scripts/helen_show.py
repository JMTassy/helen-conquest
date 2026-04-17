#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEM = ROOT / "helen_memory.json"
WIS = ROOT / "helen_wisdom.ndjson"

def load_memory():
    if not MEM.exists():
        return {"version": "HELEN_MEM_V0", "facts": {}}
    return json.loads(MEM.read_text(encoding="utf-8"))

def load_wisdom(limit=10):
    if not WIS.exists():
        return []
    lines = []
    for line in WIS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            # skip malformed lines
            continue
    return lines[-limit:]

def main():
    mem = load_memory()
    wis = load_wisdom(10)

    print("=== HELEN (LNSA) — MEMORY ===")
    facts = mem.get("facts", {})
    if not facts:
        print("(no facts yet)")
    else:
        for k, v in facts.items():
            print(f"- {k}: {v}")

    print("\n=== HELEN (LNSA) — WISDOM (last 10) ===")
    if not wis:
        print("(no wisdom yet)")
    else:
        for w in wis:
            t = w.get("t", "?")
            kind = w.get("kind", "lesson")
            lesson = w.get("lesson", "")
            evidence = w.get("evidence", "")
            status = w.get("status", "ACTIVE")
            print(f"- [{t}] ({kind}/{status}) {lesson}")
            if evidence:
                print(f"  evidence: {evidence}")

if __name__ == "__main__":
    main()
