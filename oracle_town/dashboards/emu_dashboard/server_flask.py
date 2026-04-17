#!/usr/bin/env python3
"""
Oracle Town Emulation Dashboard — Flask server.

Usage:
  pip install flask
  export LEDGER_ROOT="oracle_town/ledger"
  export TMP_ROOT="/tmp"
  python3 oracle_town/dashboards/emu_dashboard/server_flask.py
  # open http://127.0.0.1:5005
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

from flask import Flask, jsonify, send_from_directory, request

HERE = Path(__file__).resolve().parent
VIEWS = HERE / "views"
STATIC = HERE / "static"

LEDGER_ROOT = Path(os.environ.get("LEDGER_ROOT", "oracle_town/ledger")).resolve()
TMP_ROOT = Path(os.environ.get("TMP_ROOT", "/tmp")).resolve()

app = Flask(__name__)

def iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

def read_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None

def list_ledger_runs(limit: int = 50) -> List[Dict[str, Any]]:
    items: List[Tuple[float, Path]] = []
    if not LEDGER_ROOT.exists():
        return []
    for y in LEDGER_ROOT.glob("*"):
        if not y.is_dir():
            continue
        for m in y.glob("*"):
            if not m.is_dir():
                continue
            for claim_dir in m.glob("*"):
                if claim_dir.is_dir():
                    try:
                        mt = claim_dir.stat().st_mtime
                    except Exception:
                        mt = 0.0
                    items.append((mt, claim_dir))
    items.sort(key=lambda t: t[0], reverse=True)
    out = []
    for mt, p in items[:limit]:
        out.append({"claim_id": p.name, "path": str(p), "mtime": iso(mt)})
    return out

def load_run_dir(claim_dir: Path) -> Dict[str, Any]:
    claim = (read_json(claim_dir / "claim.json") or
             read_json(claim_dir / "claim_raw.json") or
             read_json(claim_dir / "claim_payload.json"))
    tri = (read_json(claim_dir / "tri_verdict.json") or
           read_json(claim_dir / "verdict.json"))
    receipt = (read_json(claim_dir / "receipt.json") or
               read_json(claim_dir / "mayor_receipt.json"))
    return {
        "claim_id": claim_dir.name,
        "path": str(claim_dir),
        "claim": claim,
        "tri_verdict": tri,
        "receipt": receipt
    }

def load_latest() -> Dict[str, Any]:
    candidates = {
        "brief": [
            "brf_out.json",
            "brf_onepager_output.json",
            "brf_output.json",
            "brief.json"
        ],
        "insights": [
            "ins_out.json",
            "ins_cluster_output.json",
            "insights.json"
        ],
        "tri": [
            "tri_verdict.json",
            "tri_output.json"
        ],
        "trend": [
            "trend_report.json"
        ],
        "receipt": [
            "receipt.json",
            "mayor_receipt.json"
        ],
    }

    def pick(names):
        for n in names:
            p = TMP_ROOT / n
            if p.exists():
                return p
        return None

    brief_p = pick(candidates["brief"])
    insights_p = pick(candidates["insights"])
    tri_p = pick(candidates["tri"])
    trend_p = pick(candidates["trend"])
    receipt_p = pick(candidates["receipt"])

    brief = read_json(brief_p) if brief_p else None
    insights = read_json(insights_p) if insights_p else None
    tri = read_json(tri_p) if tri_p else None
    trend = read_json(trend_p) if trend_p else None
    receipt = read_json(receipt_p) if receipt_p else None

    one_bet = None
    if isinstance(brief, dict):
        for k in ("one_bet", "ONE_BET", "oneBet"):
            if k in brief and isinstance(brief[k], str):
                one_bet = brief[k]
                break

    mtimes = []
    for p in (brief_p, insights_p, tri_p, trend_p, receipt_p):
        if p and p.exists():
            try:
                mtimes.append(p.stat().st_mtime)
            except Exception:
                pass

    return {
        "available": bool(brief or insights or tri or trend or receipt),
        "source": str(TMP_ROOT),
        "updated_at": iso(max(mtimes)) if mtimes else None,
        "one_bet": one_bet,
        "brief": brief,
        "insights": insights,
        "tri_verdict": tri,
        "trend": trend,
        "receipt": receipt,
    }

@app.get("/")
def index():
    return send_from_directory(VIEWS, "index.html")

@app.get("/static/<path:filename>")
def static_files(filename: str):
    return send_from_directory(STATIC, filename)

@app.get("/api/status")
def status():
    return jsonify({
        "ok": True,
        "version": "emu-dashboard-flask-0.1",
        "ledger_root": str(LEDGER_ROOT),
        "tmp_root": str(TMP_ROOT),
        "now": iso(time.time()),
        "ledger_exists": LEDGER_ROOT.exists(),
    })

@app.get("/api/latest")
def latest():
    return jsonify(load_latest())

@app.get("/api/runs")
def runs():
    try:
        limit = int(request.args.get("limit", "50"))
        limit = max(1, min(limit, 500))
    except Exception:
        limit = 50
    items = list_ledger_runs(limit=limit)
    return jsonify({"items": items, "count": len(items)})

@app.get("/api/run/<claim_id>")
def run_detail(claim_id: str):
    if "/" in claim_id or ".." in claim_id:
        return jsonify({"error": "bad claim_id"}), 400

    found = None
    for y in LEDGER_ROOT.glob("*"):
        for m in y.glob("*"):
            cand = m / claim_id
            if cand.exists() and cand.is_dir():
                found = cand
                break
        if found:
            break

    if not found:
        return jsonify({"error": "not found", "claim_id": claim_id}), 404

    return jsonify(load_run_dir(found))

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5005"))
    print(f"[emu-dashboard] flask server on http://{host}:{port}")
    print(f"[emu-dashboard] ledger_root={LEDGER_ROOT}")
    print(f"[emu-dashboard] tmp_root={TMP_ROOT}")
    app.run(host=host, port=port, debug=False)
