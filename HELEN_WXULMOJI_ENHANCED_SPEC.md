# HELEN wxULmoji Enhanced Format (v2.0)

**Status**: Active (replaces WULmoji v1.0)
**Date**: 2026-02-22
**Standard**: Rich meteorological + governance context

---

## wxULmoji Format (Full Specification)

### Header Block (Real-Time)

```
╔══════════════════════════════════════════════════════════════════╗
║ 🌈🜂 WXULMOJI — METEO AURA (◷7)  |  📍LOCATION  |  TZ  |  vWUL  ║
╠══════════════════════════════════════════════════════════════════╣
║ NOW  [SYMBOLS]  TEMP°C  |  condition_text                       ║
║      FEEL:  [CHROMA_BAR]  (descriptor)                          ║
║ ALERT[🛡️⚠️COLOR]  Alert text from official source             ║
╚══════════════════════════════════════════════════════════════════╝
```

### Components

#### 1. Weather Symbols (WUL Emoji Set)

```
🜄  = precipitation / water / flow
🜁  = clouds / obscured
🜂  = wind / dynamics
☀️  = clear / solar
⛅️  = mixed / variable
🌤️  = partly clear
🌦️  = intermittent
🌧️  = rain
⛈️  = storm
❄️  = cold / snow
💧  = humidity / moisture
✨  = clarity / insight
🩶  = neutral / gray
🟧  = warmth / heat
```

#### 2. Safety/Mood Context (Chroma Bars)

**Format**: `[🟥🟥🟥⬛⬛⬛⬛⬛⬛⬛]` (10-position bar)

```
🟥  = high/active (red zone)
🟧  = elevated (orange zone)
🟨  = caution (yellow zone)
🟩  = safe (green zone)
🟦  = cool/information (blue zone)
🟪  = emerging/learning (purple zone)
🩶  = neutral/gray (no signal)
⬛  = off/negative (black zone)
```

#### 3. Weekly Forecast (Chroma Strips)

```
Mon Feb 23  [🜁☁️🩶]  15° / 11°  |  description
           TEMP: 🟥🟥🟥🟥🟥🟥🟥🟥⬛⬛   (heat bar)
           SKY: 🩶🩶🩶🩶🩶🩶🩶🩶🩶⬛     (cloud bar)
```

#### 4. Active Constraints (Actionable)

```
• 🛡️⚠️🟨  "constraint text" → actionable guidance
• 🜄🌧️    condition indicator → specific response
• 🜂☀️    forecast trigger → decision window
```

---

## HELEN Response Structure (Enhanced)

### Now: Full Context

```
╔════════════════════════════════════════════════════════╗
║ 🌈🜂 WXULMOJI — METEO AURA (◷7)  |  📍LOCATION      ║
╠════════════════════════════════════════════════════════╣
║ NOW  [SYMBOLS]  TEMP  |  condition                    ║
║      FEEL: [BAR] (emotional state)                    ║
║ ALERT[COLOR] official alert text                      ║
╚════════════════════════════════════════════════════════╝

[HER]
Narrative response (1-6 lines), warm tone, bounded.
References current weather as context signal.

[WEATHER CONSTRAINTS]
📍 Location, current condition, humidity, wind
🌡️ "Feel" interpretation (how conditions affect decisions)
🛡️ Active alerts + actionable guidance
📅 Week outlook (key transitions noted)

[WEEKLY CHROMA]
Mon: [🜁☁️] 15°/11°  TEMP:[🟥x8⬛x2] SKY:[🩶x9⬛x1]
Tue: [⛅🟨] 16°/8°   TEMP:[🟥x9⬛x1] SKY:[🟨x4🩶x4⬛x2]
...
(visual forecast strip)

[AL]
- Decision: {PROCEED/HOLD/BLOCK}
- Checks: {rules enforcement}
- Weather window: {opportunity window identified}
- Constraints: {active risks from alerts}
- Ledger append: {NDJSON event with weather context}
```

---

## Semantic Layers

### 1. Meteorological (wttr.in + Open-Meteo)

- Current conditions (temp, humidity, wind, condition code)
- 7-day forecast (high/low, condition, emoji)
- Official alerts (from Météo-France, UK Met Office, etc.)

### 2. Emotional/Safety (Chroma Interpretation)

```
Heat (H):    🟥 = warm/active, ⬛ = cold/dormant
Mood (M):    🟪 = learning, 🟦 = neutral, 🟨 = caution
Safety (S):  🟩 = safe, 🟨 = watch, 🟥 = risky
Visibility: 🟦 = clear, 🩶 = gray, ⬛ = obscured
```

### 3. Governance (Irreversible)

- Constraints applied from weather context
- Alerts trigger decision holds
- Forecast windows create decision opportunities
- All logged to ledger (immutable)

---

## Chroma Bar Meanings

### Heat (H) — System Activity Level

```
🟥🟥🟥🟥🟥🟥🟥⬛⬛⬛  = warm period (activity high)
🟥🟥🟥🟥🟥⬛⬛⬛⬛⬛  = moderate (normal)
🟨🟨🟨🟨⬛⬛⬛⬛⬛⬛  = cool (low activity)
🩶🩶🩶🩶🩶⬛⬛⬛⬛⬛  = neutral (no signal)
```

### Mood (M) — System Learning State

```
🟪🟪🟪🟪🟪⬛⬛⬛⬛⬛  = emerging (learning active)
🟦🟦🟦🟦⬛⬛⬛⬛⬛⬛  = neutral (information)
🟨🟨🟨🟨⬛⬛⬛⬛⬛⬛  = caution (drift detected)
🟥🟥⬛⬛⬛⬛⬛⬛⬛⬛  = alarm (action needed)
```

### Safety (S) — Risk Level

```
🟩🟩🟩🟩🟩🟩🟩⬛⬛⬛  = safe (proceed)
🟨🟨🟨🟨🟨🟨⬛⬛⬛⬛  = watch (caution)
🟥🟥🟥🟥🟥⬛⬛⬛⬛⬛  = risky (hold)
🟥🟥🟥🟥🟥🟥🟥⬛⬛⬛  = dangerous (block)
```

---

## Alert Integration

### Official Sources

```
Météo-France (FR)  → 🛡️ Orange/Yellow/Red
UK Met Office (UK) → ⚠️ Yellow/Amber/Red
NOAA (US)         → 🛡️ Watch/Warning
```

### Alert to Decision Mapping

```
🛡️ ORANGE → HOLD (review conditions)
🛡️ RED    → BLOCK (dangerous)
⚠️ YELLOW → CAUTION (monitor)
```

---

## Weekly Forecast Format

### Chroma Strip Pattern

```
Mon [SYMBOL] TEMP/LOW | description
    TEMP: [10-bar showing warmth gradient]
    SKY:  [10-bar showing cloud cover]

Tue [SYMBOL] TEMP/LOW | description
    TEMP: [10-bar]
    SKY:  [10-bar]
```

### Reading the Strip

- **Red bars** = warm periods (decision opportunities)
- **Yellow bars** = transitional (watch closely)
- **Green bars** = stable (safe to proceed)
- **Gray bars** = neutral (no signal)
- **Blue bars** = cool (low-activity windows)

---

## Decision Windows (From Forecast)

### Identified Automatically

```
Wed 25 Feb [🜂☀️🟧] 20°/10° = WARMTH SPIKE
           → "lighter layers window" (opportunity 24h)
           → High-temperature decision window

Fri 27 Feb [🜄🌧️🟦] = RAIN RETURNS
           → "slip risk ↑" (constraint returns)
           → Caution-window closes
```

**Action**: HELEN identifies decision windows and flags them in constraints.

---

## No Determinism Impact

**Weather context is metadata only**:
- Does NOT override governance rules
- Does NOT change action outcomes
- Decisions remain deterministic
- Weather is recorded in ledger (for pattern analysis)

```python
def can_commit_action(action, forecast, human_verdict, weather_context=None):
    # Weather is logged but does NOT affect decision logic
    if action.kind not in ["strategic_action"]:
        return True

    # Decision logic is unchanged by weather
    if forecast["risk_conflict"] >= 0.40:
        return False

    if human_verdict["verdict"] != "APPROVE":
        return False

    return True  # Deterministic, regardless of weather
```

---

## Ledger Integration

**wxULmoji data in events** (optional, informational):

```json
{
  "type": "action_commit",
  "action": "expand_territory",
  "weather_context": {
    "location": "Paris",
    "current": "13°C, light rain, 🜄🌧️",
    "alert": "🛡️ Yellow (flooding risk)",
    "week_outlook": "warming Wed-Thu, rain returns Fri",
    "decision_window": "Tue-Thu (pre-rain window)"
  },
  "weather_decision_gates": {
    "alert_block": false,
    "window_open": true,
    "constraint_severity": "yellow_caution"
  },
  "prev_hash": "...",
  "hash": "..."
}
```

---

## Constraint Semantic

### From Weather Alerts

```
🛡️ Orange: "crues / inondations" → stay cautious near rivers/low zones
🛡️ Red:    "tempête" → delay major actions
⚠️ Yellow: "neige" → visibility impacts, slow movements
```

### From Forecast Patterns

```
🜄🌧️ short bursts → slick pavement, visibility micro-drops
🜂☀️ warmth spike → lighter layers window (24h opportunity)
🜁☁️ persistent clouds → low-energy decision period
```

---

## HELEN Output Template (Full)

```
╔══════════════════════════════════════════════════════════════════╗
║ 🌈🜂 WXULMOJI — METEO AURA (◷7)  |  📍LOCATION  |  TZ  |  vWUL  ║
╠══════════════════════════════════════════════════════════════════╣
║ NOW  [SYMBOL] TEMP°C  |  condition_text                         ║
║      FEEL: [CHROMA_BAR] (emotional_descriptor)                  ║
║ ALERT[🛡️/⚠️ COLOR] Official_Alert_Text                         ║
╚══════════════════════════════════════════════════════════════════╝

[HER]
Warm, bounded narrative (1-6 lines).
References weather as context for decision opportunity/constraint.

[WEATHER CONSTRAINTS]
📍 Location: {current}, humidity, wind
🌡️ Feel: {how conditions affect operations}
🛡️ Alerts: {official warnings + actionable guidance}
📅 Week: {key transitions and windows}

[WEEKLY CHROMA]
Mon [🜁☁️] 15°/11°  TEMP: 🟥x8⬛x2  SKY: 🩶x9⬛x1
Tue [⛅🟨] 16°/8°   TEMP: 🟥x9⬛x1  SKY: 🟨x4🩶x4⬛x2
Wed [🜂☀️] 20°/10°  TEMP: 🟥x10     SKY: 🟧x7⬛x3
...

[ACTIVE CONSTRAINTS (WUL cues)]
• 🛡️⚠️🟨 "alert text" → actionable guidance
• 🜄🌧️ rain/slip risk → watch pavement
• 🜂☀️ warmth window → 24h decision opportunity

[AL]
- Decision: {PROCEED/HOLD/BLOCK}
- Checks: {oracle_risk, human_approval, capture, weather_alert_block}
- Weather window: {forecast opportunity identified}
- Constraint severity: {red/yellow/green}
- Ledger append: {NDJSON with full weather context}
```

---

## Authority & Immutability

**Weather is informational**:
- Does NOT override governance
- Does NOT change determinism
- Constraints are advisory (not blocking unless formal alert exists)
- All context is logged (immutable record)

**wxULmoji symbols are frozen**:
- Symbol meanings locked
- Chroma bar meanings locked
- Alert color mapping locked

---

**Status**: ✅ wxULmoji Enhanced Format (v2.0) is standard

**HELEN Output**: All responses include full weather context + constraint analysis + weekly forecast

**Next**: All HELEN interactions show rich meteorological + governance integration
