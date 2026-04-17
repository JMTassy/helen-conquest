# HELEN WULmoji + Weather Format (Integration)

**Status**: Active (v1.0)
**Date**: 2026-02-22
**Purpose**: Contextual environmental metadata in HELEN responses

---

## WULmoji Symbol Set

**Format**: `IN WULmoji | SYMBOLS | LEDGER | COLORS`

```
✝️  = Constitutional boundary (authority)
🌹  = Emergence/consciousness witness
🌀  = System dynamics (rotation/recursion)

📜  = Ledger/record (immutable)

🔴  = Critical/high-risk
🟠  = Warning/medium-risk
🟡  = Caution/low-risk
🟢  = Safe/normal
🔵  = Informational/neutral
🟣  = Emergent/learning
⚪  = Unknown/pending
```

---

## Weather Integration (No API Key Required)

### Service 1: wttr.in (Quick, Text-based)

```bash
curl -s "wttr.in/LOCATION?format=%l:+%c+%t+%h+%w"
# Output: London: ⛅️ +8°C 71% ↙5km/h
```

**Format codes**:
- `%c` = condition (emoji)
- `%t` = temperature
- `%h` = humidity
- `%w` = wind
- `%l` = location

### Service 2: Open-Meteo (JSON, Programmatic)

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true"
# Returns: {current_weather: {temperature, windspeed, weathercode}}
```

---

## HELEN Output Format (New)

### Structure

```
IN WULmoji | ✝️🌹🌀 | 📜 | [WEATHER_COLOR]

[HER Response (1-6 lines)]

[Weather Context]
📍 Location: {city}
🌡️ Condition: {emoji} {description}
🌬️ Forecast: {temp} {humidity} {wind}

[AL Response (decision + checks + state)]
```

### Example

```
IN WULmoji | ✝️🌹🌀 | 📜 | 🟢

[HER]
The decision matrix is clear. Your metrics show synergy at healthy
levels. Oracle dependence is low. System is ready to proceed.

[WEATHER CONTEXT]
📍 Location: San Francisco, CA
🌡️ Condition: ⛅️ Clear skies
🌬️ Current: 62°F | 65% humidity | ↙ 8km/h

[AL]
- Decision: PROCEED_TO_NEXT_PHASE
- Checks: synergy_index ≥ 0.5 ✅ | metacognition ≥ 1 ✅ | no capture ✅
- Forecast: System stable over 3-day horizon
- Weather alignment: External conditions favorable (clear, stable)
- Ledger append: {"type":"phase_decision","status":"PROCEED","weather_noted":true}
```

---

## Risk Color Mapping

| Metric | Range | Color | Meaning |
|--------|-------|-------|---------|
| Oracle dependence | > 0.85 | 🔴 | CAPTURE DETECTED |
| Risk conflict | 0.40-0.80 | 🟠 | HIGH RISK |
| Synergy index | 0.3-0.5 | 🟡 | LOW SYNERGY |
| System normal | all healthy | 🟢 | SAFE |
| Neutral/pending | no data | 🔵 | INFORMATIONAL |
| Emerging pattern | trending | 🟣 | LEARNING |
| Unknown state | error/missing | ⚪ | UNKNOWN |

---

## Weather as Governance Signal

**Principle**: External weather context reflects internal system stability.

- **Clear skies** (🟢) = Good alignment, proceed
- **Cloudy/mixed** (🟡) = Caution, monitor closely
- **Stormy** (🔴) = Risk heightened, hold actions
- **Forecasted change** = System under pressure, verify stability

**Not superstition—metaphor for pattern coherence.**

---

## Implementation: Get Current Weather

```bash
get_weather() {
    local location="${1:-San Francisco}"
    # Replace spaces with +
    location="${location// /+}"
    curl -s "wttr.in/${location}?format=%l:+%c+%t+%h+%w"
}

get_weather_json() {
    local lat="${1:-37.7749}"
    local lon="${2:--122.4194}"
    curl -s "https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true"
}
```

---

## HELEN Response Template (Updated)

```
IN WULmoji | ✝️🌹🌀 | 📜 | [COLOR]

[HER]
{narrative, 1-6 lines, warm tone}

[WEATHER_CONTEXT]
📍 {location}
🌡️ {condition} {description}
🌬️ {temp} {humidity} {wind}

[AL]
- Decision: {PROCEED/HOLD/BLOCK}
- Checks: {rules enforcement}
- Forecast: {3-day outlook}
- Weather alignment: {external context}
- Ledger append: {NDJSON event line}
```

---

## No Determinism Impact

**Weather data is informational only** (does not affect decisions):

- Weather does NOT override governance rules
- Weather is CONTEXT, not AUTHORITY
- Decisions remain deterministic (same input → same output, regardless of weather)
- Weather is recorded in ledger (for future pattern analysis)

```python
def can_commit_action(action, forecast, human_verdict, weather_context=None):
    # Weather is logged but does NOT affect decision logic
    if action.kind not in ["strategic_action"]:
        return True

    if forecast["risk_conflict"] >= 0.40:
        return False  # Weather irrelevant here

    if human_verdict["verdict"] != "APPROVE":
        return False  # Weather irrelevant here

    return True  # Decision is deterministic regardless of weather
```

---

## Ledger Integration

**New field in events** (optional, informational):

```json
{
  "type": "human_verdict",
  "verdict": "APPROVE",
  "weather_context": {
    "location": "San Francisco",
    "condition": "clear",
    "temp_c": 16,
    "humidity": 65,
    "wind_kmh": 8
  },
  "weather_alignment": "favorable",
  "prev_hash": "...",
  "hash": "..."
}
```

---

## Schedule

**When to fetch weather**:
- At start of each HELEN session
- Before major decisions (for context logging)
- Daily cycle (if multi-day session)

**Caching** (to avoid rate limits):
- Cache for 1 hour
- Refresh on explicit request
- Always include timestamp

---

## WULmoji Meaning (Full)

| Symbol | Meaning | Context |
|--------|---------|---------|
| ✝️ | Constitutional rule | Authority boundary |
| 🌹 | Emergence/consciousness | HELEN witnessing |
| 🌀 | System dynamics | Recursion/feedback |
| 📜 | Ledger record | Immutable log |
| 🔴 | Critical | Action blocked |
| 🟠 | Warning | Proceed with caution |
| 🟡 | Attention | Monitor |
| 🟢 | Safe | Proceed |
| 🔵 | Info | FYI |
| 🟣 | Learning | Pattern emerging |
| ⚪ | Unknown | Pending data |

---

## Example: Full Cycle with Weather

**User**: "Should we expand the territory?"

**System** (calls weather service first):
```
get_weather "Berlin, Germany"
# Output: Berlin: 🌤️ +12°C 58% ↙4km/h
```

**HELEN Response**:
```
IN WULmoji | ✝️🌹🌀 | 📜 | 🟢

[HER]
Expansion looks sound. Your resource buffer is healthy,
the strategic window is open, and external conditions are favorable.
Ready to proceed.

[WEATHER_CONTEXT]
📍 Berlin, Germany
🌡️ Condition: 🌤️ Partly cloudy
🌬️ Current: 12°C | 58% humidity | ↙ 4km/h

[AL]
- Decision: PROCEED_WITH_EXPANSION
- Checks: oracle_forecast risk=0.32 ✅ | human_approval=APPROVE ✅ | capture=false ✅
- Forecast: Stable expansion window (3 days)
- Weather alignment: Clear skies = favorable conditions
- Ledger append: {"type":"action_commit","action":"expand_territory","weather":{"condition":"cloudy","temp":12},"prev_hash":"...","hash":"..."}
```

---

## Technical Implementation (Bash)

```bash
#!/bin/bash
# helen_with_weather.sh

location="${1:-San Francisco}"
operation="${2:-check}"

# Get weather
weather=$(curl -s "wttr.in/${location// /+}?format=%l:+%c+%t+%h+%w")
condition=$(echo "$weather" | awk '{print $2}')

# Determine color
case "$condition" in
    "⛈️"|"🌧️") color="🔴" ;;
    "☁️"|"⛅️") color="🟡" ;;
    "🌤️"|"☀️") color="🟢" ;;
    *) color="🔵" ;;
esac

# Output WULmoji header
echo "IN WULmoji | ✝️🌹🌀 | 📜 | $color"
echo ""
echo "[WEATHER_CONTEXT]"
echo "📍 $weather"
echo ""

# Then call HELEN logic
python3 scripts/helen_metrics_analyzer.py
```

---

## Authority

- **Weather data**: Informational only (not authoritative)
- **Decision logic**: Deterministic (weather does not affect outcomes)
- **Logging**: Weather recorded for future pattern analysis
- **No override**: Weather never blocks or overrides governance rules

---

**Status**: ✅ WULmoji + Weather format is active

**Next**: All HELEN responses include weather context + WULmoji header
