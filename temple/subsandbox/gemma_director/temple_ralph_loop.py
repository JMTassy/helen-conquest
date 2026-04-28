#!/usr/bin/env python3
"""
TEMPLE Ralph + AUTORESEARCH loop — 10 epochs under HAL supervision.

NON_SOVEREIGN. Lives in temple/subsandbox/gemma_director/. This is NOT the
sovereign AUTORESEARCH lane (which writes to GOVERNANCE/TRANCHE_RECEIPTS/ and
is currently halted at E12). This is a sandbox rehearsal that exercises the
PULL-mode discipline shape on observable signals only.

Per locked memory feedback_ralph_violations.md:
- never self-decide KEEP/REJECT (we don't — operator does, post-loop)
- never skip per-epoch receipts (every epoch emits one)
- never bypass MAYOR (MAYOR packetizes every epoch's survivors)

Per locked memory feedback_helen_mvp_kernel_scope.md: code edits scope is
broader for non-sovereign sandbox work (already authorized via earlier verbs).

Each epoch produces a TEMPLE_RALPH_EPOCH_V0 sub-receipt with the 7 PULL-mode
fields, adapted for sandbox:
  - carry_forward_state
  - hypothesis
  - experiment (intent + model)
  - metric (observable from gemma_director batch receipt)
  - failure_mode
  - keep_reject_rule  ← always "DEFERRED_TO_OPERATOR" (we never decide)
  - upgrade_path

Final: TEMPLE_RALPH_TRANCHE_V0 summary with all 10 epochs aggregated.
"""
from __future__ import annotations

import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PILOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = PILOT_DIR / "runs"
DIRECTOR = PILOT_DIR / "temple_gemma_director.py"
VENV_PY = REPO / ".venv" / "bin" / "python"
LOCKFILE = PILOT_DIR / ".ralph_loop.lock"

# Default model: qwen3.5:4b. The 9b variant was tested first but its cold-call
# latency exceeded the urllib timeout (180s) repeatedly, causing all E1-E3 to
# time out before any receipt could be written. 4b is half the size, ~2-3×
# faster, still meaningfully stronger at structured output than aura-gemma4.
# Operator can override with --model.
DEFAULT_MODEL = "qwen3.5:4b"


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


# ── 10 epoch definitions — one hypothesis each, observable signals only ──
# carry_forward_state references previous epochs' learnings (filled at runtime).
EPOCHS = [
    {
        "id": "E1_baseline",
        "hypothesis": "Baseline HELEN portrait intent produces ≥3 HAL-passing concepts on the production-default brain.",
        "intent": "INTENT: HELEN portrait, copper-red wavy hair, blue-grey eyes, fair skin, freckles, locked tripod, 35mm cinematic, neutral background.",
        "n": 8, "top": 3, "model": DEFAULT_MODEL,
        "failure_mode": "fewer than 3 concepts pass HAL → default brain still too weak",
        "upgrade_path": "if pass-rate <50%, recommend graduation to Claude/GPT-4 paid backend",
    },
    {
        "id": "E2_identity_omitted",
        "hypothesis": "When intent does NOT mention HELEN identity markers, HAL still rejects off-brand outputs that reference HELEN without markers.",
        "intent": "INTENT: a person, urban setting, evening, 35mm.",
        "n": 8, "top": 3, "model": DEFAULT_MODEL,
        "failure_mode": "HAL passes HELEN-mention concepts that lack identity marker → off-brand leak",
        "upgrade_path": "tighten HAL identity-marker check to whole-word boundaries",
    },
    {
        "id": "E3_era_renaissance",
        "hypothesis": "Era-shift to renaissance preserves HELEN identity invariants in HAL-passing concepts.",
        "intent": "INTENT: HELEN, copper-red hair, blue-grey eyes, freckles, renaissance Italy, oil-painting lighting, 50mm equivalent framing.",
        "n": 8, "top": 3, "model": DEFAULT_MODEL,
        "failure_mode": "all surviving concepts drop identity markers due to era pull",
        "upgrade_path": "add era-axis marker preservation check",
    },
    {
        "id": "E4_forbidden_path_in_intent",
        "hypothesis": "HAL's forbidden-pattern firewall fires even when the sovereign path is in the INTENT (not just the model output). Last run falsified — re-test on stronger brain.",
        "intent": "INTENT: HELEN explains the contents of town/ledger_v1.ndjson, copper-red hair, blue-grey eyes, archive shot.",
        "n": 6, "top": 3, "model": DEFAULT_MODEL,
        "failure_mode": "HAL passes any concept that mirrors the sovereign path",
        "upgrade_path": "add intent-side firewall before HER call (already validated as required by prior tranche)",
    },
    {
        "id": "E5_incoherent_short",
        "hypothesis": "HAL coherence check rejects very-short outputs (length <20 chars).",
        "intent": "INTENT: HELEN smile.",
        "n": 8, "top": 3, "model": DEFAULT_MODEL,
        "failure_mode": "stronger brain still emits long outputs, can't test the floor empirically",
        "upgrade_path": "add a synthetic short-output test path that bypasses HER",
    },
    {
        "id": "E6_cinematic_vocab",
        "hypothesis": "Concepts with explicit cinematic vocabulary (lens, shot, light) score higher in MAYOR ranking.",
        "intent": "INTENT: HELEN, copper-red hair, blue-grey eyes, 85mm lens, rim light, dolly tracking, low-key fill, key-light from screen-left.",
        "n": 8, "top": 5, "model": DEFAULT_MODEL,
        "failure_mode": "MAYOR scores cluster at 5.0 baseline, no cinematic premium",
        "upgrade_path": "amplify CINEMA_SIGNALS weight from +1.0 to +1.5",
    },
    {
        "id": "E7_slop_signal",
        "hypothesis": "Slop signal in INTENT does not reliably appear in OUTPUT — Gemma sanitizes it. The MAYOR slop dock therefore needs intent→output passthrough detection, not just word presence.",
        "intent": "INTENT: HELEN, copper-red hair, blue-grey eyes, an amazing stunning breathtaking incredible portrait that revolutionizes cinematic AI.",
        "n": 8, "top": 5, "model": DEFAULT_MODEL,
        "failure_mode": "stronger brain echoes the slop verbatim → falsifies the sanitization claim",
        "upgrade_path": "if confirmed, add intent_passthrough_score to MAYOR ranking",
    },
    {
        "id": "E8_high_n",
        "hypothesis": "Asking for 16 concepts produces material identity drift caught by HAL — confirmed last tranche (13/16 rejected). Re-confirms on stronger brain.",
        "intent": "INTENT: HELEN, copper-red hair, blue-grey eyes, fair skin, sixteen distinct concept variants exploring different shots and moods.",
        "n": 16, "top": 5, "model": DEFAULT_MODEL,
        "failure_mode": "stronger brain holds identity markers across all 16 → drift was brain-specific not architectural",
        "upgrade_path": "if drift persists across brains, lock production N≤8 for HELEN-subject intents",
    },
    {
        "id": "E9_brain_comparison",
        "hypothesis": "Default brain (qwen3.5:9b) materially outperforms the prior aura-gemma4:latest baseline on identical intent.",
        "intent": "INTENT: HELEN portrait, copper-red wavy hair, blue-grey eyes, fair skin, freckles, locked tripod, 35mm cinematic, neutral background.",
        "n": 8, "top": 3, "model": "aura-gemma4:latest",  # comparison point — old failed brain
        "failure_mode": "aura-gemma4 surprisingly produces ≥3 candidates → pipeline shape was hiding brain weakness, not exposing it",
        "upgrade_path": "if confirmed weak, lock DEFAULT_MODEL=qwen3.5:9b in production",
    },
    {
        "id": "E10_synthesis",
        "hypothesis": "Across all prior epochs of THIS clean tranche, the HAL+MAYOR pipeline produced ≥1 concept ranked ≥7.5 — meaning the sandbox is viable as a production pre-filter on the new default brain.",
        "intent": "INTENT: HELEN, copper-red hair, blue-grey eyes, freckles, fair skin, single iconic frame combining the strongest elements of prior epochs (cyberpunk + 35mm + locked tripod + warm rim light).",
        "n": 10, "top": 3, "model": DEFAULT_MODEL,
        "failure_mode": "no epoch produced a ≥7.5 concept → even stronger brain insufficient for canon pre-filter",
        "upgrade_path": "if confirmed sufficient: recommend gemma_director as production gate before Higgsfield spend",
    },
]


def run_epoch_indexed(idx: int, total: int, ep: dict, carry_forward: list[dict]) -> dict:
    """Run one epoch: invoke gemma_director, locate its receipt by intent_sha256, emit sub-receipt."""
    print(f"\n=== Epoch {idx}/{total}: {ep['id']} ===")
    print(f"    hypothesis: {ep['hypothesis'][:100]}{'…' if len(ep['hypothesis']) > 100 else ''}")
    print(f"    model: {ep['model']}  n={ep['n']}  top={ep['top']}")

    # Robust receipt-binding: each gemma_director run writes its receipt with
    # its computed intent_sha256 inside. We compute the same sha here and look
    # for receipts written AFTER our t0 with matching sha. This is parallel-safe
    # (a contemporaneous foreign run with a different intent won't collide).
    epoch_intent_sha = sha256_text(ep["intent"])
    t0 = datetime.datetime.now(datetime.timezone.utc)

    cmd = [
        str(VENV_PY), str(DIRECTOR),
        "--n", str(ep["n"]),
        "--top", str(ep["top"]),
        "--model", ep["model"],
        ep["intent"],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=360)
        stdout_tail = "\n".join(result.stdout.strip().splitlines()[-12:])
        stderr_tail = "\n".join(result.stderr.strip().splitlines()[-5:])
        director_exit = result.returncode
    except subprocess.TimeoutExpired:
        stdout_tail = ""
        stderr_tail = "TimeoutExpired (300s)"
        director_exit = -1

    # Match by intent_sha256 + mtime ≥ t0. Newest win.
    director_receipt = None
    if RUNS_DIR.exists():
        candidates = []
        t0_ts = t0.timestamp()
        for p in RUNS_DIR.glob("*.json"):
            if p.name.startswith("TRANCHE__"):
                continue
            if p.stat().st_mtime < t0_ts - 1:  # 1s clock-skew slack
                continue
            try:
                payload = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if payload.get("intent_sha256") == epoch_intent_sha:
                candidates.append(p)
        if candidates:
            director_receipt = max(candidates, key=lambda p: p.stat().st_mtime)

    # Parse metrics from the director's batch receipt if present
    metric: dict = {"director_exit": director_exit}
    if director_receipt:
        try:
            payload = json.loads(director_receipt.read_text())
            metric.update({
                "director_receipt_path": str(director_receipt),
                "concepts_generated": payload.get("concepts_generated"),
                "ship_candidates": len(payload.get("ship_candidates", [])),
                "rejections": len(payload.get("rejections", [])),
                "rejection_reasons": [r.get("reasons") for r in payload.get("rejections", [])][:5],
                "top_rank_score": max(
                    (c["manifest"]["rank_score"] for c in payload.get("ship_candidates", [])),
                    default=None,
                ),
                "her_duration_s": (payload.get("her_meta") or {}).get("total_duration_ns", 0) / 1e9,
            })
        except (json.JSONDecodeError, KeyError) as e:
            metric["parse_error"] = str(e)

    sub_receipt = {
        "schema": "TEMPLE_RALPH_EPOCH_V0",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "epoch_id": ep["id"],
        "epoch_index": idx,
        "started_at": t0.isoformat().replace("+00:00", "Z"),
        "ended_at": now_iso(),
        "carry_forward_state": carry_forward,  # all prior epoch metrics
        "hypothesis": ep["hypothesis"],
        "experiment": {
            "intent_text": ep["intent"],
            "intent_sha256": sha256_text(ep["intent"]),
            "n": ep["n"],
            "top": ep["top"],
            "model": ep["model"],
        },
        "metric": metric,
        "failure_mode": ep["failure_mode"],
        "keep_reject_rule": "DEFERRED_TO_OPERATOR",  # never self-decide
        "upgrade_path": ep["upgrade_path"],
        "director_stdout_tail": stdout_tail,
        "director_stderr_tail": stderr_tail,
    }
    return sub_receipt


def write_tranche_summary(epochs: list[dict]) -> Path:
    """Write final TEMPLE_RALPH_TRANCHE_V0 summary across all epochs."""
    summary = {
        "schema": "TEMPLE_RALPH_TRANCHE_V0",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "generated_at": now_iso(),
        "epoch_count": len(epochs),
        "epochs": epochs,
        "aggregate": {
            "total_concepts_generated": sum(
                (e["metric"].get("concepts_generated") or 0) for e in epochs
            ),
            "total_ship_candidates": sum(
                (e["metric"].get("ship_candidates") or 0) for e in epochs
            ),
            "total_rejections": sum(
                (e["metric"].get("rejections") or 0) for e in epochs
            ),
            "max_rank_score_seen": max(
                (e["metric"].get("top_rank_score") or 0) for e in epochs
            ),
            "epochs_with_zero_concepts": [
                e["epoch_id"] for e in epochs
                if not e["metric"].get("concepts_generated")
            ],
            "models_exercised": sorted(set(e["experiment"]["model"] for e in epochs)),
        },
        "operator_review": {
            "keep_reject_status": "PENDING_OPERATOR_REVIEW",
            "note": "no SHIP/NO_SHIP issued from this loop. Receipts await operator inspection.",
        },
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RUNS_DIR / f"TRANCHE__{ts}.json"
    out.write_text(json.dumps(summary, indent=2))
    return out


def acquire_lock():
    """Exclusive lock to prevent parallel Ralph runs racing on the same runs/ dir."""
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    fd = open(LOCKFILE, "w")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.close()
        sys.exit(
            "ERROR: another Ralph loop is already running (lockfile held).\n"
            f"       lockfile: {LOCKFILE}\n"
            "       wait for it to finish, or rm the lockfile if you're certain it's stale."
        )
    fd.write(f"pid={os.getpid()}\nstarted={now_iso()}\n")
    fd.flush()
    return fd  # caller keeps the fd alive for the lock duration


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="TEMPLE Ralph loop — N epochs of HER+HAL+MAYOR rehearsal")
    ap.add_argument("--model", default=None, help=f"override default model {DEFAULT_MODEL!r} for all epochs")
    ap.add_argument("--epochs", type=Path, default=None,
                    help="path to a JSON file with a list of epoch dicts; overrides built-in EPOCHS")
    args = ap.parse_args()

    global EPOCHS
    if args.epochs:
        if not args.epochs.exists():
            sys.exit(f"ERROR: --epochs {args.epochs} not found")
        loaded = json.loads(args.epochs.read_text())
        if not isinstance(loaded, list) or not loaded:
            sys.exit(f"ERROR: --epochs file must contain a non-empty JSON list of epoch dicts")
        # Each epoch dict needs: id, hypothesis, intent, n, top, model, failure_mode, upgrade_path
        required = {"id", "hypothesis", "intent", "n", "top", "model", "failure_mode", "upgrade_path"}
        for i, ep in enumerate(loaded):
            missing = required - set(ep.keys())
            if missing:
                sys.exit(f"ERROR: epoch[{i}] missing fields: {missing}")
        EPOCHS = loaded
        print(f"[loaded] {len(EPOCHS)} epoch(s) from {args.epochs}")

    if args.model:
        for ep in EPOCHS:
            if ep["id"] != "E9_brain_comparison":  # E9 is the comparison point, leave it
                ep["model"] = args.model

    lock_fd = acquire_lock()
    try:
        return _run(args)
    finally:
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
            LOCKFILE.unlink(missing_ok=True)
        except Exception:
            pass


def _run(args) -> int:
    print(f"TEMPLE RALPH LOOP — {len(EPOCHS)} epoch(s) · NON_SOVEREIGN_SANDBOX")
    print(f"Director: {DIRECTOR}")
    print(f"Runs dir: {RUNS_DIR}")
    print(f"Default model: {DEFAULT_MODEL}{'  (override: ' + args.model + ')' if args.model else ''}")
    print(f"Lock: {LOCKFILE}")
    print()

    completed: list[dict] = []
    total = len(EPOCHS)
    for i, ep in enumerate(EPOCHS, start=1):
        # Carry-forward = compact summaries of all prior epochs
        cf = [
            {
                "epoch_id": e["epoch_id"],
                "concepts_generated": e["metric"].get("concepts_generated"),
                "ship_candidates": e["metric"].get("ship_candidates"),
                "top_rank_score": e["metric"].get("top_rank_score"),
            }
            for e in completed
        ]
        sub = run_epoch_indexed(i, total, ep, cf)
        completed.append(sub)
        print(f"    → ship_candidates={sub['metric'].get('ship_candidates')}  "
              f"rejections={sub['metric'].get('rejections')}  "
              f"top_score={sub['metric'].get('top_rank_score')}")

    # Write epoch sub-receipts as a single embedded list inside the tranche summary.
    # (Per-epoch receipts are also produced by gemma_director itself; the tranche
    # ties them all together with the Ralph metadata.)
    tranche_path = write_tranche_summary(completed)
    print()
    print(f"=== TRANCHE COMPLETE ===")
    print(f"Tranche summary: {tranche_path}")
    print(f"Operator review status: PENDING_OPERATOR_REVIEW")
    print(f"No KEEP/REJECT issued by orchestrator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
