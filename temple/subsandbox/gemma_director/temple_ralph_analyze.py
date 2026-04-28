#!/usr/bin/env python3
"""
TEMPLE Ralph tranche analyzer — extracts the 5-criterion report.

NON_SOVEREIGN. Reads a TRANCHE_*.json file (TEMPLE_RALPH_TRANCHE_V0 schema),
opens its referenced gemma_director receipts to deepen the analysis, and
prints the five criteria the operator wants:

  1. pass/fail count       (per-epoch + aggregate)
  2. best concept          (highest MAYOR rank_score, full text + epoch)
  3. model comparison      (per-model aggregate metrics)
  4. HAL behavior          (rejection signatures, identity-marker fires, forbidden-pattern fires)
  5. default-model recommendation

Usage:
    python3 temple/subsandbox/gemma_director/temple_ralph_analyze.py
    python3 temple/subsandbox/gemma_director/temple_ralph_analyze.py path/to/TRANCHE_*.json
    python3 temple/subsandbox/gemma_director/temple_ralph_analyze.py --latest
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = PILOT_DIR / "runs"


def load_director_receipt(path_str: str | None) -> dict | None:
    if not path_str:
        return None
    p = Path(path_str)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def latest_tranche() -> Path | None:
    candidates = sorted(RUNS_DIR.glob("TRANCHE__*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def analyze(tranche: dict) -> dict:
    epochs = tranche.get("epochs", [])
    aggregate = tranche.get("aggregate", {})

    # --- 1. pass/fail count ---
    per_epoch = []
    pass_n = 0
    fail_n = 0
    for ep in epochs:
        m = ep.get("metric", {})
        cands = m.get("ship_candidates")
        gen = m.get("concepts_generated")
        # "pass" = the epoch produced ≥1 ship_candidate
        is_pass = bool(cands and cands > 0)
        per_epoch.append({
            "id": ep.get("epoch_id", "?"),
            "model": ep.get("experiment", {}).get("model"),
            "concepts": gen,
            "candidates": cands,
            "rejections": m.get("rejections"),
            "top_score": m.get("top_rank_score"),
            "pass": is_pass,
        })
        if is_pass:
            pass_n += 1
        else:
            fail_n += 1

    # --- 2. best concept across all epochs ---
    best = {"score": -1.0, "epoch_id": None, "concept": None}
    for ep in epochs:
        m = ep.get("metric", {})
        rcpt = load_director_receipt(m.get("director_receipt_path"))
        if not rcpt:
            continue
        for cand in rcpt.get("ship_candidates", []):
            score = cand.get("manifest", {}).get("rank_score", -1)
            if score > best["score"]:
                best = {
                    "score": score,
                    "epoch_id": ep.get("epoch_id"),
                    "model": ep.get("experiment", {}).get("model"),
                    "concept": cand.get("manifest", {}).get("concept_text", "?"),
                }

    # --- 3. model comparison (aggregate per model) ---
    by_model: dict[str, dict] = defaultdict(lambda: {
        "epochs_run": 0, "epochs_pass": 0,
        "concepts_total": 0, "candidates_total": 0,
        "rejections_total": 0, "max_score": 0.0,
    })
    for ep in epochs:
        model = ep.get("experiment", {}).get("model", "?")
        m = ep.get("metric", {})
        b = by_model[model]
        b["epochs_run"] += 1
        if (m.get("ship_candidates") or 0) > 0:
            b["epochs_pass"] += 1
        b["concepts_total"] += m.get("concepts_generated") or 0
        b["candidates_total"] += m.get("ship_candidates") or 0
        b["rejections_total"] += m.get("rejections") or 0
        ts = m.get("top_rank_score") or 0
        if ts and ts > b["max_score"]:
            b["max_score"] = ts

    # --- 4. HAL behavior ---
    reason_counts: Counter[str] = Counter()
    for ep in epochs:
        m = ep.get("metric", {})
        for reasons in (m.get("rejection_reasons") or []):
            for r in reasons:
                reason_counts[r] += 1
    # Also count from director receipts directly (more complete than orchestrator's preview)
    full_reasons: Counter[str] = Counter()
    forbidden_hits: list[str] = []
    for ep in epochs:
        rcpt = load_director_receipt(ep.get("metric", {}).get("director_receipt_path"))
        if not rcpt:
            continue
        for rej in rcpt.get("rejections", []):
            for r in rej.get("reasons", []):
                full_reasons[r] += 1
                if r.startswith("forbidden_pattern:"):
                    forbidden_hits.append(r)

    # --- 5. recommendation ---
    # Pick the model with the highest pass-rate AND highest max_score; if tied, prefer
    # higher candidates_total. Skip models with 0 epochs.
    rec_model = None
    rec_reason = ""
    if by_model:
        ranked = sorted(
            by_model.items(),
            key=lambda kv: (
                kv[1]["epochs_pass"] / max(kv[1]["epochs_run"], 1),
                kv[1]["max_score"],
                kv[1]["candidates_total"],
            ),
            reverse=True,
        )
        top_model, top_metrics = ranked[0]
        rec_model = top_model
        pass_rate = top_metrics["epochs_pass"] / max(top_metrics["epochs_run"], 1)
        rec_reason = (
            f"highest pass-rate {pass_rate*100:.0f}% across {top_metrics['epochs_run']} epochs, "
            f"max_score={top_metrics['max_score']}, candidates_total={top_metrics['candidates_total']}"
        )

    return {
        "tranche_meta": {
            "epoch_count": tranche.get("epoch_count"),
            "generated_at": tranche.get("generated_at"),
            "authority_status": tranche.get("authority_status"),
        },
        "criterion_1_pass_fail": {
            "pass": pass_n,
            "fail": fail_n,
            "per_epoch": per_epoch,
        },
        "criterion_2_best_concept": best,
        "criterion_3_model_comparison": dict(by_model),
        "criterion_4_hal_behavior": {
            "rejection_reasons_orchestrator_preview": dict(reason_counts),
            "rejection_reasons_full": dict(full_reasons),
            "forbidden_pattern_hits": forbidden_hits,
        },
        "criterion_5_recommendation": {
            "default_model": rec_model,
            "rationale": rec_reason,
        },
    }


def render_report(report: dict) -> str:
    lines: list[str] = []
    meta = report["tranche_meta"]
    lines.append(f"# TEMPLE RALPH TRANCHE — 5-CRITERION REPORT")
    lines.append(f"epochs: {meta['epoch_count']}  generated: {meta['generated_at']}  authority: {meta['authority_status']}")
    lines.append("")

    # 1
    c1 = report["criterion_1_pass_fail"]
    lines.append(f"## 1. PASS / FAIL")
    lines.append(f"   pass: {c1['pass']}   fail: {c1['fail']}")
    for e in c1["per_epoch"]:
        mark = "✓" if e["pass"] else "✗"
        lines.append(
            f"   {mark} {e['id']:30s} model={e['model']:24s} concepts={e['concepts']!s:>4} "
            f"cands={e['candidates']!s:>3} rejs={e['rejections']!s:>3} top={e['top_score']}"
        )
    lines.append("")

    # 2
    c2 = report["criterion_2_best_concept"]
    lines.append(f"## 2. BEST CONCEPT")
    if c2.get("epoch_id"):
        lines.append(f"   score: {c2['score']}    epoch: {c2['epoch_id']}    model: {c2['model']}")
        lines.append(f"   concept: {c2['concept']}")
    else:
        lines.append("   (no concept survived to a candidate; see HAL behavior)")
    lines.append("")

    # 3
    c3 = report["criterion_3_model_comparison"]
    lines.append(f"## 3. MODEL COMPARISON")
    if not c3:
        lines.append("   (no model data)")
    for model, m in c3.items():
        pr = m["epochs_pass"] / max(m["epochs_run"], 1) * 100
        lines.append(
            f"   {model:28s}  epochs={m['epochs_run']}  pass={m['epochs_pass']} ({pr:.0f}%)  "
            f"concepts={m['concepts_total']}  cands={m['candidates_total']}  rejs={m['rejections_total']}  max_score={m['max_score']}"
        )
    lines.append("")

    # 4
    c4 = report["criterion_4_hal_behavior"]
    lines.append(f"## 4. HAL BEHAVIOR")
    full = c4["rejection_reasons_full"]
    if full:
        lines.append("   rejection reasons (counts):")
        for r, n in sorted(full.items(), key=lambda kv: -kv[1]):
            lines.append(f"     {n:3d} × {r}")
    else:
        lines.append("   (no rejections recorded — either HAL passed everything or no concepts to gate)")
    if c4["forbidden_pattern_hits"]:
        lines.append("   forbidden-pattern fires:")
        for hit in c4["forbidden_pattern_hits"][:10]:
            lines.append(f"     - {hit}")
    lines.append("")

    # 5
    c5 = report["criterion_5_recommendation"]
    lines.append(f"## 5. DEFAULT-MODEL RECOMMENDATION")
    if c5.get("default_model"):
        lines.append(f"   recommend: {c5['default_model']}")
        lines.append(f"   why:        {c5['rationale']}")
    else:
        lines.append("   (no recommendation — insufficient data)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze a TEMPLE Ralph TRANCHE")
    ap.add_argument("tranche_path", nargs="?", help="path to TRANCHE_*.json (default: --latest)")
    ap.add_argument("--latest", action="store_true", help="auto-pick the most recent TRANCHE in runs/")
    ap.add_argument("--json", action="store_true", help="emit raw JSON instead of human-readable report")
    args = ap.parse_args()

    if args.tranche_path:
        path = Path(args.tranche_path)
    else:
        path = latest_tranche()
        if not path:
            print(f"ERROR: no TRANCHE_*.json in {RUNS_DIR}", file=sys.stderr)
            return 2

    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 2

    print(f"# source: {path}", file=sys.stderr)
    tranche = json.loads(path.read_text())
    report = analyze(tranche)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
