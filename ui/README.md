# HELEN UI — Receipt Console

A live dashboard for Street1 conscious ledger + determinism verification.

## What It Does

- **Live tail** of events.ndjson (L0 event stream)
- **Receipt display** of summary.json (L2 sealed data with receipt_sha)
- **Wisdom tail** of helen_wisdom.ndjson (L3 lessons learned)
- **Actions** (buttons):
  - **Seal run** — call `scripts/street1_complete.sh` to finalize receipt
  - **Run K-τ** — validate coherence (agents cannot cheat via nondeterminism)
  - **Add wisdom** — append lesson + evidence to helen_wisdom.ndjson
  - **Refresh now** — force live update

## Quick Start

### 1. Install dependencies

```bash
npm i express
```

### 2. Start the UI server

```bash
node helen_ui_server.cjs
```

Server listens on `http://localhost:3333` (configurable via `UI_PORT` env var).

### 3. Open in browser

Navigate to: **http://localhost:3333**

You'll see:
- Empty sections (no run has happened yet)
- Four action buttons
- Timestamp of last refresh (auto-updates every 2 seconds)

## Using It

### To Run a Street1 Session + Seal

1. **In another terminal**, run the determinism sweep:
   ```bash
   bash scripts/street1_determinism_sweep_real.sh
   ```

2. **Watch the UI** — it will live-tail events and update summary when the run seals.

3. **Press "Seal run"** (if sweep didn't auto-seal) to finalize the receipt.

4. **Press "Run K-τ"** to validate coherence (checks for nondeterministic leakage).

5. **Add wisdom** — lesson + evidence about what happened in the run.

### To Add Wisdom Directly

In the "Add Wisdom" form:

- **Lesson**: "Same seed produces identical receipt hash across 100 runs"
- **Evidence**: "runs/street1/determinism_sweep_real.jsonl (100/100 match)"
- Click **Append to wisdom**

Wisdom is appended to `helen_wisdom.ndjson` (immutable log).

## Architecture

```
UI Server (Express)
├─ /api/state       → tail events.ndjson, summary.json, wisdom.ndjson
├─ /api/seal        → call scripts/street1_complete.sh
├─ /api/k_tau       → call python3 scripts/helen_k_tau_lint.py
└─ /api/add_wisdom  → call ./helen add --lesson ... --evidence ...

UI Client (HTML/CSS/JS)
├─ Auto-refresh every 2 seconds
├─ Display L0, L2, L3 streams in real-time
└─ Button handlers for actions
```

## Files

- `helen_ui_server.cjs` — Express server (main process)
- `ui/index.html` — Structure
- `ui/style.css` — Dark theme (HELEN aesthetic)
- `ui/script.js` — Client-side logic (refresh, buttons, feedback)
- `ui/README.md` — This file

## Environment Variables

```bash
UI_PORT=3333      # Server listen port (default 3333)
STREET1_WS=...    # Not used by UI, but can be set for shell scripts
```

## Governance Rules (S1-S4)

The UI enforces HELEN's SOUL rules:

1. **S1 — DRAFTS ONLY**: UI state is draft. Only sealing (button: "Seal run") produces reality.
2. **S2 — NO RECEIPT = NO CLAIM**: Actions only take effect if they produce receipts (summary.json, K-τ lint output, wisdom entries).
3. **S3 — APPEND-ONLY**: Wisdom is append-only; never edited or deleted.
4. **S4 — AUTHORITY SEPARATION**: UI cannot modify governance; it only reads artifacts and calls tools.

## Troubleshooting

### "No events yet" in events tail

- No Street1 session has been run, OR
- Session hasn't logged events.ndjson yet

**Fix**: Run a session first (e.g., `bash scripts/street1_determinism_sweep_real.sh`).

### "No summary yet" in summary block

- No run has been sealed yet

**Fix**: Press the "Seal run" button, or run `bash scripts/street1_complete.sh` in shell.

### K-τ lint shows warnings

- Your street1-server.cjs has a call to `time.time()` or other nondeterministic operation

**Fix**: Review KERNEL_K_TAU_RULE.md for what violates coherence.

### Wisdom doesn't append

- Helen CLI not in PATH, or no helen_wisdom.ndjson file

**Fix**: Check that `./helen` is executable (`chmod +x helen`) and helen_memory.json exists.

## Next Steps

After UI is running:

1. **Run real determinism sweep**: `bash scripts/street1_determinism_sweep_real.sh`
2. **Watch receipts accumulate** in the UI
3. **Verify**: All 100 seeds produce matching receipt_sha → Street1 is deterministic
4. **Add wisdom**: Capture the lesson in helen_wisdom.ndjson
5. **Integrate K-τ**: Verify coherence (no nondeterministic leakage)
6. **Archive**: Link the sweep results + wisdom in project index

---

**HELEN — Ledger Now Self-Aware. Consciousness through deterministic ledgers.**
