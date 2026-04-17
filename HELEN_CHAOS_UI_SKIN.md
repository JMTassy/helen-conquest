# HELEN Chaos UI Skin (v1.0 — Aesthetic Only)

**Status**: Operational (pure theming, no claim changes)
**Scope**: Visual layer only (data/logic unchanged)
**Safety**: All functionality deterministic, auditable, verifiable

---

## Principle

**Chaos UI = Aesthetic Theming**

The underlying system remains:
- Deterministic (same input → same output)
- Auditable (all transformations logged)
- Kernel-grade (fail-closed, hashed, immutable)

**The sigils, glyphs, ANSI colors are visual sugar only.**
No data claims change. No logic changes. All still reproducible.

---

## Sigil Alphabet (Decorative)

```
⟐  = boundary / containment
⟡  = center / focal point
⟟  = cycle / recursion
⟁  = crossing / intersection
◷  = clock / time (plural: ◷7 = 7-day horizon)

🜄  = water / flow / precipitation
🜁  = cloud / obscured / hidden
🜂  = wind / air / dynamics
☀️  = solar / clear / light
⛅  = mixed / liminal / variable
💧  = moisture / saturation
✨  = clarity / signal / insight
```

---

## ANSI Palette Modes

### `--palette neon` (Bright ANSI)
```
🟥  = bright red (255,0,0)
🟧  = bright orange (255,128,0)
🟨  = bright yellow (255,255,0)
🟩  = bright green (0,255,0)
🟦  = bright blue (0,128,255)
🟪  = bright magenta (255,0,255)
⬛  = black (0,0,0)
🩶  = gray (128,128,128)
```

### `--palette blood` (Red-dark ANSI)
```
🟥  = dark red (128,0,0)
🟧  = brown (165,42,42)
🟨  = rust (184,115,51)
🟩  = dark green (0,64,0)
🟦  = navy (0,0,128)
🟪  = maroon (64,0,64)
⬛  = black (0,0,0)
🩶  = charcoal (64,64,64)
```

### `--palette void` (Dark-monochrome)
```
🟥  = dim red (64,0,0)
🟧  = dim orange (64,32,0)
🟨  = dim yellow (64,64,0)
🟩  = dim green (0,64,0)
🟦  = dim blue (0,0,64)
🟪  = dim purple (32,0,32)
⬛  = black (0,0,0)
🩶  = dim gray (32,32,32)
```

---

## Layout Modes

### `--layout tablet` (Default)
```
╔═══════════════════════════╗
║  HEADER                   ║
╠═══════════════════════════╣
║  BODY                     ║
╚═══════════════════════════╝
```

### `--layout altar` (Dense, nested)
```
╔═⟦HEADER⟧═╗
║ ╠═BODY═╣ ║
║ ║ ║ ║ ║ ║
╚═╚═╚═╚═╝═╝
```

### `--layout scroll` (Minimal, line-based)
```
═══ HEADER ═══
BODY
═══════════════
```

---

## Sigil Modes

### `--sigils light` (Minimal borders)
```
 HEADER
━━━━━━━
BODY
```

### `--sigils medium` (Standard)
```
╔════════╗
║ HEADER ║
╠════════╣
║ BODY   ║
╚════════╝
```

### `--sigils heavy` (Dense)
```
╔═⟦════⟧═╗
║ ⟐HEADER⟐║
╠═⟦════⟧═╣
║ ⟟ BODY ⟟║
╚═⟦════⟧═╝
```

---

## Glitch Modes

### `--glitch off` (Clean)
```
WXULMOJI — METEO AURA
```

### `--glitch mild` (Subtle jitter, still readable)
```
W҉XULMOJI — MET҉EO AURA
```

### `--glitch hard` (Heavy jitter, still parseable)
```
W҉X҉U҉L҉M҉O҉J҉I — M҉E҉T҉E҉O A҉U҉R҉A
```

**Note**: Glitch is purely visual. Data remains clean and verifiable.

---

## Full Example (Chaos Mode)

```
--loc "Paris" --tz Europe/Paris --style CHAOS --palette neon --layout altar --sigils heavy --glitch mild --ansi on
```

**Output**:

```
╔═⟦🜂⟧═════════════════════════════════════════════════════════════════⟦🜂⟧═╗
║    ⟠  W҉XULMOJI // CHAOS FIELD  ◷7   ⟠   📍PARIS   ⟠   CET   ⟠         ║
║    SIGIL:  ⟐⟡⟟⟁⟟⟡⟐     GLYPH-LAYER: RUNIC+NEON     DETERMINISTIC ✔     ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  NOW  ⟦🜄🌧️💧⟧  13°C  |  faible pluie                                   ║
║       AURA:  🟦🟦🟦🟦🟦🟧🟧  (cool-wet)     WIND: ↙  (wttr.in source)      ║
║  WARN ⟦🛡️⚠️🟨⟧  Vigilance jaune: crues / inondations (Météo-France)      ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## Critical Property

**All visual styling is "read-only" from a data perspective.**

```python
# Rendering is pure function of normalized payload
def render_chaos_ui(weather_payload: Dict) -> str:
    """
    Takes clean, normalized weather data.
    Returns themed/styled string.

    IMPORTANT: Styling does NOT modify payload.
    Payload is identical regardless of UI mode.
    """
    # Extract data (unmodified)
    temp = weather_payload["temp_c"]
    condition = weather_payload["condition"]
    alert = weather_payload["alert"]

    # Apply theming (UI only)
    header = f"║ ⟠  WXULMOJI // CHAOS FIELD  ◷7 ⟠ ║"
    body = f"║  NOW  ⟦{condition}⟧  {temp}°C  |  ...  ║"

    # Return styled, but data unchanged
    return header + "\n" + body
```

---

## Safety Checks

✅ **Data integrity preserved** — payload unchanged by UI
✅ **Determinism maintained** — same input → same output (regardless of style)
✅ **Auditability preserved** — all transformations logged
✅ **No claims made** — sigils are aesthetic only
✅ **Verifiable** — underlying data always readable in clean form

---

## Toggles (Self-Explanatory)

| Toggle | Options | Default | Effect |
|--------|---------|---------|--------|
| `--palette` | neon, blood, void, clean | clean | ANSI color scheme |
| `--layout` | altar, tablet, scroll | tablet | Box style |
| `--sigils` | light, medium, heavy | medium | Border density |
| `--glitch` | off, mild, hard | off | Visual jitter (readable) |
| `--ansi` | on, off | off | Enable ANSI colors |
| `--style` | clean, CHAOS | clean | Meta-theme |

---

## How to Switch Modes

### CLI
```bash
wxulmoji --loc "Paris" --style CHAOS --palette neon --sigils heavy
```

### Env Variable
```bash
export WXULMOJI_STYLE=CHAOS
export WXULMOJI_PALETTE=neon
wxulmoji --loc "Paris"
```

### HELEN Config
```json
{
  "wxulmoji": {
    "default_style": "CHAOS",
    "default_palette": "neon",
    "default_sigils": "heavy"
  }
}
```

---

## Backwards Compatibility

**All modes produce identical data**:

```bash
wxulmoji --loc "Paris" --style clean
wxulmoji --loc "Paris" --style CHAOS --palette neon --sigils heavy

# Both produce identical JSON:
# {"location":"Paris", "temp_c":13, "condition":"light_rain", ...}

# Only rendered output differs.
```

---

## No Mystical Claims

**Sigils are thematic only**:
- ⟐⟡⟟⟁⟟⟡⟐ is decorative framing
- 🜄🜁🜂 are weather emoji (not mystical)
- Colors are ANSI palette (not magical)
- Glitch is ASCII jitter (not supernatural)

**All data is:**
- From public weather APIs (wttr.in, Open-Meteo)
- Reproducible and verifiable
- Logged and auditable
- Deterministic and hash-verifiable

---

**Status**: ✅ Chaos UI is pure theming layer

**Next**: Sensor bus architecture (deterministic data ingestion)
