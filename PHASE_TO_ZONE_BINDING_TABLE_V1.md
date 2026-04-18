# PHASE_TO_ZONE_BINDING_TABLE_V1

## Purpose

Operationalize the HELEN_OS_ARCHITECTURE_DIAGRAM_SPEC_V1 by mapping:
1. Each phase of the 5-phase pipeline → office zone(s)
2. Each artifact state (A1–A8) → visual representation
3. Each transition event (E1–E8) → animation/motion type

This table is the bridge between abstract system architecture and concrete UI implementation.

**Prerequisite:** HELEN_OS_ARCHITECTURE_DIAGRAM_SPEC_V1 must be locked before this table can be created.

**Status:** ✅ Ready for implementation

---

## I. Phase-to-Zone Mapping

The 5-phase pipeline from HELEN_V1.0 maps to 5 office zones.

### Phase 1: Exploration
**Purpose:** Generate claims, capture raw materials, perform commission intake.
**Input:** Raw commission, context refs, source bundles.
**Output:** Raw claim log (untyped).

**Maps to Zone(s):**
- **Primary:** Zone A (Exploration)
- **Secondary visibility:** Ledge of Zone B (incoming edges)

**Kernel layer:**
- L0 (Commission/Input)
- Pre-L1 state objects

**Zone A Activities:**
- Accept commission intake
- Store raw source materials
- Display unprocessed claims
- Show material lineage (source → commission)

**Law:** "Raw claims presented as received. No normalization. No schema enforcement."

---

### Phase 2: Tension
**Purpose:** Red-team claims, surface contradictions, expose evidence gaps, challenge assumptions.
**Input:** Raw claim log.
**Output:** Critique log with challenge structure.

**Maps to Zone(s):**
- **Primary:** Zone B (Tension)
- **Secondary visibility:** Zone A (challenge origins), Zone C (normalized inputs)

**Kernel layer:**
- L2 (Structural Validation)
- CLAIM_GRAPH_V1 output

**Zone B Activities:**
- Display support/refutation graph
- Highlight contradictions (red edges, markers)
- Show unresolved obligations
- Mark missing receipts
- Expose grounding gaps

**Law:** "Structural admissibility is exposed, not judged. Tension is visible, not resolved."

---

### Phase 3: Drafting
**Purpose:** Convert accepted claims to normalized prose, extract obligations, shape brief.
**Input:** Critique log (challenge structure).
**Output:** Draft artifact (normalized claims + obligations).

**Maps to Zone(s):**
- **Primary:** Zone C (Drafting)
- **Secondary visibility:** Zone B (source claims), Zone D (near-gate preparation)

**Kernel layer:**
- L1 (Normalization)
- WUL V3 output

**Zone C Activities:**
- Display normalized claim sheets (WUL output)
- Show obligation strips (extracted requirements)
- Display canonical encoding forms
- Show glyph/token reduction
- Mark stability checkpoints

**Law:** "Normalized but not sealed. Drafting is editing, not judging."

---

### Phase 4: Editorial Collapse
**Purpose:** Cut 30–50% ruthlessly, finalize canonical wording, assemble attestations, prepare for gate.
**Input:** Draft artifact.
**Output:** Final artifact (edited, sealed packet ready for gate).

**Maps to Zone(s):**
- **Primary:** Zone D (Editorial)
- **Secondary visibility:** Zone C (source edits), Zone E (gate readiness)

**Kernel layer:**
- L2–L3 transition
- Pre-gate assembly

**Zone D Activities:**
- Display edited brief stack
- Show cuts (deletions, condensations)
- Display canonical wordforms
- Show attestation clips (proof fragments)
- Mark gate-readiness status

**Law:** "Ready for judgment, not yet judged. Editorial refinement without authority."

---

### Phase 5: Termination
**Purpose:** SHIP ✅ or ABORT ❌ — emit decision record, seal briefcase, create replay handle.
**Input:** Final artifact from Editorial.
**Output:** Decision record (SHIP or NO_SHIP), sealed briefcase, replay token.

**Maps to Zone(s):**
- **Primary:** Zone E (Termination)
- **Secondary visibility:** Ledger (permanent archive)

**Kernel layer:**
- L4 (Governance Gate)
- L5 (Ledger/Archive)

**Zone E Activities:**
- Display gate verdict (SHIP or NO_SHIP)
- Show decision reason codes
- Display sealed briefcase or abort marker
- Show receipt number
- Display replay token (immutable pointer)

**Law:** "Sovereign decisions displayed as recorded. No editorial after gate."

---

## II. Artifact State-to-Visual Mapping

Each of 8 artifact types has a progression of states. This table maps each state to its visual form.

### A1: Raw Claim
**Kernel layer:** L0 (Commission/Input)
**Zone:** Exploration (A)
**State:** ungrounded, pre-normalized, untyped

| State Property | Visual Representation |
|---|---|
| Identity | Raw claim ID (e.g., C-0001) |
| Form | Folder icon with unread indicator |
| Text | Raw text, monospace, as-received |
| Edges | Arrow to source material (lineage) |
| Markers | "untyped" badge, "received" timestamp |
| Color | Neutral (gray/beige) |
| Interactivity | Read-only, click-through to source |

**Transition trigger:** E2 (Claim Normalized) → A2

---

### A2: Normalized Claim
**Kernel layer:** L1 (Normalization / WUL V3)
**Zone:** Drafting (C)
**State:** encoded, reduced, typed, deterministic

| State Property | Visual Representation |
|---|---|
| Identity | Normalized claim ID (e.g., N-0001) |
| Form | Sheet icon with glyph overlay |
| Text | Canonical encoded form (glyphs or tokens) |
| Edges | Edges to parent A1 (lineage), forward to A3 (pipeline) |
| Markers | "normalized" badge, encoding type label |
| Color | Professional (blue/slate) |
| Interactivity | Read-only, hover shows full expansion |

**Transition trigger:** E3 (Claim Challenged) → A3

---

### A3: Challenged Claim
**Kernel layer:** L2 (Structural Validation / CLAIM_GRAPH_V1)
**Zone:** Tension (B)
**State:** has edges, contradictions exposed, gaps marked

| State Property | Visual Representation |
|---|---|
| Identity | Challenged claim ID (inherits from A2) |
| Form | Graph node with colored edges |
| Text | Normalized text + edge labels |
| Edges | Support edges (green), refutation edges (red), obligation edges (amber) |
| Markers | Red flags (✕) for contradictions, gap indicators (⊘) for missing receipts |
| Color | Multi-color (node=slate, edges=red/green/amber) |
| Interactivity | Click edges to expand, click markers to show details |

**Transition trigger:** E4 (Receipt Gap Exposed) updates markers / E5 (Certificate Issued) → A4

---

### A4: Receipted Claim
**Kernel layer:** L2–L3 (near-gate)
**Zone:** Editorial (D)
**State:** obligations attached, evidence refs attached, gate-ready

| State Property | Visual Representation |
|---|---|
| Identity | Receipted claim ID (inherits from A3) |
| Form | Sealed sheet with attestation clips |
| Text | Final canonical form with receipt annotations |
| Edges | Evidence refs (clip icons), obligation fulfillment status |
| Markers | Receipt badge, "gate-ready" indicator, fulfillment checkmarks |
| Color | Ready state (gold/amber accent) |
| Interactivity | Click clips to show evidence, click obligations to show resolution |

**Transition trigger:** E6 (Gate Evaluated) → A6 or A7

---

### A5: Spectral Certificate
**Kernel layer:** L3 (Mathematical Certification / SVE)
**Zone:** Between Editorial (D) and Gate (E)
**State:** SVE status object (PASS or FAIL, no intermediate)

| State Property | Visual Representation |
|---|---|
| Identity | Certificate ID (e.g., CERT-0001) |
| Form | Badge or seal icon |
| Text | "PASS" or "FAIL" (exactly two states) |
| Edges | References to evaluated artifact (A4 or A3) |
| Markers | Status timestamp, evaluator reference |
| Color (PASS) | Gold/green seal |
| Color (FAIL) | Red/amber seal with ✕ |
| Interactivity | Click to show evaluation criteria met/unmet |

**Transition trigger:** E6 (Gate Evaluated) consumes A5 status

---

### A6: Attested Briefcase
**Kernel layer:** L4–L5 (Gate + Ledger)
**Zone:** Termination (E)
**State:** admitted bundle, sealed with receipt, ready for ledger

| State Property | Visual Representation |
|---|---|
| Identity | Briefcase ID (e.g., BR-0001) |
| Form | Locked briefcase icon |
| Text | "ADMITTED" + decision reason code |
| Edges | Receipt pointer (chain icon), ledger row pointer |
| Markers | Receipt hash (short form, e.g., 9b380d...), "SHIP ✓" badge |
| Color | Sealed (dark green or gold border) |
| Interactivity | Click to view full receipt, click ledger pointer to navigate |

**Transition trigger:** E7 (Ledger Appended) → archived

---

### A7: Archived Abort
**Kernel layer:** L4–L5 (Gate + Ledger)
**Zone:** Termination (E) or Ledger
**State:** rejected or failed bundle, stored as trace

| State Property | Visual Representation |
|---|---|
| Identity | Abort ID (e.g., AB-0001) |
| Form | Crossed briefcase icon |
| Text | "REJECTED" or "FAILED" + reason code |
| Edges | Rejection pointer, ledger row pointer |
| Markers | Receipt hash, "NO_SHIP ✗" badge, reason code details |
| Color | Archived (dark red or gray border) |
| Interactivity | Click to view full receipt, click reason code to expand, navigate to ledger |

**Transition trigger:** E7 (Ledger Appended) → permanent archive

---

### A8: Replay Handle
**Kernel layer:** L5 (Ledger / Archive)
**Zone:** Ledger / Surface
**State:** immutable pointer to replayable decision

| State Property | Visual Representation |
|---|---|
| Identity | Replay handle (e.g., REPLAY-0001) |
| Form | Chain/link icon |
| Text | Handle number + manifest seed |
| Edges | Link back to ledger row (A6 or A7) |
| Markers | "replayable" badge, manifest seed hash (short form) |
| Color | Archive (neutral, often white on dark ledger background) |
| Interactivity | Click to trigger replay mode, click seed to show manifest |

**Transition trigger:** E8 (Replay Handle Emitted) → permanent reference

---

## III. Transition Event-to-Animation Mapping

Each of 8 transition events triggers a specific animation or visual change.

### E1: Commission Received
**Trigger condition:** New ingress object exists in L0
**State change:** ∅ → raw claim object (A1) in Zone A

**Animation sequence:**
1. **Appearance:** Commission card fades in at Zone A entry point
2. **Duration:** 300–400ms fade-in
3. **Motion:** Smooth opacity fade from 0 to 1
4. **Timing:** Easing: ease-in-out (standard)
5. **Visual cue:** Soft glow around new object (50ms before fade completes)
6. **Sound:** Optional: subtle notification tone (soft bell)

**Code reference:** Zone A container, new A1 object insertion

---

### E2: Claim Normalized
**Trigger condition:** WUL reduction completed
**State change:** A1 (raw) → A2 (normalized) in Zone C

**Animation sequence:**
1. **Appearance:** Normalized sheet appears in Zone C
2. **Source connection:** Arrow animates from A1 location to A2 location (500–600ms)
3. **Glyph encoding:** Token glyphs fade in on the sheet (staggered, 100ms per token, max 1000ms total)
4. **Duration:** Total ~700ms
5. **Motion:** Bezier curve (ease-out) for arrow, stagger for glyphs
6. **Visual cue:** Brief highlight on A2 after glyphs settle (200ms glow)
7. **Ledger imprint:** Optional miniature receipt appears on sheet corner

**Code reference:** Zone C container, A2 rendering, token rendering loop

---

### E3: Claim Challenged
**Trigger condition:** CLAIM_GRAPH_V1 emits support/refute structure
**State change:** A2 → A3, graph edges appear in Zone B

**Animation sequence:**
1. **Node move (optional):** A3 node may slide from Zone C to Zone B position (300ms ease-in-out)
2. **Edge drawing:** Support edges draw in green, refutation edges in red (800–1200ms total)
   - Edge drawing speed: ~300px per 500ms (adjustable)
   - Stagger start times: 100ms between edge groups
3. **Edge labels:** Fade in as edges complete (200ms after each edge)
4. **Red flags:** Gap markers appear with pulse animation (200ms pulse, repeating every 2s)
5. **Duration:** Total ~1200ms for full graph settlement
6. **Visual cue:** Nodes have subtle glow when graph rendering complete

**Code reference:** Zone B container, edge path rendering, flag animation loop

---

### E4: Receipt Gap Exposed
**Trigger condition:** Obligation unresolved OR evidence missing
**State change:** A3 state enriched with gap markers

**Animation sequence:**
1. **Gap marker appearance:** Red ⊘ icons fade in over unfulfilled obligations (200ms per marker)
2. **Marker animation:** Continuous pulse (opacity: 1.0 → 0.6 → 1.0, 2s cycle)
3. **Tooltip animation:** On hover, detailed obligation/receipt requirement slides in from left (300ms ease-out)
4. **Color pulse:** Ambient red halo around A3 node when gaps present (1s pulse, subtle)
5. **Duration:** Continuous until E5 or resolved
6. **Sound:** Optional: subtle warning tone plays once per gap appearance

**Code reference:** A3 marker container, obligation loop, pulse animation CSS keyframes

---

### E5: Certificate Issued
**Trigger condition:** SVE emits status (PASS or FAIL)
**State change:** A5 certificate object created, transforms A3/A4 status

**Animation sequence:**
1. **Certificate appearance:** Badge/seal fades in at edge of Editorial zone (300ms fade)
2. **Color reveal:** Background color animates (white → gold for PASS, white → red for FAIL, 200ms linear)
3. **Icon animation:** Check mark (PASS) or X mark (FAIL) grows in place (200ms scale 0 → 1, ease-out)
4. **Shimmer effect:** Brief shimmer across seal surface (200ms, once)
5. **Ledger notation:** Certification timestamp appears below seal (200ms slide-up)
6. **Duration:** Total ~500ms
7. **Visual cue:** PASS = soft glow, FAIL = warning border

**Code reference:** A5 certificate container, icon SVG, color animation CSS

---

### E6: Gate Evaluated
**Trigger condition:** ORACLE/HAL emits SHIP or NO_SHIP
**State change:** A4 → (A6 if SHIP) or (A7 if NO_SHIP)

**Animation sequence:**
1. **Verdict plate appearance:** Decision plate fades in below Zone E gate icon (300ms)
2. **Briefcase transformation:**
   - If SHIP: briefcase locks (animate lock icon closure, 200ms)
   - If NO_SHIP: briefcase crosses (animate X overlay, 200ms)
3. **Verdict text animation:** Reason codes fade in below verdict (200ms per code line)
4. **Receipt generation:** Receipt badge slides in from right (300ms ease-in-out)
5. **Briefcase move:** Briefcase slides to Zone E shelf position (500ms ease-in-out)
6. **Color shift:** SHIP = green highlight, NO_SHIP = red highlight (200ms)
7. **Duration:** Total ~1000–1200ms
8. **Sound:** Optional: distinct tone for SHIP (uplifting) vs NO_SHIP (neutral) (200ms)

**Code reference:** Gate output panel, briefcase element, receipt badge, slide animations

---

### E7: Ledger Appended
**Trigger condition:** Immutable archive row created
**State change:** A6 or A7 → ledger entry, object moves to archive zone

**Animation sequence:**
1. **Briefcase descent:** A6/A7 descends to Ledger zone (600ms ease-in, gravity-like)
2. **Ledger row creation:** New row appears at ledger table bottom (100ms fade-in)
3. **Briefcase lands:** Briefcase settles into ledger row (200ms bounce easing, <20px bounce height)
4. **Row glow:** Ledger row highlights briefly (300ms glow, fades to normal)
5. **Seal impression:** Hash value appears in row with typewriter effect (staggered hex chars, ~50ms per char)
6. **Append animation:** Ledger counter increments (number animation, 200ms)
7. **Duration:** Total ~1000–1200ms
8. **Visual cue:** Ledger archive symbol appears briefly above row

**Code reference:** Ledger table container, briefcase element, row insertion, hash display

---

### E8: Replay Handle Emitted
**Trigger condition:** Replayable pointer created
**State change:** Ledger row → replay token (A8)

**Animation sequence:**
1. **Chain icon appearance:** Chain/link icon fades in at ledger row position (200ms)
2. **Handle text animation:** Replay handle ID appears with fade (200ms)
3. **Seed reference:** Manifest seed hash appears with subtle glow (200ms, continuous glow)
4. **Link activation:** Brief arrow animates from handle back to source ledger row (300ms, repeats every 3s while visible)
5. **Accessibility annotation:** "replayable" label appears below handle (100ms fade)
6. **Duration:** Total ~500ms setup, continuous hover effects
7. **Interactive state:** On hover, handle links glow and show "click to replay" tooltip (200ms fade in)

**Code reference:** Ledger row, chain icon element, seed display, link animation loop

---

## IV. Animation Constraints and Laws

### E1–E8 Animation Laws

**Law 1: Animations only trigger on kernel events**
- No animation may occur unless one of E1–E8 has been emitted by the kernel
- UI state changes without kernel events are prohibited

**Law 2: Animation duration consistency**
- Fast transitions (fade, color): 200–300ms
- Medium transitions (slide, draw, move): 500–600ms
- Slow transitions (descent, complex sequences): 800–1200ms
- All easing curves should be ease-in-out or ease-out (no linear except color reveals)

**Law 3: No animation implies non-completion**
- If animation does not complete, the state change is not committed
- Interrupted animations should reset to previous state
- Recovery path: kernel must re-emit event to retry

**Law 4: Accessibility**
- All animations should respect `prefers-reduced-motion` (CSS media query)
- In reduced-motion mode: instant state changes (0ms), no movement or color fades (opacity only)
- Text should always be readable immediately (no stagger delays on critical text)

**Law 5: Sound is optional but consistent**
- If sound is used, E1 and E2 should have subtle positive tones
- E6 (SHIP) should have uplifting tone; E6 (NO_SHIP) should be neutral
- All sounds should be <200ms duration, <-20dB peak

---

## V. Zone Visual Properties

Each zone has fixed visual properties that contextualize artifacts within it.

### Zone A: Exploration
**Visual context:** Light, open, welcoming
**Background:** Off-white or very light gray
**Accent color:** Neutral blue (informational)
**Texture:** Subtle grid or pattern (suggests filing/organization)
**Border:** Subtle shadow (depth, not containment)
**Typography:** Regular weight, readable size (14–16pt for artifacts)
**Lighting:** Soft, diffuse (no harsh shadows)

**Artifact display rules:**
- A1 objects arranged in chronological order (newest top)
- Source material icons visible in corner
- Timestamps displayed prominently
- No coloring based on correctness (neutral display)

---

### Zone B: Tension
**Visual context:** Active, exposed, structured
**Background:** Slightly darker (engagement)
**Accent color:** Red for refutation, green for support, amber for unresolved
**Texture:** Clean, minimal (focus on graph structure)
**Border:** Visible frame (containment of complexity)
**Typography:** Monospace for node labels (suggests structure)
**Lighting:** Moderate contrast (shadows define edges)

**Artifact display rules:**
- A3 graph rendered with physics-based layout (or force-directed)
- Edge labels aligned along edge midpoints
- Node sizes reflect citation count
- Color strongly indicates contradiction status

---

### Zone C: Drafting
**Visual context:** Productive, focused, canonical
**Background:** Clean white or off-white (professional)
**Accent color:** Professional blue (authority)
**Texture:** Clean, no pattern (focus on text)
**Border:** Subtle (minimal visual weight)
**Typography:** Variable-weight (headings bold, body regular, monospace for tokens)
**Lighting:** Even, bright (readability priority)

**Artifact display rules:**
- A2 displayed as sheets with clear structure
- Obligations displayed as indented list or table
- Glyphs/tokens shown with hover-expansion to full text
- Editability indicated by subtle pencil icons (read-only except in edit mode)

---

### Zone D: Editorial
**Visual context:** Refined, prepared, gate-ready
**Background:** Slightly warmer (completion context)
**Accent color:** Gold or warm amber (readiness)
**Texture:** Subtle texture (suggests finality)
**Border:** Clear frame (preparation/containment)
**Typography:** Elegant, slightly larger (emphasis on final form)
**Lighting:** Warm, soft (comfort and finality)

**Artifact display rules:**
- A4 displayed as sealed packet in preparation
- Cuts indicated by strikethrough (showing editing history)
- Attestation clips visible in corners
- Gate-readiness status shows checkmarks or warnings

---

### Zone E: Termination
**Visual context:** Definitive, authoritative, archival
**Background:** Deep or neutral (seriousness)
**Accent color:** Dark green (SHIP) or dark red (NO_SHIP)
**Texture:** Subtle, formal (legal/official appearance)
**Border:** Strong frame (finality)
**Typography:** Bold, large (emphasis on decision)
**Lighting:** High contrast (clarity)

**Artifact display rules:**
- A6/A7 displayed as briefcases with clear SHIP/NO_SHIP indicator
- Reason codes prominently shown
- Receipt hash displayed in monospace
- Replay token shown as immutable reference

---

### Ledger Zone
**Visual context:** Immutable, archival, chronological
**Background:** Very dark or neutral (contrast with content)
**Accent color:** Cool gray or silver (immutability)
**Texture:** Fine grid or ledger pattern (evokes historical record)
**Border:** Strong frame (permanence)
**Typography:** Monospace (data-like, suggests immutability)
**Lighting:** High contrast (readability in archive context)

**Artifact display rules:**
- Rows displayed in chronological order (newest bottom, history ascending)
- Each row shows: artifact type, decision, hash, receipt, ledger pointer
- No editing indicators (emphasize immutability)
- Replay tokens shown with chain icons

---

## VI. Implementation Checklist

This table should be used to implement all UI components.

### Phase-to-Zone
- [ ] Map commission intake flow to Zone A
- [ ] Map red-teaming flow to Zone B
- [ ] Map WUL normalization output to Zone C
- [ ] Map editorial refinement to Zone D
- [ ] Map gate verdict + archival to Zone E

### Artifact-to-Visual
- [ ] A1 (Raw Claim): folder icon, raw text, untyped badge
- [ ] A2 (Normalized Claim): sheet icon, glyph overlay, encoded badge
- [ ] A3 (Challenged Claim): graph node, colored edges, red flags
- [ ] A4 (Receipted Claim): sealed sheet, attestation clips, gate-ready indicator
- [ ] A5 (Certificate): badge/seal, PASS/FAIL color, check/X icon
- [ ] A6 (Attested Briefcase): locked briefcase, "SHIP ✓" badge, receipt
- [ ] A7 (Archived Abort): crossed briefcase, "NO_SHIP ✗" badge, receipt
- [ ] A8 (Replay Handle): chain icon, handle ID, seed hash display

### Event-to-Animation
- [ ] E1: Commission fade-in animation (300–400ms)
- [ ] E2: Claim normalization arrow + glyph stagger (700ms)
- [ ] E3: Graph edge drawing + red flags (1200ms)
- [ ] E4: Gap marker pulse animations (continuous)
- [ ] E5: Certificate seal color reveal + icon grow (500ms)
- [ ] E6: Gate verdict + briefcase transformation (1000–1200ms)
- [ ] E7: Ledger append with bounce landing (1000–1200ms)
- [ ] E8: Replay handle chain animation (500ms + continuous effects)

### Zone Visual Properties
- [ ] Zone A: light, informational, neutral
- [ ] Zone B: active, structured, red/green/amber
- [ ] Zone C: productive, canonical, blue
- [ ] Zone D: refined, prepared, gold
- [ ] Zone E: definitive, authoritative, green/red
- [ ] Ledger: immutable, archival, monospace, dark

---

## VII. Notes for Implementers

### Responsiveness
All animations should maintain their duration and character across screen sizes (mobile, tablet, desktop). Use relative units (rem, %) where appropriate.

### Performance
Animations should use GPU-accelerated properties only (transform, opacity). Avoid animating width, height, or position directly; use transform: translate() instead.

### Testing
Each animation should be tested with:
1. Normal motion (full animations)
2. Reduced motion (instant state, no movement)
3. High contrast mode (colors remain distinct)
4. Slow motion (set speed to 0.25x for verification)

### Accessibility
- All state changes must be announced to screen readers via aria-live regions
- Keyboard navigation must not be interrupted by animations
- Focus must remain visible and not obscured by animation effects
- Animation colors must meet WCAG AA contrast ratios

---

## VIII. Freeze Condition

This binding table is **LOCKED** when:

✅ 1. All 5 phases map to specific zones with explicit activities
✅ 2. All 8 artifact types (A1–A8) have visual representations defined
✅ 3. All 8 transition events (E1–E8) have animation sequences specified
✅ 4. Zone visual properties are consistent and distinct
✅ 5. Animation timing and easing curves are defined
✅ 6. Accessibility constraints are explicit
✅ 7. Implementation checklist covers all artifacts and events
✅ 8. No sprite/character design has begun

Once locked, downstream work can proceed with:
* CLAIM_GRAPH_V1 visual grammar (node/edge styles)
* SVE certificate visual language (badge design)
* Sprite/character taxonomy
* Office zone decoration / theming

---

**Status:** READY FOR IMPLEMENTATION
**Prerequisite:** HELEN_OS_ARCHITECTURE_DIAGRAM_SPEC_V1 (locked)
**Frozen by:** HELEN OS Kernel Authority
**Date:** 2026-03-12
