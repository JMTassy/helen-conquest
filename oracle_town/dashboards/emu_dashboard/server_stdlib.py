#!/usr/bin/env python3
"""
Oracle Town Emulation Dashboard — stdlib-only server (no dependencies).

Usage:
  export LEDGER_ROOT="oracle_town/ledger"
  export TMP_ROOT="/tmp"
  python3 oracle_town/dashboards/emu_dashboard/server_stdlib.py
  # open http://127.0.0.1:5005
"""

import json
import os
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
VIEWS = HERE / "views"
STATIC = HERE / "static"

DEFAULT_LEDGER_ROOT = os.environ.get("LEDGER_ROOT", "oracle_town/ledger")
DEFAULT_TMP_ROOT = os.environ.get("TMP_ROOT", "/tmp")

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

def list_ledger_runs(ledger_root: Path, limit: int = 50) -> List[Dict[str, Any]]:
    items: List[Tuple[float, Path]] = []
    if not ledger_root.exists():
        return []
    for y in ledger_root.glob("*"):
        if not y.is_dir(): continue
        for m in y.glob("*"):
            if not m.is_dir(): continue
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
        out.append({
            "claim_id": p.name,
            "path": str(p),
            "mtime": iso(mt),
        })
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
        "receipt": receipt,
    }

def load_latest(tmp_root: Path) -> Dict[str, Any]:
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

    def pick(names: List[str]) -> Optional[Path]:
        for n in names:
            p = tmp_root / n
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

    # Extract ONE BET
    one_bet = None
    if isinstance(brief, dict):
        for k in ("one_bet", "ONE_BET", "oneBet"):
            if k in brief and isinstance(brief[k], str):
                one_bet = brief[k]
                break

    available = any([brief, insights, tri, trend, receipt])
    updated_at = None
    mtimes = []
    for p in (brief_p, insights_p, tri_p, trend_p, receipt_p):
        if p and p.exists():
            try:
                mtimes.append(p.stat().st_mtime)
            except Exception:
                pass
    if mtimes:
        updated_at = iso(max(mtimes))

    return {
        "available": bool(available),
        "source": str(tmp_root),
        "updated_at": updated_at or None,
        "one_bet": one_bet,
        "brief": brief,
        "insights": insights,
        "tri_verdict": tri,
        "trend": trend,
        "receipt": receipt,
    }

class Handler(SimpleHTTPRequestHandler):
    ledger_root = Path(DEFAULT_LEDGER_ROOT).resolve()
    tmp_root = Path(DEFAULT_TMP_ROOT).resolve()

    def _send_json(self, obj: Any, status: int = 200):
        data = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write((VIEWS / "index.html").read_bytes())
            return

        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            file_path = STATIC / rel
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                ctype = "application/javascript; charset=utf-8" if file_path.suffix == ".js" else "application/octet-stream"
                self.send_header("Content-Type", ctype)
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            self._send_json({"error": "static not found"}, 404)
            return

        if path == "/api/status":
            self._send_json({
                "ok": True,
                "version": "emu-dashboard-stdlib-0.1",
                "ledger_root": str(self.ledger_root),
                "tmp_root": str(self.tmp_root),
                "now": iso(time.time()),
                "ledger_exists": self.ledger_root.exists(),
            })
            return

        if path == "/api/latest":
            self._send_json(load_latest(self.tmp_root))
            return

        if path == "/api/runs":
            q = urllib.parse.parse_qs(parsed.query)
            try:
                limit = int(q.get("limit", ["50"])[0])
                limit = max(1, min(limit, 500))
            except Exception:
                limit = 50
            items = list_ledger_runs(self.ledger_root, limit=limit)
            self._send_json({"items": items, "count": len(items)})
            return

        if path.startswith("/api/run/"):
            claim_id = path[len("/api/run/"):]
            claim_id = urllib.parse.unquote(claim_id)
            if "/" in claim_id or ".." in claim_id:
                self._send_json({"error": "bad claim_id"}, 400)
                return
            found = None
            for y in self.ledger_root.glob("*"):
                for m in y.glob("*"):
                    cand = m / claim_id
                    if cand.exists() and cand.is_dir():
                        found = cand
                        break
                if found:
                    break
            if not found:
                self._send_json({"error": "not found", "claim_id": claim_id}, 404)
                return
            self._send_json(load_run_dir(found))
            return

        self._send_json({"error": "not found"}, 404)

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5005"))
    Handler.ledger_root = Path(DEFAULT_LEDGER_ROOT).resolve()
    Handler.tmp_root = Path(DEFAULT_TMP_ROOT).resolve()
    httpd = HTTPServer((host, port), Handler)
    print(f"[emu-dashboard] stdlib server on http://{host}:{port}")
    print(f"[emu-dashboard] ledger_root={Handler.ledger_root}")
    print(f"[emu-dashboard] tmp_root={Handler.tmp_root}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
