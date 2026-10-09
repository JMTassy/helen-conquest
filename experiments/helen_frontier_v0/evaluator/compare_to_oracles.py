"""After the fact: compare a blind_outcomes.json to the frozen V1 oracles. Not part of the evaluator; runs separately.
Reports per-oracle match, and treats mismatches as data about both sides. Never a verdict."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "fixtures" / "jester_riemann_fixtures_v1.json"


def expected_map(fx: dict) -> dict[str, dict]:
    out = {}
    for f in fx["fixtures"]:
        for v in (f.get("variants") or [f]):
            out[v["id"]] = v["expected"]
    return out


def compare(outcomes: dict, fx: dict) -> dict:
    exp = expected_map(fx)
    rows, matches = [], 0
    for o in outcomes["outcomes"]:
        e = exp.get(o["id"])
        match = bool(e) and o["outcome"] == e["outcome"] and o["state_transition"] == e["state_transition"]
        matches += match
        rows.append({"id": o["id"], "expected": e["outcome"] if e else None, "got": o["outcome"], "match": match})
    return {"schema": "ORACLE_COMPARISON_V0", "authority": False, "evaluator": outcomes.get("evaluator"),
            "n": len(rows), "matches": matches, "mismatches": [r for r in rows if not r["match"]], "rows": rows,
            "interpretation": "a mismatch is data about the oracle as much as about the evaluator; adjudicate blind"}


def main(argv=None) -> int:
    p = Path(argv[0] if argv else sys.argv[1])
    rep = compare(json.loads(p.read_text()), json.loads(V1.read_text()))
    (p.parent / "oracle_comparison.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n")
    print(f"{rep['matches']}/{rep['n']} match · mismatches: {[r['id'] for r in rep['mismatches']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
