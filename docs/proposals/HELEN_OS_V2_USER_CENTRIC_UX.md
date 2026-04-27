# HELEN OS v2 — User-Centric UX Proposal

**Status:** PROPOSAL  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** PROPOSAL  
**Implementation scope:** UX_DESIGN_DOC_UPDATE_ONLY  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  
**Next verb:** review UX proposal  
**Updated:** 2026-04-27 — Apple-like progressive disclosure revision

> This document is a design proposal only.  
> It does not amend the kernel, the ledger, the schema registry, or any sovereign path.  
> It does not constitute a CLOSURE_RECEIPT or TRANCHE_SUB_RECEIPT.  
> Promotion to canon requires a separate KERNEL-gated dispatch.

---

## Product thesis

HELEN OS is not a dashboard.  
It is a decision space.

**Focus Mode** helps the user act.  
**Witness Mode** proves the action was governed.

---

## Design axiom (v2)

> **HELEN OS should not show intelligence everywhere. It should make intelligence feel effortless.**

This is the single governing constraint for all UX decisions:

- If something is not needed right now, it is not shown.
- Complexity is revealed only when the operator reaches for it.
- The default state is calm. Density is opt-in.

---

## Product tagline (locked)

> **HELEN suggests. You decide. Everything is recorded.**

This encodes the three constitutional obligations in one sentence:
- HELEN proposes (non-sovereign, she cannot decide)
- The operator chooses (free will, Rule IV)
- The ledger records (NO RECEIPT = NO CLAIM)

### Constitutional phrase (separate usage — system chrome, not marketing)

> HELEN sees. HELEN proposes. The gate authorizes. The executor acts.  
> The ledger records. The reducer decides.

These two phrases serve different roles and must not be conflated:
- The tagline is the user-facing product promise
- The constitutional phrase is the architectural statement for system chrome and governance documentation

---

## Progressive disclosure architecture

This is the core v2 design shift. The UX is built in layers — each layer visible only when the operator actively reaches for it.

### The three reveal layers

```
LAYER 0 — Ambient (always visible)
  HELEN presence · active intent · three proposals

LAYER 1 — On-demand (tap/click to expand)
  Receipt pill expands → last 5 ledger entries
  AMP status pill expands → provider health panel
  Voice/channels strip expands → channel selector

LAYER 2 — Modal / sheet (deliberate action)
  Witness Mode → slides in as a panel from the right
  Oracle Mode → opens as a full overlay
  Temple Mode → opens as a full overlay
  Settings → modal sheet from bottom
  Knowledge Compiler → separate sheet
```

**Rule:** Nothing moves from Layer 0 to Layer 1 or Layer 2 without an operator gesture.  
HELEN does not push complexity forward. The operator pulls it.

---

## Focus Mode — default daily interface

**Design principle:** I am working. Show me only what I need.

### Default state (Layer 0)

The screen at rest contains exactly these elements:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ◆  HELEN                               │
│                  calm · ready · present                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Prepare my Q3 product strategy                     │   │
│  │  from notes, market research, and recent emails     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [1]  Gather and organise all relevant sources              │
│  [2]  Synthesise key insights and identify the narrative    │
│  [3]  Draft the strategy with a clear executive summary     │
│                                                             │
│  ────────────────────────────────────────────────────────  │
│  ● Latest receipt appended · seq=147                  ›    │
│  ────────────────────────────────────────────────────────  │
│                                                             │
│  [ AMP ]  [ Files ]  [ Notes ]  [ Mail ]  [ Settings ]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**What is always visible:**
- HELEN Intelligence Core (calm, centered, minimal)
- One active intent — user-set or HELEN-suggested
- Exactly three structured action proposals (never more)
- Compact receipt pill: `● Latest receipt appended · seq=N  ›`
- Bottom dock: AMP · Files · Notes · Mail · Settings
- Mode toggle (top-right, minimal): `Focus  /  Witness`

**What is hidden by default (pull to reveal):**
- Receipt ledger detail — behind the receipt pill `›`
- AMP provider health — behind the `AMP` dock item
- Policy gate verdicts — Witness Mode only
- Language / Desire firewalls — Witness Mode only
- Claim workflow counts — Witness Mode only
- Ghost Closure Detector — Witness Mode only
- Reducer Engine state — Witness Mode only
- Knowledge Compiler progress — behind Settings
- Constitutional strip — Witness Mode only

### Interaction patterns

**Receipt pill expansion (tap `›`):**  
The pill expands in-place to show the last 5 ledger entries. Collapses on tap-away. Does not leave the current screen.

**Dock items (tap to open as pop-in sheet):**  
Each dock item slides up as a card from the bottom. The main interface dims but remains visible behind it. Closing the sheet returns to the exact same state.

**Three proposals:**  
Each is tappable. Tapping enters the confirmation beat — a second-level screen:
```
◆  Confirmed?

  Gather and organise all relevant sources
  for the Q3 product strategy

  [Confirm]  [Edit]  [Cancel]
```
Confirmation writes a receipt and returns to Focus Mode with the receipt pill pulsing once.

**HELEN's voice:**  
Waveform appears only when HELEN is speaking. Gone when she is silent. Not a persistent element.

**Operator voice input:**  
A single pill at the bottom edge. Tap to speak. Collapses when not recording.

---

## Witness Mode — advanced inspection interface

**Design principle:** I am watching the system. Reveal the proof.

Accessed via the mode toggle or keyboard shortcut. Slides in as a panel — it does not replace Focus Mode; it overlays it. The operator can return to Focus at any moment.

**Additional elements (beyond Focus Mode Layer 0):**

| Panel | Reveal gesture | Content |
|---|---|---|
| Receipt Ledger | Mode entry | Full append-only pulse, real receipt IDs, cum_hash visible |
| Claim Workflow | Mode entry | PROPOSED / PENDING / ADMITTED / REJECTED counts + rate |
| LEGORACLE State | Active claim only | Verdict badge — appears during evaluation, disappears when done |
| Policy Gate | Tap to expand | Firewall status |
| Reducer Engine | Tap to expand | INPUT / ADMITTED / REJECTED / REDUCTION RATE |
| Knowledge Compiler | Tap to expand | SOURCES / PATTERNS / LAST COMPILE |
| Constitutional Strip | Scroll down | §I–§VIII, each with VERIFIED state |
| Context Stack | Tap to expand | 8-layer technical stack |

**Rule:** Witness Mode panels are additive — they do not replace Focus Mode elements.  
The intent field and three proposals remain visible. Witness Mode adds proof; it does not replace work.

---

## LEGORACLE states

The LEGORACLE gate must reflect the actual claim lifecycle. It must **not** show a permanent verdict as a background UI state.

| State | When shown | Display |
|---|---|---|
| **Gate Clear / No Active Claim** | Default idle | No badge. Quiet green dot in Witness Mode only. |
| **EVALUATING** | Claim is being processed | Gate active, spinner — appears over the dock |
| **SHIP AUTHORIZED** | Gate passed, claim admitted | Green badge — temporary, fades after 3 seconds |
| **SHIP FORBIDDEN** | Gate blocked claim | Red badge — temporary, shows reason code, fades |
| **DENIED** | Hard rejection | Red — persists until operator dismisses |
| **PENDING RECEIPT** | Awaiting chain receipt | Amber — ambient, non-intrusive |

**Rule:** `SHIP FORBIDDEN` must never appear as a persistent background status.  
It is a verdict on a specific claim at a specific moment — not a system identity.  
Showing it permanently implies the OS itself is broken. It is not.

**Rule:** In Focus Mode, gate state is invisible unless a claim is actively being evaluated.  
The operator working on a task should not see governance machinery unless they look for it.

---

## Information density principle

| When | Show | Do not show |
|---|---|---|
| Default / ambient | Intent · Proposals · Receipt pill | Everything else |
| Active work | Confirmation beat · Receipt pulse | Ledger full, gate verdicts |
| Operator expands | Requested panel only | Other panels, unsolicited |
| Witness Mode | Full governance layer | Nothing — reveal all on entry |
| Error / block | Targeted notification | System-wide alert, full cockpit |

**One focus at a time.**  
If a confirmation sheet is open, the dock is dimmed.  
If Witness Mode is open, the confirmation beat is blocked.  
States do not stack. The operator is never managing two layers simultaneously.

---

## Animation and transition vocabulary

These are design constraints, not implementation specs.

| Transition | Style | Duration |
|---|---|---|
| Sheet / panel reveal | Slide up from bottom or right | ~280ms ease-out |
| Receipt pill expansion | Expand in-place | ~180ms ease |
| Proposal confirmation | Cross-fade to confirmation beat | ~200ms |
| Receipt pulse | Single green flash on pill | ~600ms, once |
| Witness Mode entry | Overlay fades in from right | ~300ms ease-out |
| Gate verdict badge | Fade in, hold, fade out | 300ms / 3s / 400ms |
| Voice waveform | Appear on voice start, fade on silence | ~150ms each |

**Rule:** No persistent animations. No breathing orbs. No pulsing backgrounds.  
Motion serves information — it does not decorate it.

---

## Spacing and typographic principles

- Primary action (proposals): large, high contrast, generous line height
- Supporting information (receipt pill, AMP status): smaller, dimmed (`DIM` / 60% opacity)
- Structural chrome (dock, mode toggle): smallest, neutral
- Error or governance signals: color-coded, never more than one visible at a time

**Whitespace is not emptiness. It is signal.**  
Empty space around an intent communicates: this is what matters right now.

---

## Example user intent (canonical reference)

**Replace all esoteric example intents with grounded, work-oriented examples.**

❌ `Explore quantum alignment insights for my work.`  
✅ `Prepare my Q3 product strategy from notes, market research, and recent emails.`

or:

✅ `Research competitors in the AI OS space and prepare a Q3 positioning brief.`

The intent field must feel like an OS for real work, not a meditation application.  
The sacred and poetic register belongs in Oracle Mode and Temple Mode — not in the default intent field.

---

## Four operating modes (product architecture)

| Mode | Design principle | Access pattern |
|---|---|---|
| **FOCUS MODE** | I am working | Default — always present |
| **WITNESS MODE** | I am watching the system | Mode toggle → slides in |
| **ORACLE MODE** | I am exploring symbolic meaning | Dock → full overlay |
| **TEMPLE MODE** | I am composing / reflecting / imagining | Dock → full overlay |

Focus and Witness are the two surfaces of the core OS.  
Oracle and Temple are extended modes — full overlay, accessed deliberately, never the default.

---

## Context maps — technical vs symbolic

Two valid uses of contextual visualization exist. They must not be mixed.

### CONTEXT STACK (Witness Mode — technical, authoritative)

| Layer | Contents |
|---|---|
| User Intent | Active goal, stated or inferred |
| Active Task | Current execution unit |
| Sources | Files, emails, notes, web content in scope |
| Memory Candidates | Retrieved knowledge units from compiled wiki |
| Claims | Proposed, pending, admitted claims |
| Policies | Active policy constraints |
| Receipts | Recent ledger entries in scope |
| Execution State | Current executor status |

This is a technical stack. It maps to real system components.  
It must be labelled `CONTEXT STACK` and must not use spiritual vocabulary.

### AURA CONTEXT MAP (Oracle / Temple only — symbolic, non-authoritative)

Acceptable only in Oracle Mode or Temple Mode, explicitly labelled as a symbolic metaphor.

> ⚠ Symbolic model — not a technical authority layer.

Labels such as AKASHIC, SOUL, TIMELESS, SOURCE are permitted here as poetic metaphors.  
They carry no system authority, emit no receipts, and govern no claims.

**Rule:** Sacred vocabulary must not appear as technical fact unless explicitly labelled symbolic.

---

## What this design is not

- **Not a cockpit.** No permanent wall of metrics, counts, and status indicators.
- **Not a notification OS.** HELEN does not push alerts. The operator pulls information.
- **Not a demo mode.** Every visible element corresponds to a real system state.
- **Not a chatbot UI.** There is no chat window. HELEN speaks through proposals and receipts, not conversation threads.
- **Not a progress-bar OS.** HELEN does not show thinking progress. It shows results.

---

## Summary of design decisions

| Decision | Resolution |
|---|---|
| Core v2 axiom | "Make intelligence feel effortless" — show less, mean more |
| Default view | FOCUS MODE — Layer 0 only |
| Progressive disclosure | Three layers: ambient / on-demand / modal |
| Information density | One focus at a time — panels do not stack |
| Advanced view | WITNESS MODE — slides in, additive |
| Product tagline | HELEN suggests. You decide. Everything is recorded. |
| Default LEGORACLE state | Invisible in Focus Mode; quiet dot in Witness Mode |
| SHIP FORBIDDEN | Verdict only — temporary badge, never persistent |
| Context map (technical) | CONTEXT STACK — 8 grounded layers, Witness Mode only |
| Context map (symbolic) | AURA CONTEXT MAP — Oracle/Temple only, explicitly metaphorical |
| Default example intent | Prepare my Q3 product strategy from notes, market research, and recent emails |
| Sacred vocabulary | Oracle/Temple modes only, never in CONTEXT STACK |
| Persistent cockpit | Removed |
| Three action proposals | Maximum in Focus Mode |
| Animations | Functional only — no decorative motion |
| Voice waveform | Appears on voice activity, absent otherwise |
| Dock items | Open as pop-in sheets — main screen dims behind, never replaced |
| Confirmation beat | Isolated — single action, single screen, single moment |

---

## Closing

HELEN OS v2 respire.

Pas tout affiché en même temps.  
Une intention à la fois.  
L'intelligence se révèle quand on l'appelle — pas avant.

> See less. Understand more. Act faster.
