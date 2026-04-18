EMU DASHBOARD — Read-only Emulation Visualization

Directory Structure
===================

oracle_town/dashboards/emu_dashboard/
├── server_stdlib.py      (no dependencies)
├── server_flask.py       (requires: pip install flask)
├── views/
│   └── index.html        (shared UI)
└── static/
    └── app.js            (shared UI logic)

/tmp files monitored
====================

OBS_SCAN:     obs_out.json, obs_scan_output.json
INS_CLUSTER:  ins_out.json, ins_cluster_output.json
BRF_ONEPAGER: brf_out.json, brf_onepager_output.json
TREND_MEMORY: trend_report.json
TRI_GATE:     tri_verdict.json
MAYOR:        receipt.json, mayor_receipt.json

Ledger monitored
================

oracle_town/ledger/YYYY/MM/claim_id/
├── claim.json
├── tri_verdict.json
└── mayor_receipt.json

Quick Start (Option A: No Dependencies)
========================================

export LEDGER_ROOT="oracle_town/ledger"
export TMP_ROOT="/tmp"
export HOST="127.0.0.1"
export PORT="5005"

python3 oracle_town/dashboards/emu_dashboard/server_stdlib.py

Then open:
http://127.0.0.1:5005

Quick Start (Option B: Flask)
=============================

pip install flask

export LEDGER_ROOT="oracle_town/ledger"
export TMP_ROOT="/tmp"
export HOST="127.0.0.1"
export PORT="5005"

python3 oracle_town/dashboards/emu_dashboard/server_flask.py

Then open:
http://127.0.0.1:5005

API Endpoints
=============

GET /                       → index.html
GET /static/<filename>      → JS/CSS
GET /api/status            → server health + paths
GET /api/latest            → current /tmp state
GET /api/runs?limit=50     → ledger history
GET /api/run/<claim_id>    → full run data

Dashboard Features
==================

Latest Emulation Section:
  - ONE BET (highest-confidence insight)
  - TRI Verdict (unsigned verification)
  - Receipt (signed decision)
  - Insights/Brief (clusters from INS_CLUSTER)
  - Trend Report (7-day comparison)

Ledger History Section:
  - All claims in ledger (newest first)
  - Click claim_id to load full 3-file run
  - View claim + verdict + receipt together

Live Refresh
============

Dashboard polls /api/latest and /api/runs every 2.5 seconds.
No refresh button needed — displays latest /tmp state automatically.

Hardening
=========

Run dashboard under unprivileged user:

chmod -R a-w oracle_town/ledger
chmod -R a-w oracle_town/policies 2>/dev/null || true

Dashboard can only read. Cannot modify authority.

Integration with Daily Loop
============================

bash oracle_town/daily_emulation_loop.sh
# Produces all /tmp files automatically

python3 oracle_town/dashboards/emu_dashboard/server_stdlib.py
# Reads them immediately (no restart needed)

That's it. Read-only jurisdiction visualization.

---

Mode A Status: ✓ Emulation-only, dashboard live, ready for daily runs.
