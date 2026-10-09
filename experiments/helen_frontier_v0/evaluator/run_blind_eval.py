"""CLI: run the provider-neutral blind evaluator on a *_blind.json fixture file.

  python -I run_blind_eval.py --adapter openai --blind ../swarm_v0/inputs/fixtures_blind_v1.json --out ./runs/codex_v1
  python -I run_blind_eval.py --adapter null  ...   (plumbing only; every oracle UNPARSEABLE)

The 'openai' binding is what the operator calls CODEX_EVALUATOR. Preconditions (not capabilities): OPENAI_API_KEY in
the environment, and the base URL host allowed by the network policy. Missing preconditions are reported, never mocked.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import NullAdapter, ResponsesAPIAdapter, run_blind_evaluation  # noqa: E402

HERE = Path(__file__).resolve().parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", choices=["openai", "null"], required=True)
    ap.add_argument("--blind", type=Path, default=HERE.parent / "swarm_v0" / "inputs" / "fixtures_blind_v1.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seat", default="CODEX_EVALUATOR")
    ap.add_argument("--temperature", type=float, default=0.0)
    a = ap.parse_args(argv)
    if a.adapter == "openai":
        ad = ResponsesAPIAdapter()
        pre = ad.preconditions()
        if not pre["api_key_present"]:
            print(json.dumps({"status": "PRECONDITION_FAILED", "missing": ad.api_key_env, "host": pre["host"],
                              "note": "add the key as an environment secret; nothing was mocked"}, indent=1))
            return 2
    else:
        ad = NullAdapter(); a.seat = a.seat + "_NULL_PLUMBING"
    po, pr = run_blind_evaluation(ad, a.blind, a.out, seat=a.seat, temperature=a.temperature)
    rec = json.loads(pr.read_text())
    print(f"outcomes → {po}\nreceipt  → {pr}\nevaluated {rec['observed']['oracles_evaluated']} · unparseable {rec['observed']['unparseable']} · hosts {rec['observed']['hosts_contacted']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
