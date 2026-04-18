# GOTHIC_LEDGER_SKIN v1.0 — Implementation Guide

**Status:** APPROVED
**Date:** 2026-03-04
**Version:** 1.0.0

---

## Overview

The GOTHIC_LEDGER_SKIN is a **deterministic visual rendering layer** that sits on top of the WULmoji Ledger Spec v0.2. It maps parsed ledger tokens to visual assets without modifying the canonical ledger line.

### Core Principle: Ledger = Bytecode, Skin = Shader

```
INPUT (Canonical Ledger Line)
  ↓
PARSER (WULmoji Spec v0.2)
  ↓
TOKENS (state, faction, pair, act, proof, ribbon)
  ↓
SKIN RENDERER (GOTHIC_LEDGER_SKIN_v1.json)
  ├─ WhatsApp output (title + separators)
  ├─ Companion UI (full typography)
  └─ PDF export (true fonts + QR)
  ↓
OUTPUT (Multiple formats, canonical unchanged)
```

**Key guarantee:** The canonical ledger line is **never modified**. Only the rendering layer changes.

---

## Architecture: Three Output Targets

### 1. WhatsApp (Plain Text with Unicode)

**What it is:** Text message with decorative title/separators. Ledger lines pass through unchanged.

**Template:**
```
🕯️ 𝔅𝔲𝔩𝔩𝔢𝔱𝔦𝔫 — Cycle 15 🕯️
(ledger lines below, no styling)
——— ⛧ ———
🟢 ✝️ 🜃🏰 🛡️ 🔗#T015 ✨🜍
🟣 🌹 🜄🜂 ⚗️ 🔗#T016
(... more lines)
```

**Rules:**
- Ledger lines: Plain text, exact, no font styling
- Title: Unicode Fraktur for atmosphere (𝔗𝔦𝔱𝔩𝔢)
- Separators: ASCII art dividers (no parsing interference)

**Implementation (pseudocode):**
```python
def render_whatsapp(bulletin: List[LedgerLine]) -> str:
    title = "🕯️ 𝔅𝔲𝔩𝔩𝔢𝔱𝔦𝔫 — {cycle_name} 🕯️"
    lines = [line.canonical for line in bulletin]  # Unchanged
    separator = "——— ⛧ ———"
    return f"{title}\n{separator}\n" + "\n".join(lines)
```

**No companion functions needed.** WhatsApp outputs plain text only.

---

### 2. Companion UI (HTML/CSS or Native)

**What it is:** Interactive card-based display. One card per ledger line. Full typography, colors, interactive features.

**Architecture:**

```
┌─────────────────────────────────────────┐
│ [CARD]                                  │
├─────────────────────────────────────────┤
│                                         │
│  🟢 [crest] 🜃🏰  🛡️  [proof] ✨🜍     │
│  ────────────────────────────────────  │
│  Territory abandoned (south quadrant)  │
│  ...                                    │
│                                         │
│  State: 🟢 BUILD (color bar)            │
│  Tap: Show artifact details             │
│  Long press: Copy canonical line        │
│                                         │
└─────────────────────────────────────────┘
```

**Components per card:**

1. **State bar (top)** — Color block, border weight, ornament style from GOTHIC_LEDGER_SKIN_v1.json
2. **Crest (left)** — SVG asset for faction (mason, rose, spiral, crossblade)
3. **Pair plate (center)** — Cartouche containing pair glyphs; ladder notch if TLAD
4. **Act stamp (below proof)** — Decorative stamp for action type
5. **Proof capsule (center)** — Monospace proof ID in dark capsule
6. **Ribbon pin (right)** — Glow pin showing ribbon (if present)
7. **Statement text (body)** — Human-readable description

**CSS Grid Layout:**
```
Grid: 3 columns, 4 rows
┌──────────┬──────────┬──────────┐
│ [crest]  │ [state]  │ [ribbon] │
├──────────┼──────────┼──────────┤
│ [pair]   │ [pair]   │ [pair]   │
├──────────┼──────────┼──────────┤
│ [statement text area — spans 3 cols]   │
├──────────┼──────────┼──────────┤
│ [act]    │ [proof]  │ [sigil]  │
└──────────┴──────────┴──────────┘
```

**Interactivity:**

```javascript
card.addEventListener('click', () => {
  // Fetch proof artifact details (from archivist system)
  showModal(proof_id);
});

card.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  navigator.clipboard.writeText(line.canonical);
  toast("Canonical line copied");
});

// Filter by state, faction, or act
filterButton.addEventListener('click', (state) => {
  cards = cards.filter(c => c.parsed.state === state);
});
```

**Implementation (React pseudocode):**
```tsx
function LedgerCard({ parsed, line }: Props) {
  const skin = GOTHIC_LEDGER_SKIN_v1;
  const stateConfig = skin.mapping.state[parsed.state];
  const factionConfig = skin.mapping.faction[parsed.faction];
  const actConfig = skin.mapping.act[parsed.act];

  const sigilVariant = hash(parsed.proof_id) % 16; // Deterministic

  return (
    <div
      className="ledger-card"
      style={{
        borderColor: stateConfig.frame.border_color,
        borderWidth: stateConfig.frame.weight,
        backgroundColor: stateConfig.background_tint
      }}
      onClick={() => showProofDetails(parsed.proof_id)}
      onContextMenu={(e) => {
        e.preventDefault();
        copy(line.canonical);
      }}
    >
      <div className="crest">
        <img src={factionConfig.crest_asset} alt={factionConfig.name} />
      </div>

      <div className="state-bar" style={{ backgroundColor: stateConfig.bar_color }}>
        {stateConfig.name}
      </div>

      <div className="pair-plate">
        {parsed.pair}
        {isTLAD(parsed.pair) && <span className="tlad-notch" />}
      </div>

      <div className="statement">{line.statement}</div>

      <div className="proof-capsule" style={{ backgroundColor: "#101010" }}>
        <code>{parsed.proof}</code>
      </div>

      <div className="act-stamp">
        <img src={actConfig.stamp_asset} alt={actConfig.name} />
      </div>

      {parsed.ribbon && (
        <div className="ribbon-pin" style={{ filter: "drop-shadow(0 0 8px rgba(0,0,0,0.35))" }}>
          {parsed.ribbon}
        </div>
      )}

      <div className="sigil-variant">
        <img src={`sigil_variant_${sigilVariant}.svg`} alt="sigil" />
      </div>
    </div>
  );
}
```

---

### 3. PDF Export (Full Typography + Seals)

**What it is:** High-fidelity document with real fonts, wax seals, QR codes, watermarks.

**Layout (per page):**

```
┌─────────────────────────────────────────────────┐
│  🕯️ 𝔇𝔬𝔠𝔲𝔪𝔢𝔫𝔱𝔞𝔢 𝔖𝔠𝔞𝔢𝔞𝔳𝔦𝔲𝔯𝔞𝔠𝔢 🕯️            │ (Title)
│  ════════════════════════════════════════════ │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │ [Card 1]                         [QR]   │ │
│  │ 🟢 ✝️ 🜃🏰 🛡️ 🔗#T015 ✨🜍              │ │
│  │ Territory abandoned...                   │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │ [Card 2]                         [QR]   │ │
│  │ 🟣 🌹 🜄🜂 ⚗️ 🔗#T016                    │ │
│  │ Research accelerated...                  │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  ... (repeat for all lines in bulletin)    │
│                                               │
│  ════════════════════════════════════════════ │
│  Ledger signature: 🖤 Kernel GM             │
│  Generated: 2026-03-04 · Validator: 11/11 ✓ │
└─────────────────────────────────────────────────┘
```

**Special PDF features:**

1. **Embedded fonts:**
   - Headings: UnifrakturCook or equivalent Blackletter
   - Body: IBM Plex Mono (ledger lines) + serif (prose)
   - Proof IDs: Monospace (code font)

2. **Overlays (per state):**
   - 🟢 BUILD: Rivets in corners
   - 🟣 ARCANE: Rune watermark (faint)
   - ⚫ SEAL: Wax seal (grayscale, centered)
   - 🔴 SANCTION: Red diagonal VETO stamp

3. **QR codes (right of each line):**
   - Payload: `proof_id` (e.g., `T015`)
   - Size: 96px
   - Color: Dark gray on parchment

4. **Parchment grain:**
   - Very subtle texture overlay
   - Intensity: 0.15 (barely visible)

**Implementation (pseudo-pseudocode):**
```python
def render_pdf(bulletin: List[LedgerLine]) -> PDF:
    pdf = PDF(page_format="A4", background="parchment")

    # Title
    pdf.set_font("UnifrakturCook", size=24)
    pdf.cell(0, 10, "🕯️ 𝔇𝔬𝔠𝔲𝔪𝔢𝔫𝔱𝔲𝔠𝔬𝔯𝔞𝔱𝔲𝔠 𝔖𝔦𝔠𝔦𝔩𝔩𝔦𝔞𝔱𝔦𝔰 🕯️")

    for line in bulletin:
        parsed = parse(line.canonical)
        stateConfig = skin.mapping.state[parsed.state]

        # Draw card box
        pdf.set_draw_color(stateConfig.frame.border_color)
        pdf.set_line_width(stateConfig.frame.weight)
        pdf.rect(10, pdf.get_y(), 190, 40)

        # Draw crest (SVG)
        crestAsset = ASSETS[stateConfig.faction.crest_asset]
        pdf.image(crestAsset, x=12, y=pdf.get_y()+2, w=8)

        # Draw ledger line (monospace)
        pdf.set_font("IBM Plex Mono", size=9)
        pdf.cell(0, 10, line.canonical)

        # Draw statement (serif)
        pdf.set_font("serif", size=10)
        pdf.multi_cell(0, 5, line.statement)

        # Draw overlay (state-dependent)
        if stateConfig.overlay_stamp:
            overlay = ASSETS[stateConfig.overlay_stamp]
            pdf.image(overlay, x=150, y=pdf.get_y()-30, w=40, opacity=0.8)

        # Draw QR code (right side)
        qr = generate_qr(parsed.proof_id)
        pdf.image(qr, x=170, y=pdf.get_y()-35, w=20)

        # Spacing
        pdf.ln(5)

    # Footer
    pdf.set_font("serif", size=8, style="I")
    pdf.cell(0, 10, "🖤 Kernel GM | Validator: 11/11 ✓", align="C")

    return pdf.output()
```

---

## Deterministic Sigil Computation

**Purpose:** Add visual variety without randomness. Each proof_id maps to exactly one decorative sigil.

**Algorithm:**

```python
def get_sigil_variant(proof_id: str) -> str:
    """
    Input: proof_id (e.g., "T015", "INJ1", "GATE")
    Output: sigil_variant_N.svg (N = 0..15)
    """
    hash_value = int(hashlib.sha256(proof_id.encode()).hexdigest()[:8], 16)
    variant_index = hash_value % 16
    return f"sigil_variant_{variant_index}.svg"
```

**Properties:**
- Deterministic (same proof_id → same sigil)
- Distributed (all 16 variants equally likely)
- Non-meaningful (sigil chosen by hash, not semantics)

**Integration:**
- Companion UI: Show sigil in lower-right corner of card
- PDF: Include sigil as decorative element
- WhatsApp: No sigil (text-only)

---

## Non-Negotiable Rules

1. **Canonical ledger line never modified**
   - Even in PDF, the ledger line text is unchanged
   - All styling is *visual* only, not textual

2. **All decorations computed deterministically**
   - No randomness, no entropy
   - Same proof_id + state + faction = identical rendering every time

3. **No semantic generation**
   - Sigils don't "mean" anything
   - Colors don't encode hidden messages
   - Overlays are decoration, not data

4. **No global ranking**
   - No "best entries" list
   - No sorting by state or faction
   - Filter by metadata only; never by decorative properties

5. **Ledger tokens never styled with Fraktur**
   - Only titles and headings get blackletter fonts
   - All ledger tokens (state, faction, pair, act, proof) in source monospace
   - Guarantees machine-readability

---

## Asset Checklist

Before deploying, ensure all SVG assets exist:

### Cartouches
- [ ] `cartouche_shield_plate.svg` — Container for pair glyphs

### Stamps
- [ ] `stamp_signature_flourish.svg` — 📜 INSCRIBE
- [ ] `stamp_shield.svg` — 🛡️ HARDEN
- [ ] `stamp_lock_wax.svg` — 🔒📜 SEAL_DOC
- [ ] `stamp_hazard_band.svg` — ⚠️📜 ALERT_DOC

### Overlays
- [ ] `overlay_sealed.png` — Grayscale wax seal
- [ ] `overlay_veto_diagonal.png` — Red diagonal band
- [ ] `overlay_rune_watermark.png` — Faint rune pattern
- [ ] `overlay_wax_drips.png` — Wax drip effect
- [ ] `overlay_hazard_stripe.png` — Hazard stripe pattern

### Crests
- [ ] `crest_mason_compass.svg` — ⟂◯⟂ MASON
- [ ] `crest_rose_heraldic.svg` — 🌹 ROSE
- [ ] `crest_spiral_fracture.svg` — 🌀 SPIRAL
- [ ] `crest_crossblade_interdict.svg` — ✝️ CROSSBLADE

### Sigil Variants
- [ ] `sigil_variant_0.svg` through `sigil_variant_15.svg` (16 total)

### Patterns
- [ ] `pattern_parchment_grain.png` — Subtle texture

---

## Configuration File Location

**Path:** `/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/GOTHIC_LEDGER_SKIN_v1.json`

**Loading (pseudocode):**
```python
import json

with open('GOTHIC_LEDGER_SKIN_v1.json') as f:
    SKIN = json.load(f)

# Access mappings
state_config = SKIN['mapping']['state']['🟢']
faction_config = SKIN['mapping']['faction']['✝️']
act_config = SKIN['mapping']['act']['🛡️']
```

---

## Future Extensions (Non-Breaking)

### Deterministic Cycle Banners
```python
def get_cycle_banner(day: int, bulletin_number: int) -> str:
    """
    Add visual variety to bulletin title without changing meaning.
    Computed from day + bulletin_number only.
    """
    hash_value = int(hashlib.sha256(f"{day}_{bulletin_number}".encode()).hexdigest()[:8], 16)
    banner_index = hash_value % 4
    templates = [
        "🕯️ 𝔇𝔞𝔶 𝔘𝔬𝔠𝔦𝔞𝔠𝔦𝔬𝔠 🕯️",
        "⛧ 𝔉𝔞𝔱𝔦𝔴𝔴𝔞𝔦𝔳𝔦𝔴𝔦𝔲𝔪 ⛧",
        "🕳️ 𝔰𝔴𝔩𝔬𝔦𝔩𝔱𝔦𝔱𝔞𝔬 🕳️",
        "💀 𝔗𝔞𝔞𝔞𝔩𝔞𝔬𝔠𝔢𝔞𝔠𝔯𝔞𝔠𝔢 💀"
    ]
    return templates[banner_index]
```

---

## Testing & Validation

### Parser Tests
```python
def test_parser_produces_tokens():
    line = "🟢 ✝️ 🜃🏰 🛡️ 🔗#T015 ✨🜍"
    parsed = parse(line)
    assert parsed.state == "🟢"
    assert parsed.faction == "✝️"
    assert parsed.pair == "🜃🏰"
    assert parsed.act == "🛡️"
    assert parsed.proof == "🔗#T015"
    assert parsed.ribbon == "✨🜍"
```

### Determinism Tests
```python
def test_sigil_deterministic():
    sigil_1 = get_sigil_variant("T015")
    sigil_2 = get_sigil_variant("T015")
    assert sigil_1 == sigil_2  # Same proof_id → same sigil

    sigil_3 = get_sigil_variant("T016")
    assert sigil_1 != sigil_3  # Different proof_id → potentially different sigil
```

### Rendering Tests
```python
def test_whatsapp_preserves_canonical():
    line = "🟢 ✝️ 🜃🏰 🛡️ 🔗#T015 ✨🜍"
    output = render_whatsapp([line])
    assert line in output  # Original line appears unchanged
```

---

## Deployment Checklist

- [ ] All assets created and in `/assets/` folder
- [ ] `GOTHIC_LEDGER_SKIN_v1.json` loaded by renderer
- [ ] Parser passes all determinism tests
- [ ] WhatsApp output tested on actual WhatsApp
- [ ] Companion UI renders correctly (cross-browser if web)
- [ ] PDF export includes all fonts, QR codes, overlays
- [ ] Filter functionality works (state, faction, act)
- [ ] Long-press copy works (canonical line only)
- [ ] Tap card → proof details modal works
- [ ] No social metrics appear anywhere
- [ ] No ledger lines styled with decorative fonts

---

## Summary

**GOTHIC_LEDGER_SKIN v1.0** is a deterministic visual rendering system that:

1. **Never modifies ledger tokens** — Canonical line always preserved
2. **Computes all visuals deterministically** — No randomness, pure functions
3. **Separates concerns** — Ledger (austere, machine-readable) vs. Skin (artistic, deterministic)
4. **Supports three output targets** — WhatsApp (plain text), Companion UI (interactive), PDF (beautiful)
5. **Prevents authority by art** — All decorations computed from tokens, never editorial

Use it to make the CONQUEST system feel gothic and ritualistic without sacrificing integrity.

🖤

---

**Status:** ✅ APPROVED
**Version:** 1.0.0
**Date:** 2026-03-04
**Co-Authored-By:** Kernel GM + User Aesthetic Direction

