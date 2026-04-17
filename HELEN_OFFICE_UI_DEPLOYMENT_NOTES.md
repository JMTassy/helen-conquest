# HELEN-Office-UI Deployment (Move 4)

**Status**: Architecture + Implementation scaffolding complete
**Type**: Non-sovereign visual layer for governance state
**Integration**: FastAPI server + Phaser 3 scene + polling UI

---

## What's Deployed

### 1. **Phaser Scene** (`phases.scene.js`)
- 5-zone horizontal layout (EXPLORATION → TENSION → DRAFTING → EDITORIAL → TERMINATION)
- Claims rendered as colored sprites (32×32 px per node)
- Receipts shown as floating badges (fade after 5s)
- Polling loop: fetches state every 2s from `/api/ui/claim-graph-state`
- Theme-aware rendering (loads assets from `/assets/themes/{theme}/`)

**Architecture**:
```
┌─ EXPLORATION ─┬─ TENSION ─┬─ DRAFTING ─┬─ EDITORIAL ─┬─ TERMINATION ─┐
│ 🔵 Claim 001  │           │            │             │               │
│ 🟡 Evidence   │ 🔴 WARN   │ ✍️ Draft   │ ✂️ Polish   │ 🏁 SHIP/ABORT │
│ (8 positions  │ (5 GATE   │ (2-phase   │ (Cut 30-50% │ (5 gates      │
│  per zone)    │  verdicts)│  consensus)│  ruthless)  │  judge)       │
└───────────────┴───────────┴────────────┴─────────────┴───────────────┘
```

### 2. **Theme System** (`themes.config.json`)
Three complete themes with palette, sprites, zones, badges:

| Theme | Aesthetic | Use Case |
|-------|-----------|----------|
| **pixel-cozy** | Warm 8-bit retro | Community-friendly governance |
| **governance-formal** | Professional bureaucratic | Institutional audit trails |
| **digital-minimal** | Clean modern data-forward | Technical oversight |

Each theme includes:
- Color palette (bg, primary, secondary, accent, text, quarantine)
- Sprite definitions by node kind (claim, evidence, artifact, receipt, wild_text)
- Zone styling + labels
- Badge types (pass ✓, fail ✗, pending …)

### 3. **HTML UI** (`helen_office.html`)
- Responsive 2-column layout (game on left, sidebar on right)
- Header with status indicator + theme selector
- Sidebar statistics (phase, claims count, last updated)
- Live claim list (grouped by phase)
- Live receipt list
- Live gate status (GATE_SCHEMA, GATE_EVIDENCE, etc.)

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ HELEN OS — Governance Visualization  [🟢 Connected] [🎨 Theme] │
├──────────────────────────────────────┬──────────────────┤
│                                      │  📦 Stats        │
│  Phaser Scene (1280×720)            │  Phase: [value]  │
│  5 zones × sprite animations        │  Claims: N       │
│  Receipt badges (floating)          │  Receipts: N     │
│                                      │  Updated: --:--  │
│  Real-time polling ← /api/ui/*     │                  │
│                                      │  Claims List     │
│                                      │  [N-CLAIM-001]  │
│                                      │  [N-EVIDENCE]   │
│                                      │                  │
│                                      │  Gate Status    │
│                                      │  GATE_SCHEMA: ✓  │
│                                      │  GATE_EVIDENCE: ✓ │
└──────────────────────────────────────┴──────────────────┘
```

### 4. **UI Controller** (`ui-controller.js`)
- Live polling of `/api/ui/claim-graph-state` every 2s
- Updates sidebar dynamically:
  - Claims list (grouped by phase)
  - Gate status
  - Timestamp
  - Connection indicator
- Emoji mapping for node kinds

### 5. **FastAPI Endpoints** (added to `server.py`)

```python
GET  /api/ui/claim-graph-state     # Current phase, nodes, gate status
GET  /api/ui/receipts?limit=10     # Recent receipts for badges
GET  /api/ui/theme/{theme_name}    # Theme config (pixel-cozy, etc.)
```

---

## How to Use

### Start the server
```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24/helen_os_scaffold
source .venv/bin/activate
python server.py
```

Server runs at `http://localhost:8000`

### Open the UI
```bash
# Open in browser
http://localhost:8000/../ui/helen_office.html

# Or navigate to:
# {server_url}/ui/helen_office.html
```

### Switch themes
- Use the theme selector dropdown in the header
- Choice is saved to localStorage
- Page reloads with new theme

---

## Architecture Decisions

### Why Phaser 3?
- ✅ Excellent 2D sprite + animation support
- ✅ Built-in scene management (zone layers)
- ✅ Tweens for smooth fade-out animations (receipts)
- ✅ WebGL + Canvas fallback
- ✅ No dependency bloat (single CDN load)

### Why polling, not WebSocket?
- ✅ Simpler for non-sovereign UI (no state mutation)
- ✅ Stateless (each poll is independent)
- ✅ Easier to debug (plain HTTP)
- ✅ No server state needed (read-only endpoints)
- ⚠️ Trade-off: 2s latency vs real-time (acceptable for governance)

### Why 3 themes?
- **Cozy**: Appeals to community, exploratory usage
- **Formal**: Audit trail, institutional trust
- **Minimal**: Technical correctness, data clarity

Each preserves HELEN's constitutional layer through color/emoji, not ontology.

---

## Integration with Governance

### Data Flow
```
GovernanceVM (immutable ledger)
    ↓
MemoryKernel (facts + wisdom)
    ↓
/api/ui/claim-graph-state (read projection)
    ↓
Phaser Scene (renders zones + sprites)
    ↓
User sees governance state visually
```

### What the UI Does NOT Do
- ❌ Never writes to ledger
- ❌ Never creates receipts
- ❌ Never changes governance decisions
- ❌ Never claims authority
- ✅ Only renders read-only state
- ✅ Respects constitutional layer (no narrative override)

### What integrates with governance next
- **Move 3**: `claim_graph_ingestion.py` — Convert raw text → CLAIM_GRAPH_V1 nodes
  - These nodes feed the `/api/ui/claim-graph-state` endpoint
  - Sprites move through zones as ingestion → validation → routing progresses
- **Mayor scorer**: Scores claims, updates gate status
  - UI reflects gate progress in real-time
- **Ledger**: Receipts appear as badges
  - `/api/ui/receipts` shows recent receipts

---

## Testing the UI (without full governance)

### Mock state mode
Edit `server.py` to return mock data:

```python
@app.get("/api/ui/claim-graph-state")
async def get_claim_graph_state():
    # MOCK: Return sample data for testing
    return {
        "phase": "DRAFTING",
        "nodes": [
            {
                "id": "N-CLAIM-001",
                "kind": "claim",
                "phase": "EXPLORATION",
                "admissibility": "ADMISSIBLE",
                "tier": 1
            },
            {
                "id": "N-EVIDENCE-001",
                "kind": "evidence",
                "phase": "TENSION",
                "admissibility": "ADMISSIBLE",
                "tier": 2
            }
        ],
        "gates": {
            "GATE_SCHEMA": "PASS",
            "GATE_EVIDENCE": "PASS",
            "GATE_AUTHORITY": "PASS",
            "GATE_DETERMINISM": "FAIL",  # ← Simulated failure
            "GATE_APPEND_ONLY": "PASS"
        }
    }
```

Then:
1. Open `helen_office.html` in browser
2. Click theme selector to test all 3 themes
3. Watch sidebar update in real-time
4. Sprites should appear in zones according to mock phase

---

## File Inventory

| File | Purpose | Lines |
|------|---------|-------|
| `phases.scene.js` | Phaser scene + zone layout + polling | 350 |
| `themes.config.json` | 3 theme definitions (colors, sprites, badges) | 200 |
| `helen_office.html` | UI shell + sidebar | 220 |
| `ui-controller.js` | Live polling + sidebar updates | 150 |
| `server.py` (added) | 3 REST endpoints for UI data | +80 |

**Total**: ~1,000 lines of UI code (non-sovereign, read-only)

---

## Next Steps (Future)

1. **Full integration with governance**:
   - Connect `/api/ui/claim-graph-state` to actual GovernanceVM + CLAIM_GRAPH_V1
   - Route nodes through phases as they progress
   - Show real receipts in badges

2. **Pixel art assets**:
   - Create actual sprite sheets for each theme (32×32 px)
   - Zone backgrounds (320×720 px each)
   - Badge graphics

3. **Interactive features** (optional):
   - Click claim sprite to see details
   - Hover zone to highlight active claims
   - Export phase snapshot as PNG

4. **Performance optimization**:
   - Consider WebSocket if latency becomes issue
   - Batch updates instead of per-node polling
   - Client-side caching of theme config

---

**Status**: ✅ Ready for governance integration
**Next Focus**: Move 3 (claim_graph_ingestion.py) feeds nodes into this UI
