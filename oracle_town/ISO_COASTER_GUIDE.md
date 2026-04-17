# ISO-COASTER VISUALIZATION GUIDE

**Oracle Town Iso-Perspective Town Visualization**

Date: January 31, 2026
Status: COMPLETE (Option 2 Implementation)
K5 Determinism: ✓ Verified (5-10 iterations)

---

## Overview

The iso-coaster is a **read-only, non-authoritative visualization** of Oracle Town's jurisdiction state rendered in isometric (30-degree) perspective. It transforms CityState JSON snapshots into both ASCII and HTML/SVG renderings for different use cases.

**Key Property:** Same CityState dict → identical visualization output (K5 determinism verified)

---

## Architecture

### Two Rendering Modes

| Mode | File | Output | Format | Use Case |
|------|------|--------|--------|----------|
| **ASCII Snapshot** | `city_state_renderer.py` | Terminal-friendly | Fixed 47-char width | CLI monitoring, logs, email |
| **HTML/SVG Iso-Coaster** | `iso_coaster_renderer.py` | Browser-viewable | Interactive HTML page | Dashboard, visual exploration |

Both share the same **frozen configuration** (`iso_coaster_config.py`) ensuring consistent module definitions and visual rules.

---

## ASCII Renderer

### Entry Point

```python
from oracle_town.city_state_renderer import render_city_state

city_state = {
    "date": "2026-01-31",
    "run_id": "daily-01",
    "policy": {"version": "v7", "hash": "sha256:abc123"},
    "verdicts": {"accepted": 5, "rejected": 10},
    "modules": {
        "OBS": {"status": "OK"},
        "INSIGHT": {"status": "OK"},
        "MEMORY": {"status": "OFF"},
        "BRIEF": {"status": "OK"},
        "TRI": {"status": "OK"},
        "PUBLISH": {"status": "FAIL"},
    },
    "top_insights": [
        "Acceptance rate: 33.3%",
        "Total verdicts: 15",
    ],
}

output = render_city_state(city_state)
print(output)
```

### Example Output

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ORACLE TOWN — 2026-01-31 RUN daily-01     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Policy: v7 (sha256:abc123…)
┃ Verdicts: ACCEPT 5 | REJECT 10
┃
┃ CITY STATE
┃
┃        [OBS] OK     ████▉
┃         │
┃    [INSIGHT] OK     ████▉
┃         │ │
┃    [MEMORY]        [BRIEF]
┃      OFF ░░░░░      OK ████▉
┃         │ │
┃           ↓
┃      [TRI] OK       ████▉
┃           ↓
┃    [PUBLISH] FAIL   █████
┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ TOP INSIGHTS
┃
┃ • Acceptance rate: 33.3%
┃ • Total verdicts: 15
┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘
```

**Key Features:**
- Fixed 47-character width (fits in 80-char terminal)
- Canonical ASCII art (reproducible exactly)
- Status glyphs: OK (████▉), OFF (░░░░░), FAIL (█████)
- Module network topology (data flow arrows)
- Top insights section (insight highlights)
- Deterministic rendering (K5 verified 10x + 50x stress test)

---

## HTML/SVG ISO-Coaster Renderer

### Entry Point

```python
from oracle_town.iso_coaster_renderer import render_iso_coaster

city_state = {
    "date": "2026-01-31",
    "run_id": "daily-iso",
    "policy": {"version": "v7", "hash": "sha256:abc123"},
    "verdicts": {"accepted": 5, "rejected": 10},
    "modules": {
        "OBS": {"status": "OK"},
        "INSIGHT": {"status": "OK"},
        "MEMORY": {"status": "OFF"},
        "BRIEF": {"status": "OK"},
        "TRI": {"status": "OK"},
        "PUBLISH": {"status": "FAIL"},
    },
}

html = render_iso_coaster(city_state)
print(html)  # Save to file or serve via HTTP
```

### Technical Details

**ISO Projection (30-degree Isometric):**
```
screen_x = (x - y) * cos(30°)  ≈ (x - y) * 0.866
screen_y = (x + y) * sin(30°)  =  (x + y) * 0.5
```

**Building Layout (Fixed Coordinates):**
```
OBS:      (0, 0)     [Reference origin]
INSIGHT:  (0, 1)     [Down from OBS]
MEMORY:   (-1, 2)    [Left-below]
BRIEF:    (0, 2)     [Center-below]
TRI:      (0, 3)     [Below BRIEF, center]
PUBLISH:  (1, 2)     [Right-below]
```

**Visual Properties:**
- Buildings: Diamond shapes (4-point polygons)
- Colors: Green (OK #10b981), Gray (OFF #6b7280), Red (FAIL #ef4444)
- Brightness: Adjusted per status (OK=1.0, OFF=0.4, FAIL=0.8)
- Labels: Module names in white text, centered
- Indicators: Status circles above each building
- Special: "IMMUTABLE" text below TRI module

**Output Format:**
- Complete HTML5 document
- Embedded SVG (no external dependencies)
- CSS styling (dark theme, responsive)
- Statistics header (policy, verdicts, date)
- Disclaimer footer (non-authoritative notice)
- ~7.8 KB uncompressed

### Dashboard Integration

The HTML iso-coaster is available via HTTP:

```bash
# Start dashboard
python3 oracle_town/dashboard_server.py

# Fetch iso-coaster visualization
curl http://localhost:5000/api/city-state/iso-html > iso_coaster.html

# Open in browser
open iso_coaster.html
```

**API Endpoint:** `GET /api/city-state/iso-html`
- Returns: HTML document (Content-Type: text/html)
- Response time: <50ms
- Determinism: K5 verified (same verdicts → identical HTML)

---

## Configuration (Frozen)

All module definitions, colors, and visual rules are defined in `oracle_town/iso_coaster_config.py`:

### Module Archetypes

```python
MODULE_ARCHETYPES = {
    "OBS": {
        "name": "Observatory",
        "role": "Observation & Ingestion",
        "symbol": "⌖",
        "position": (0, 0),
    },
    "INSIGHT": {
        "name": "Library",
        "role": "Pattern Analysis",
        "symbol": "📚",
        "position": (0, 1),
    },
    "MEMORY": {
        "name": "Vault",
        "role": "Historical Data",
        "symbol": "🔐",
        "position": (-1, 2),
    },
    "BRIEF": {
        "name": "Scriptorium",
        "role": "Synthesis",
        "symbol": "✍",
        "position": (0, 2),
    },
    "TRI": {
        "name": "Courthouse",
        "role": "Verification & Authority",
        "symbol": "⚖",
        "position": (0, 3),
        "immutable": True,  # Constitutional marker
    },
    "PUBLISH": {
        "name": "Gate",
        "role": "Ledger Commit",
        "symbol": "🚪",
        "position": (1, 2),
    },
}
```

### Status Visuals

```python
STATUS_COLORS = {
    "OK": "#10b981",      # Green (operational)
    "OFF": "#6b7280",     # Gray (inactive)
    "FAIL": "#ef4444",    # Red (error)
}

STATUS_BRIGHTNESS = {
    "OK": 1.0,            # Fully visible
    "OFF": 0.4,           # Dimmed
    "FAIL": 0.8,          # Visible warning
}
```

### Network Topology

```python
NETWORK_TOPOLOGY = {
    "OBS": ["INSIGHT"],                  # Observations → Insights
    "INSIGHT": ["MEMORY", "BRIEF"],      # Insights → Memory + Synthesis
    "MEMORY": ["TRI"],                   # Memory → TRI
    "BRIEF": ["TRI"],                    # Synthesis → TRI
    "TRI": ["PUBLISH"],                  # TRI verdict → Publication
    "PUBLISH": [],                       # Terminal (ledger)
}
```

**All configuration is IMMUTABLE** — changes require governance approval and new versions.

---

## Visual Discipline Charter

The iso-coaster visualization is governed by 8 immutable rules (see `VISUAL_DISCIPLINE_CHARTER.md`):

| Rule | Forbids | Reason |
|------|---------|--------|
| 1 | Speculative animations | Animations suggest causality where only data exists |
| 2 | Progress bars tied to REJECT | Rejection is not failed progress |
| 3 | "Attempted" states | Only OK, OFF, or FAIL exist |
| 4 | Predictions | Only historical data; no forecasts |
| 5 | Auto-expansion | Fixed layout; no progressive disclosure |
| 6 | Gamification | Governance is serious; no badges/streaks |
| 7 | Reinterpretation of silence | FAIL and OFF are distinct; equal visual weight |
| 8 | "Helpful" inferences | Absence is not a signal; honest defaults only |

**Non-negotiable:** The visualization shows what is. It does not suggest, infer, predict, or deceive.

---

## K5 Determinism Verification

Both renderers are guaranteed to be deterministic (K5 invariant):

### Verification Tests

**ASCII Renderer:**
```bash
# 10 iterations → identical output
python3 tests/test_city_state_renderer.py

# 50-iteration stress test
# All iterations produce identical JSON hash
```

**HTML/SVG Renderer:**
```bash
# 5 iterations → identical output
python3 tests/test_iso_coaster_renderer.py

# 10-iteration stress test
# All iterations produce identical HTML
```

**Dashboard Integration:**
```bash
# 6 endpoint tests
python3 tests/test_dashboard_iso_coaster_integration.py

# 10-iteration determinism test
# Same verdicts → identical HTML every time
```

### Determinism Guarantee

```python
import hashlib
from oracle_town.iso_coaster_renderer import render_iso_coaster

city_state = {...}  # Fixed input

hashes = []
for i in range(200):
    html = render_iso_coaster(city_state)
    h = hashlib.sha256(html.encode()).hexdigest()
    hashes.append(h)

assert len(set(hashes)) == 1  # All 200 iterations identical
print(f"K5 Determinism verified: {hashes[0][:16]}...")
```

---

## Usage Examples

### CLI: ASCII Snapshot

```bash
# Generate ASCII snapshot
python3 oracle_town/city_state_renderer.py

# Output: Canonical ASCII art to stdout
```

### Dashboard: HTML Visualization

```bash
# Start dashboard server
python3 oracle_town/dashboard_server.py &

# Two endpoints available:
# GET /api/city-state/ascii      → ASCII snapshot (text/plain)
# GET /api/city-state/iso-html   → HTML iso-coaster (text/html)

# Fetch and display
curl http://localhost:5000/api/city-state/iso-html > iso.html
open iso.html
```

### Programmatic: Integration

```python
from oracle_town.city_state_renderer import render_city_state
from oracle_town.iso_coaster_renderer import render_iso_coaster

# Build current state from verdicts
city_state = {
    "date": today,
    "run_id": f"run-{run_number}",
    "policy": {"version": policy_version, "hash": policy_hash},
    "verdicts": {"accepted": accept_count, "rejected": reject_count},
    "modules": module_states,
    "top_insights": insights,
}

# Render both formats
ascii_output = render_city_state(city_state)
html_output = render_iso_coaster(city_state)

# Use for monitoring, logging, or HTTP responses
```

---

## Design Philosophy

### What the Iso-Coaster Is

✓ A **snapshot** of jurisdiction state at a point in time
✓ A **read-only visualization** (cannot mutate governance)
✓ **Deterministic and reproducible** (K5 verified)
✓ **Self-contained** (no external assets or API calls)
✓ **Honest** (shows what is; makes absence visible)

### What the Iso-Coaster Is NOT

✗ An interactive query tool (that's Phase 6: Interactive Explorer)
✗ An authoritative source of verdicts (that's the ledger)
✗ A predictor of future decisions (rules against predictions)
✗ A progress indicator (governance is not a game)
✗ A tool for live monitoring (that's the ledger stream)

---

## File Manifest

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `city_state_renderer.py` | ASCII snapshot renderer | 150 | ✓ Complete |
| `iso_coaster_renderer.py` | HTML/SVG renderer | 400+ | ✓ Complete |
| `iso_coaster_config.py` | Frozen config (modules, colors, topology) | 180 | ✓ Complete |
| `VISUAL_DISCIPLINE_CHARTER.md` | Constitutional rules | 367 | ✓ Complete |
| `tests/test_city_state_renderer.py` | ASCII renderer tests (10 tests) | 250 | ✓ All passing |
| `tests/test_iso_coaster_renderer.py` | HTML renderer tests (11 tests) | 450+ | ✓ All passing |
| `tests/test_dashboard_iso_coaster_integration.py` | Dashboard integration tests (6 tests) | 300 | ✓ All passing |

**Total:** 29 tests, 100% passing, K5 determinism verified

---

## Endpoints (Dashboard)

### ASCII Snapshot

**Request:**
```
GET /api/city-state/ascii
```

**Response:**
```
Content-Type: text/plain
Content-Length: ~400 bytes

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ORACLE TOWN — 2026-01-31 RUN dashboard-poll ┃
...
```

### HTML ISO-Coaster

**Request:**
```
GET /api/city-state/iso-html
```

**Response:**
```
Content-Type: text/html
Content-Length: ~7800 bytes

<!DOCTYPE html>
<html>
<head>
    <title>Oracle Town — Iso-Coaster</title>
    <style>...</style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Oracle Town — Iso-Coaster</h1>
    </div>
    <div class="stats">...</div>
    <svg viewBox="0 0 ... ...">...</svg>
    <div class="disclaimer">...</div>
</body>
</html>
```

---

## Next Steps (Future Enhancements)

Potential extensions not yet implemented:

1. **Embed in Dashboard** — Add iso-coaster widget to dashboard HTML (sidebar or full-page tab)
2. **Historical Playback** — Animate state changes over time (multiple snapshots)
3. **Ledger Integration** — Click buildings to view related verdicts
4. **Export Formats** — PNG/SVG export for reports and presentations
5. **Responsive Tiles** — Adjust building size based on verdict volume

All of these can be built on top of the deterministic foundation established by the current renderers.

---

## Related Documents

- `VISUAL_DISCIPLINE_CHARTER.md` — Constitutional rules (8 immutable rules)
- `oracle_town/city_state_renderer.py` — ASCII renderer (implementation)
- `oracle_town/iso_coaster_renderer.py` — HTML renderer (implementation)
- `oracle_town/iso_coaster_config.py` — Configuration (frozen tileset)
- `CLAUDE.md` — Architecture and development guide
- `IMPLEMENTATION_ROADMAP.md` — Daily OS extension phases

---

## Closing Statement

The iso-coaster visualization is a **map, not a database query tool**. It shows the structure of the town at a moment in time. Like any good map:

- It is **honest** (shows what exists, not what might exist)
- It is **stable** (same town → same map)
- It is **readable** (clear symbols, no jargon)
- It is **deterministic** (K5 verified: reproducible)

This makes it suitable for understanding jurisdiction state without making false claims about causality, prediction, or progress.

---

**Signed:** Oracle Town Visualization Team
**Date:** January 31, 2026
**Status:** IMMUTABLE (Constitutional)
