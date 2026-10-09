"""Preregistered scorer. Joins scores.json (labels never seen by the runner) with G2 labels and applies the frozen rule.

Pure: no model, no network. Threshold-free AUC; disagreement = EQUIVALENT below the overall median or DIFFERENT above it.
Produces a table and a list, never a verdict.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PAIRS = REPO / "experiments/helen_frontier_v0/swarm_v0/G2_EQUIVALENCE_ANNOTATOR/equivalence_pairs.json"
EQ, DF = "EQUIVALENT_DISTINCTION", "DIFFERENT_DISTINCTION"


def auc(pos: list[float], neg: list[float]) -> float:
    if not pos or not neg:
        return float("nan")
    s = 0.0
    for p in pos:
        for n in neg:
            s += 1.0 if p > n else 0.5 if p == n else 0.0
    return s / (len(pos) * len(neg))


def score(scores: dict, labels: list[dict], dim_key: str = "score_768") -> dict:
    by_idx = {p["pair_index"]: p for p in scores["pairs"]}
    rows = []
    for i, lab in enumerate(labels):
        sc = by_idx[i][dim_key]
        rows.append({"pair_index": i, "a": lab["a"], "b": lab["b"], "label": lab["label"], "score": sc})
    allsc = [r["score"] for r in rows]
    med = statistics.median(allsc)
    pos = [r["score"] for r in rows if r["label"] == EQ]
    neg = [r["score"] for r in rows if r["label"] == DF]
    for r in rows:
        r["disagreement"] = (r["label"] == EQ and r["score"] < med) or (r["label"] == DF and r["score"] > med)
    dis = [r for r in rows if r["disagreement"]]
    return {
        "schema": "G2_EMBEDDING_SCORED_V0", "authority": False, "ledger_effect": "none", "dim": dim_key,
        "n_pairs": len(rows), "median_all": med, "auc_equivalent_vs_different": auc(pos, neg),
        "n_disagreements": len(dis),
        "disagreements": [{k: r[k] for k in ("pair_index", "a", "b", "label", "score")} for r in dis],
        "rows": rows,
        "interpretation": "disagreements are signals for blinded adjudication, not evidence that either side is right",
    }


def main() -> int:
    scores = json.loads((HERE / "scores.json").read_text(encoding="utf-8"))
    labels = json.loads(PAIRS.read_text(encoding="utf-8"))["pairs"]
    for dim_key in ("score_768", "score_256"):
        rep = score(scores, labels, dim_key)
        rep["observed_from_runner"] = scores.get("observed")
        rep["asserted_from_runner"] = scores.get("asserted")
        (HERE / f"scored_report_{dim_key[-3:]}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{dim_key}: AUC={rep['auc_equivalent_vs_different']:.3f} · disagreements={rep['n_disagreements']} / {rep['n_pairs']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
