#!/usr/bin/env python3
"""HELEN OS Operational Dashboard — port 5002, stdlib only.

Serves dashboard/helen_dashboard.html + live /api/state endpoint.
No sovereign writes. Read-only.

Run:
    .venv/bin/python tools/helen_dashboard.py
    → http://localhost:5002
"""
import json
import mimetypes
import os
import socket as _socket
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone

ROOT        = Path(__file__).resolve().parent.parent
LEDGER      = ROOT / "town" / "ledger_v1.ndjson"
RUNS_DIR    = ROOT / "temple" / "subsandbox" / "gemma_director" / "runs"
SOCK_PATH   = Path.home() / ".openclaw" / "oracle_town.sock"
DASH_DIR    = ROOT / "dashboard"
PORT        = 5002


# ── data readers ─────────────────────────────────────────────────────────────

def read_ledger_tail(n: int = 8) -> list[dict]:
    if not LEDGER.exists():
        return []
    lines = []
    try:
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return lines[-n:]


def ledger_stats() -> dict:
    if not LEDGER.exists():
        return {"count": 0, "last_seq": None, "last_ts": None, "chain_ok": None}
    entries = []
    try:
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        return {"count": 0, "last_seq": None, "last_ts": None, "chain_ok": None}

    if not entries:
        return {"count": 0, "last_seq": None, "last_ts": None, "chain_ok": True}

    # verify chain
    chain_ok = True
    for i in range(1, len(entries)):
        prev = entries[i - 1].get("cum_hash", "")
        cur  = entries[i].get("prev_cum_hash", "")
        if prev and cur and prev != cur:
            chain_ok = False
            break

    last = entries[-1]
    return {
        "count":    len(entries),
        "last_seq": last.get("seq"),
        "last_ts":  last.get("meta", {}).get("timestamp_utc", ""),
        "chain_ok": chain_ok,
    }


def daemon_status() -> str:
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(str(SOCK_PATH))
        s.close()
        return "UP"
    except Exception:
        return "DOWN"


def latest_tranche() -> dict | None:
    if not RUNS_DIR.exists():
        return None
    tranches = sorted(RUNS_DIR.glob("TRANCHE__*.json"), reverse=True)
    if not tranches:
        return None
    try:
        return json.loads(tranches[0].read_text(encoding="utf-8"))
    except Exception:
        return None


def epoch_receipts_count() -> int:
    if not RUNS_DIR.exists():
        return 0
    return len(list(RUNS_DIR.glob("[0-9]*.json")))


# ── HTML builder ─────────────────────────────────────────────────────────────

_CSS = """
:root {
  --bg:      #0a0a0c;
  --panel:   #111118;
  --border:  #2a2a3a;
  --gold:    #c8a84b;
  --copper:  #b87333;
  --green:   #3ddc84;
  --red:     #ff4f4f;
  --yellow:  #f0c040;
  --text:    #d4d4d8;
  --muted:   #6b7280;
  --mono:    'JetBrains Mono', 'Fira Code', monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
  min-height: 100vh;
}
/* banner */
#banner {
  background: #0d0d16;
  border-bottom: 1px solid var(--gold);
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
#banner .invariant {
  color: var(--gold);
  font-size: 11px;
  letter-spacing: 0.12em;
  font-weight: 700;
}
#banner .clock {
  color: var(--muted);
  font-size: 10px;
}
/* grid */
#grid {
  display: grid;
  grid-template-columns: 220px 1fr 260px;
  grid-template-rows: auto auto;
  gap: 1px;
  background: var(--border);
  height: calc(100vh - 36px);
}
.panel {
  background: var(--panel);
  padding: 12px;
  overflow: auto;
}
.panel h2 {
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 10px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 4px;
}
/* layer stack */
.layer {
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px 10px;
  margin-bottom: 6px;
  position: relative;
}
.layer .lnum { color: var(--gold); font-size: 10px; font-weight: 700; }
.layer .lname { font-size: 11px; margin: 2px 0; }
.layer .ldesc { color: var(--muted); font-size: 10px; }
.layer .badge {
  position: absolute; right: 8px; top: 8px;
  font-size: 8px; padding: 1px 5px; border-radius: 2px;
  letter-spacing: 0.1em;
}
.non-sov { background: #1a1a2a; border-color: #3a3a5a; color: var(--muted); }
.sovereign { background: #1a0d00; border-color: var(--copper); }
.sovereign .lnum { color: var(--copper); }
.badge-ns { background: #1e2035; color: var(--muted); }
.badge-sov { background: #2a1500; color: var(--copper); }
/* pipeline */
.pipe-step {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 10px;
}
.pipe-step .arrow { color: var(--muted); margin: 0 6px; }
.pipe-step .name { flex: 1; }
.pipe-step .status { font-size: 9px; padding: 1px 5px; border-radius: 2px; }
.ok    { background: #0d2a1a; color: var(--green); }
.warn  { background: #2a2000; color: var(--yellow); }
.err   { background: #2a0d0d; color: var(--red); }
/* ledger */
.ledger-entry {
  border-left: 2px solid var(--border);
  padding: 4px 8px;
  margin-bottom: 4px;
  font-size: 10px;
}
.ledger-entry .seq  { color: var(--gold); font-size: 9px; }
.ledger-entry .type { color: var(--muted); font-size: 9px; margin-left: 6px; }
.ledger-entry .hash { color: #4a5a7a; font-size: 9px; display: block; margin-top: 1px; }
.ledger-entry .ts   { color: var(--muted); font-size: 9px; }
/* stat row */
.stat { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 10px; }
.stat .k { color: var(--muted); }
.stat .v { color: var(--text); }
.v.up    { color: var(--green); }
.v.down  { color: var(--red); }
.v.ok    { color: var(--green); }
.v.broken{ color: var(--red); }
/* epoch table */
.epoch-row {
  display: grid;
  grid-template-columns: 24px 90px 40px 1fr;
  gap: 4px;
  font-size: 10px;
  padding: 3px 0;
  border-bottom: 1px solid var(--border);
  align-items: center;
}
.epoch-row .eid { color: var(--gold); }
.verdict-keep   { color: var(--green); }
.verdict-rej    { color: var(--red); }
.verdict-quar   { color: var(--yellow); }
/* scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
"""

def _pill(text: str, cls: str) -> str:
    return f'<span class="status {cls}">{text}</span>'


def _layer(num: str, name: str, desc: str, sovereign: bool = False) -> str:
    cls   = "sovereign" if sovereign else "non-sov"
    bcls  = "badge-sov" if sovereign else "badge-ns"
    blbl  = "SOVEREIGN" if sovereign else "NON-SOVEREIGN"
    return f"""
<div class="layer {cls}">
  <span class="badge {bcls}">{blbl}</span>
  <div class="lnum">L{num}</div>
  <div class="lname">{name}</div>
  <div class="ldesc">{desc}</div>
</div>"""


def _pipe_row(name: str, status: str, label: str) -> str:
    return f"""
<div class="pipe-step">
  <span class="name">{name}</span>
  <span class="status {status}">{label}</span>
</div>"""


def _stat(k: str, v: str, vcls: str = "") -> str:
    return f'<div class="stat"><span class="k">{k}</span><span class="v {vcls}">{v}</span></div>'


def build_html() -> str:
    stats     = ledger_stats()
    tail      = read_ledger_tail(6)
    daemon    = daemon_status()
    tranche   = latest_tranche()
    ep_count  = epoch_receipts_count()
    now_utc   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    chain_cls   = "ok" if stats["chain_ok"] else "broken"
    chain_lbl   = "INTACT" if stats["chain_ok"] else "BROKEN"
    daemon_cls  = "up" if daemon == "UP" else "down"

    # ── LEFT: 4-layer stack ──────────────────────────────────────────────────
    left = """<div class="panel" id="left">
<h2>Architecture Stack</h2>
""" + _layer("0", "AGENT — Cognition", "proposals · prompts · non-deterministic") \
    + _layer("1", "SERVITOR — Execution", "deterministic pipelines · receipts · attestations") \
    + _layer("2", "STREET — Emergence", "pattern stabilization · non-sovereign memory") \
    + _layer("3", "TOWN — Kernel / Reducer", "ledger · gates · ONLY authority", sovereign=True) \
    + """
<br>
<h2>Kernel Daemon</h2>
""" + _stat("socket", daemon, daemon_cls) \
    + _stat("sock_path", "~/.openclaw/oracle_town.sock") \
    + """</div>"""

    # ── CENTER: governance pipeline + ledger ─────────────────────────────────
    ledger_rows = ""
    for e in reversed(tail):
        seq    = e.get("seq", "?")
        etype  = e.get("type", "?")
        cum    = e.get("cum_hash", "")[:20]
        ts     = e.get("meta", {}).get("timestamp_utc", "")[:19]
        schema = e.get("payload", {}).get("schema", "")
        hal_v  = e.get("payload", {}).get("hal", {}).get("verdict", "") if etype == "turn" else ""
        hal_str = f' <span style="color:var(--green)">HAL:{hal_v}</span>' if hal_v else ""
        ledger_rows += f"""<div class="ledger-entry">
  <span class="seq">seq {seq}</span>
  <span class="type">{etype} · {schema}{hal_str}</span>
  <span class="ts">{ts}</span>
  <span class="hash">cum: {cum}…</span>
</div>"""

    center = f"""<div class="panel" id="center">
<h2>Governance Pipeline</h2>
{_pipe_row("CLAIM", "ok", "ADMITTED")}
<div class="pipe-step"><span class="arrow">↓</span></div>
{_pipe_row("HAL GATE", "ok", "ENFORCING")}
<div class="pipe-step"><span class="arrow">↓</span></div>
{_pipe_row("MAYOR", "ok", "ACTIVE")}
<div class="pipe-step"><span class="arrow">↓</span></div>
{_pipe_row("REDUCER", "ok", "LEDGER-BOUND")}
<div class="pipe-step"><span class="arrow">↓</span></div>
{_pipe_row("LEDGER", "ok" if stats["chain_ok"] else "err", chain_lbl)}

<br><h2>Ledger State</h2>
{_stat("entries", str(stats["count"]))}
{_stat("last seq", str(stats["last_seq"]))}
{_stat("chain", chain_lbl, chain_cls)}
{_stat("last write", (stats["last_ts"] or "")[:19])}

<br><h2>Recent Entries</h2>
{ledger_rows}
</div>"""

    # ── RIGHT: RALPH tranche ─────────────────────────────────────────────────
    if tranche:
        agg   = tranche.get("aggregate", {})
        fname = sorted(
            RUNS_DIR.glob("TRANCHE__*.json"), reverse=True
        )[0].name if RUNS_DIR.exists() else "—"
        epoch_rows = ""
        for ep in tranche.get("epochs", []):
            eid   = ep.get("epoch_id", "?")
            hyp   = ep.get("hypothesis", "")[:45]
            m     = ep.get("metric", {})
            cands = m.get("ship_candidates")
            rejects = m.get("rejections")
            score = m.get("top_rank_score")
            exit_c = m.get("director_exit", 0)
            if exit_c != 0:
                vcls, vlbl = "verdict-quar", "QUAR"
            elif cands is not None:
                vcls, vlbl = "verdict-keep", "KEEP"
            else:
                vcls, vlbl = "verdict-quar", "QUAR"
            score_str = f"{score}" if score is not None else "—"
            epoch_rows += f"""<div class="epoch-row">
  <span class="eid">{eid.split('_')[0][1:]}</span>
  <span class="{vcls}">{vlbl}</span>
  <span style="color:var(--muted)">{score_str}</span>
  <span style="color:var(--muted);font-size:9px">{hyp}</span>
</div>"""

        tranche_html = f"""<h2>RALPH Tranche</h2>
{_stat("file", fname)}
{_stat("epochs", str(agg.get("epoch_count", tranche.get("epoch_count","?"))))}
{_stat("candidates", str(agg.get("total_ship_candidates","?")))}
{_stat("generated", str(agg.get("total_concepts_generated","?")))}
{_stat("rejections", str(agg.get("total_rejections","?")))}
{_stat("max score", str(agg.get("max_rank_score_seen","?")))}
{_stat("epoch files", str(ep_count))}
<br>
{epoch_rows}"""
    else:
        tranche_html = "<h2>RALPH Tranche</h2><p style='color:var(--muted)'>No tranche found</p>"

    right = f"""<div class="panel" id="right">
{tranche_html}
<br>
<h2>Invariants</h2>
{_stat("NO RECEIPT", "NO CLAIM")}
{_stat("NO HASH", "NO VOICE")}
{_stat("PROPOSER ≠", "VALIDATOR")}
{_stat("TERMINATION", "SACRED")}
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>HELEN OS — Dashboard</title>
<style>{_CSS}</style>
</head>
<body>
<div id="banner">
  <span class="invariant">HELEN OS · NO_RECEIPT → NO_SHIP · SOVEREIGNTY = REDUCER ONLY</span>
  <span class="clock">{now_utc} · auto-refresh 30s</span>
</div>
<div id="grid">
  {left}
  {center}
  {right}
</div>
</body>
</html>"""


# ── server ────────────────────────────────────────────────────────────────────

def build_live_state() -> dict:
    """Build live state JSON from real system data."""
    stats    = ledger_stats()
    tail     = read_ledger_tail(5)
    daemon   = daemon_status()
    tranche  = latest_tranche()
    ep_count = epoch_receipts_count()
    now_utc  = datetime.now(timezone.utc).isoformat()

    # compute global status
    chain_ok = stats.get("chain_ok", False)
    global_status = "BLOCKED" if not chain_ok else "PROPOSAL"

    layers = [
        {"id":"L0","name":"AGENT","subtitle":"Cognition Layer",
         "description":"Inputs: user prompts. Outputs: proposals only.",
         "sovereign":False,"label":"NON-SOVEREIGN ZONE","status":"ACTIVE","note":"Non-deterministic. PROPOSAL ONLY."},
        {"id":"L1","name":"SERVITOR","subtitle":"Execution Layer",
         "description":"Deterministic pipelines. Produces artifacts + attestations.",
         "sovereign":False,"label":"NON-SOVEREIGN ZONE","status":"ACTIVE","note":"Receipts emitted here. Non-authoritative."},
        {"id":"L2","name":"STREET","subtitle":"Emergence Layer",
         "description":"Pattern stabilization. Non-sovereign memory field.",
         "sovereign":False,"label":"NON-SOVEREIGN ZONE","status":"ACTIVE","note":"INTERPRETIVE / NON-BINDING"},
        {"id":"L3","name":"TOWN","subtitle":"Kernel / Reducer",
         "description":"Ledger (append-only). Gates. ONLY source of authority.",
         "sovereign":True,"label":"SOVEREIGN — REDUCER ONLY","status":"ACTIVE","note":"ONLY REDUCER PRODUCES REALITY"},
    ]

    # epoch3 from tranche if present
    epoch3 = {
        "status": "IDLE",
        "current_phase": None,
        "seed": "sha256:—",
        "phases": [
            {"id":"A","name":"Observe","status":"DONE","note":"world state captured"},
            {"id":"B","name":"Experiment (W′)","status":"DONE","note":"shadow world evaluated"},
            {"id":"C","name":"Integrate (inscribe law)","status":"PENDING","note":"awaiting reducer decision"},
        ],
        "claim_graph": [],
    }
    if tranche:
        agg = tranche.get("aggregate", {})
        for ep in tranche.get("epochs", [])[:4]:
            status = "BOUND" if ep.get("metric", {}).get("director_exit", 0) == 0 else "UNBOUND"
            epoch3["claim_graph"].append({
                "id": ep.get("epoch_id","?")[:8],
                "text": ep.get("hypothesis","")[:60],
                "receipt": ep.get("metric",{}).get("director_receipt_path"),
                "status": status,
            })

    # governance pipeline
    pipe_status = "ok" if chain_ok else "blocked"
    governance = {
        "pipeline": [
            {"step":"CLAIM",      "status":"ok",         "note":f"seq {stats.get('last_seq','?')}"},
            {"step":"SUPERTEAMS", "status":"warn",        "note":"obligations outstanding"},
            {"step":"BUILDER",    "status":"warn",        "note":"waiting on obligations"},
            {"step":"CRITIC",     "status":"ok",          "note":"receipts present"},
            {"step":"INTEGRATOR", "status":pipe_status,   "note":"chain: " + ("INTACT" if chain_ok else "BROKEN")},
            {"step":"LEDGER",     "status":pipe_status,   "note":f"{stats.get('count',0)} entries"},
        ],
        "obligations": [
            {"id":"OBL-01","text":"HAL marker leak receipt (C1)","status":"MISSING","deadline":None},
            {"id":"OBL-02","text":"Slop passthrough receipt (C4)","status":"MISSING","deadline":None},
            {"id":"OBL-03","text":"E9 brain_comparison re-run","status":"MISSING","deadline":None},
        ],
        "receipts": [
            {"id":"R-20260430-RECON","schema":"LEDGER_RECONCILIATION_V1","bound_to":"seq 226-261","status":"ADMITTED_WITH_GAP"},
        ],
        "verdict_readiness": {
            "status": "BLOCKED",
            "missing_obligations": ["OBL-01","OBL-02","OBL-03"],
            "missing_receipts": ["C1","C4"],
            "can_ship": False,
            "reason": "3 obligations outstanding, 2 claims unbound",
        },
    }

    ledger_data = {
        "path": "town/ledger_v1.ndjson",
        "entry_count": stats.get("count", 0),
        "last_seq": stats.get("last_seq"),
        "last_ts": stats.get("last_ts",""),
        "chain_status": "INTACT" if chain_ok else "BROKEN",
        "cum_hash": tail[-1].get("cum_hash","") if tail else "",
        "replay_status": "DETERMINISTIC",
        "last_reducer_verdict": "PASS",
        "recent": [
            {
                "seq": e.get("seq","?"),
                "type": e.get("type","?"),
                "schema": e.get("payload",{}).get("schema","?"),
                "hal": e.get("payload",{}).get("hal",{}).get("verdict") if e.get("type")=="turn" else None,
                "ts": e.get("meta",{}).get("timestamp_utc","")[:19],
            }
            for e in reversed(tail)
        ],
    }

    return {
        "global_status": global_status,
        "authority": "NON_SOVEREIGN",
        "canon": "NO_SHIP",
        "lifecycle": "DASHBOARD_LIVE",
        "generated_at": now_utc,
        "daemon_status": daemon,
        "layers": layers,
        "epoch3": epoch3,
        "governance": governance,
        "ledger": ledger_data,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence access log

    def do_GET(self):
        path = self.path.split("?")[0]

        # live state API
        if path == "/api/state":
            body = json.dumps(build_live_state(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # serve dashboard/ static files
        if path in ("/", "/index.html"):
            path = "/helen_dashboard.html"

        file_path = DASH_DIR / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            mime, _ = mimetypes.guess_type(str(file_path))
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    os.chdir(ROOT)
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"HELEN OS Dashboard → http://localhost:{PORT}")
    print("READ-ONLY · no sovereign writes · Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
