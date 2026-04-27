# HELEN OS v2 — User-Centric UX

NON_SOVEREIGN — DESIGN_CANON — DOCTRINE

```
artifact_type:         UX_DESIGN_CANON
proposal_id:           HELEN_OS_V2_USER_CENTRIC_UX
authority:             NON_SOVEREIGN
canon:                 DESIGN_CANON
lifecycle:             DOCTRINE
implementation_status: NOT_IMPLEMENTED
helen_status:          DOCTRINE (validated 2026-04-27, peer-review PASS 9/9,
                       reviewer session a7e1460ed050b535f; promotion to INVARIANT
                       requires §12 reconciliation option + implementation spec)
memory_class:          CANDIDATE_UX
captured_on:           2026-04-27
captured_by:           operator (jeanmarie.tassy@uzik.com)
promoted_on:           2026-04-27
promoted_by:           operator directive
peer_review:           PASS 9/9 (session a7e1460ed050b535f, K2/Rule 3 enforced)
provenance:            operator UX redirection 2026-04-27, in dialogue with
                       the operator dashboard contract (six invariants).
related_memory:        feedback_operator_dashboard_contract.md
                       project_helen_amp.md
                       feedback_helen_protagonist_not_hologram.md
```

> **Core thesis**
> HELEN OS should not show intelligence everywhere.
> It should make intelligence feel effortless.

> **UX canon (preserved verbatim)**
> HELEN n'est pas un cockpit.
> HELEN est une présence calme qui ouvre le bon panneau au bon moment.

---

## §1. Executive Summary

HELEN OS v2 reframes the operating system from "always-on cockpit" to "calm
presence that opens the right panel at the right moment." The OS retains its
constitutional spine — sovereign kernel, append-only ledger, K-gate
discipline, NO RECEIPT = NO CLAIM — but the **interface stops broadcasting
intelligence**. Instead, it surfaces:

- one current intent (in the user's language)
- at most three suggested actions
- a compact ledger pill
- a dock of modules that stay closed until invoked

Everything else — capacity meters, OS noise, gate verdicts, raw ledger tail —
moves to Advanced Mode behind progressive disclosure. The result is an
Apple-like, AI-native OS where the AI is *felt*, not *displayed*.

This document is a **design proposal only**. It does not implement, does not
ship, does not amend any constitutional contract. See §12 for what it is
**not**.

---

## §2. UX Principles

```
Voir moins.       See less.
Comprendre plus.  Understand more.
Agir plus vite.   Act faster.
```

Three operational consequences:

1. **Calm by default.** The main surface is sparse. Density is opt-in, never
   default. The OS does not shout.

2. **Intent-first.** The operator's current intent is the anchor. Every
   element on screen relates to that intent — or it does not appear.

3. **Suggestion, not decision.** HELEN proposes; the user confirms; the
   ledger remembers. HELEN never decides silently. The chain of
   `propose → confirm → receipt` is the only path through which the system
   acts.

4. **One focus at a time.** No module competes for attention. The active
   panel is the only panel. Dismiss it and the surface returns to calm.

5. **Progressive disclosure.** Detail appears when asked for, never before.
   Complexity lives behind one deliberate tap.

---

## §3. Main Screen Structure

A calm surface with five elements. Nothing else is permanently visible.

```
┌──────────────────────────────────────────────────────────┐
│   [status pill: kernel · ledger · safety]                │  top menu bar
│                                                          │  (status only)
│                                                          │
│              ◉  HELEN Intelligence Core                  │  embodied
│                                                          │  protagonist
│                                                          │  (canon §10)
│              Current intent:                             │
│              "<one line, human language>"                │
│                                                          │
│              ▸ Action 1                                  │  ≤ 3 actions
│              ▸ Action 2                                  │
│              ▸ Action 3                                  │
│                                                          │
│                                [⏚ ledger •••]            │  compact pill
│                                                          │
│  [ AMP ][ Files ][ Net ][ Notes ][ Cal ][ Mail ][ … ]    │  dock
└──────────────────────────────────────────────────────────┘
```

| Element | Contract |
|---|---|
| **HELEN core** | Embodied protagonist, calm, central. Never a generic AI hologram. (See §10 visual canon.) |
| **Top menu bar** | Status only — kernel up/down, ledger health, safety state. No actions, no noise. |
| **Current intent** | One sentence in the operator's language. The "what are we doing right now?" anchor. Always visible. Never collapses. |
| **Suggested actions** | **Maximum 3.** If there are more, the system has not yet understood the intent. More options = a UX failure, not a feature. |
| **Ledger pill** | Dot + event count. Tap → sheet with last N receipts. Never a wall. Color encodes chain health. |
| **Dock** | Module icons, closed by default. Tap to open as sheet, pop-in, or side panel. No module is permanent. |

### §3.1 What is not on the main screen

The following are **not** visible by default and do not appear unless
explicitly invoked:

- Capacity meters
- Raw ledger tail
- Gate verdicts (K8, K-tau, K-rho, K-wul)
- OS noise stream
- Worker lane status
- Mayor registry
- Schema audit results
- Any chart, graph, or telemetry panel

---

## §4. Hidden Modules by Default

```
AMP    Files    Internet    Notes    Calendar    Mail    Oracle    Settings
```

Each module appears only when invoked. Closing returns the system to calm.

| Module | Surface form | Opens as | Notes |
|---|---|---|---|
| **AMP** | Side panel (right) | Slide in | Operator resonance engine; `project_helen_amp.md` |
| **Files** | Sheet | Slide up | Browse, scope-locked to non-sovereign paths |
| **Internet** | Pop-in card | Fade in | Search / fetch; receipt-bound if mutating |
| **Notes** | Side panel (left) | Slide in | Capture surface; append-only |
| **Calendar** | Sheet | Slide up | Read-first; mutations confirmed via receipt sheet |
| **Mail** | Sheet | Slide up | Read-first; mutations confirmed via receipt sheet |
| **Oracle** | Pop-in card | Fade in | HELEN deep query; always returns to main |
| **Settings** | Sheet | Slide up | Advanced Mode lives here, hidden by default |

**No module is permanent.** No module sprawls. Each is dismissable with a
single gesture (`Esc`, swipe, or tap outside) and the surface returns
immediately to the main screen.

---

## §5. Interaction Flow

```
clic / commande / voix
  ↓
intent detected
  ↓
HELEN proposes (1–3 actions)
  ↓
operator confirms or dismisses
  ↓
if confirmed → receipt sheet → kernel route → ledger append
  ↓
retour au calme (main screen)
```

Every path terminates in **return to calm**. No path leaves the operator on a
wall of data, a chain of nested menus, or a celebratory animation that
overstays its welcome.

Voice, keyboard, and click inputs collapse to the same flow. The interaction
grammar is consistent across all input modalities.

### §5.1 Returning to calm

"Return to calm" is a first-class action, not a fallback. The main screen is
the resting state — always reachable, always coherent. The OS treats it the
way macOS treats the desktop: the ground you return to, never an error state.

---

## §6. Apple-like Behavior Rules

Ten rules. Ordered by priority.

1. **One focus at a time.** The main screen has one anchor: current intent.
   Open one module; the previous one collapses unless explicitly pinned.

2. **Progressive disclosure.** Detail appears when asked for, never before.
   The first view of anything should be the simplest possible version of it.

3. **No data walls.** Never show a table, chart, or stream by default. These
   surfaces live behind a deliberate tap.

4. **Confirm before mutating.** Every state change that touches the kernel
   requires an explicit confirmation. Silent mutations do not exist.

5. **Receipts are not trophies.** The receipt hash flashes briefly, then
   disappears. No success screen lingers. The system trusts the operator to
   know that confirmation happened.

6. **Calm returns automatically.** After any action completes, the surface
   returns to the main screen without requiring a "close" or "back" action
   from the operator.

7. **Three actions maximum.** If HELEN proposes more than three actions, it
   has not understood the intent. The constraint is intentional — it forces
   clarity of proposal.

8. **Status lives in the menu bar, nowhere else.** The top bar is the only
   place that broadcasts system health. Everything else is contextual.

9. **Hidden until needed.** Advanced Mode, capacity meters, OS noise — these
   surfaces exist for debugging and auditing. They are not the OS; they are
   tools within the OS.

10. **HELEN is presence, not performance.** She does not animate unnecessarily,
    does not narrate her own actions, does not ask for attention. She is felt
    when needed; she is invisible when not.

---

## §7. Ledger UX

The ledger is the constitutional spine — and on the main screen it is
**a single pill**.

```
[⏚ 4,712 ✓]      compact (default)
   ↓ tap
┌──────────────────────────────────┐
│ Last receipts                    │
│  • 17:42  helen.say   → #4712    │
│  • 17:41  hal.gate    → #4711    │
│  • 17:39  k_tau.lint  → #4710    │
│  …                               │
│        [ open full tail ]        │
└──────────────────────────────────┘
```

**Pill states:**

| Dot color | Meaning |
|---|---|
| Green | Chain valid, ledger healthy |
| Amber | Lag detected or pending event |
| Red | Integrity error — requires operator attention |

**"open full tail"** is the bridge to Advanced Mode (§9), where the raw
NDJSON tail, gate verdicts, and cumulative hash chain live.

The ledger **never blocks the main screen**. It is quiet by default,
expandable on demand. It is never silenced — the dot is always visible, always
honest about chain state.

---

## §8. Receipt Confirmation Sheet

When an action mutates state, a small confirmation sheet shows before anything
is routed to the kernel:

```
┌──────────────────────────────────────────────┐
│  HELEN proposes:                             │
│  <one sentence — what will happen>           │
│                                              │
│  ▾ Inputs (collapsed by default)             │
│  → kernel route: <op_type>                   │
│  → expected receipt: <RECEIPT_CLASS_V1>      │
│                                              │
│         [ Cancel ]      [ Confirm ]          │
└──────────────────────────────────────────────┘
```

**After Confirm:**
- the receipt hash flashes in the ledger pill for ~3 seconds
- the pill counter increments
- the surface returns to calm
- no toast, no celebration, no lingering modal

**After Cancel:**
- the sheet dismisses
- nothing is routed
- nothing is written to the ledger
- the surface returns to the main screen as if nothing happened

This sheet is the only path through which mutation enters the constitutional
spine from the UI. "No hidden mutation" (Rule 4, §6) is enforced here.

The "Inputs (collapsed)" section expands on demand — operator can inspect the
full payload before confirming. Collapsed by default; the summary sentence
should be sufficient for routine operations.

---

## §9. Advanced Mode

Hidden by default. Reached via `Settings → Advanced`. Never auto-opened.
Never shown to an operator who has not explicitly requested it.

Surfaces available in Advanced Mode (each as its own sheet, never
simultaneously forced):

- Raw ledger tail (NDJSON stream)
- Capacity meters (compute, memory, queue depth)
- OS noise stream (kernel events, gate runs)
- Gate verdicts (K8 / K-tau / K-rho / K-wul) — expandable per gate
- Worker lanes (`ops/runs/<run-id>/workers/...`)
- Mayor key registry status
- Schema audit results
- Ghost closure detector output

Advanced Mode is for **power users** — operator audits, MAYOR debugging,
K-gate diagnosis. Routine sessions never need it. Opening Advanced Mode does
not disable the calm layer; closing it returns to the main screen.

The surfaces it exposes are the same surfaces the operator dashboard contract
mandates be **available**. This proposal makes them **available on demand**
rather than always-on. This is the one open tension with the dashboard
contract — reconciliation candidates are listed in §12.

---

## §10. Visual Language

**Palette:**
- Base: dark graphite (`#0d1117` class)
- Accents: soft violet (`#a78bfa` class)
- Presence highlights: warm amber (`#f59e0b` class)
- Ledger health: green / amber / red for pill state only
- Reserved for NO_SHIP / threshold verdicts: red — not used decoratively

**Typography:**
- Large, readable, restrained
- One display weight (headers, intent line)
- One body weight (actions, metadata)
- No decorative fonts
- Negative space is intentional — do not fill it

**Structure:**
- Glass panels for sheets and pop-ins (translucent dark, slight blur)
- Subtle depth layering — main screen → sheet → modal, never more than 3
  levels deep
- Subtle sacred geometry as background texture (grid harmonics, barely
  visible, never decorative overlay)
- No skeuomorphism

**HELEN protagonist canon** (from `feedback_helen_protagonist_not_hologram.md`):
- Copper / red hair, blue-grey eyes, fair skin with freckles
- Black / gold sovereign-tech aesthetic
- Calm, still, present
- **Not** a generic blue AI hologram
- **Not** a robot or abstract icon
- **Not** an animation loop that runs without purpose
- Appears embodied and real — rarity is signature (she appears when relevant,
  not as permanent wallpaper)

**Forbidden:**
- Walls of charts or tables as default views
- Permanent telemetry overlays
- Blinking alerts on the main surface
- Celebration animations that linger
- Rotating / pulsing AI sphere as HELEN's representation
- Any visual that implies "the AI is always watching you"

---

## §11. Core Copy

Visible on the main screen, in priority order:

```
HELEN sees.
HELEN proposes.
You choose.
The ledger remembers.
```

UX canon phrase (preserved verbatim, never paraphrased):

> HELEN n'est pas un cockpit.
> HELEN est une présence calme qui ouvre le bon panneau au bon moment.

Core thesis (at the top of every spec derived from this proposal):

> HELEN OS should not show intelligence everywhere.
> It should make intelligence feel effortless.

---

## §12. Non-Goals

This proposal does **not**:

- Implement any window manager, route, or UI component
- Build a GUI prototype or mockup
- Modify the sovereign kernel, governance layer, schemas, ledger, closures,
  or tranche receipts
- Change any K-gate script or lint rule
- Touch any path under the sovereign-path firewall

It does **not** resolve the one open tension with the operator dashboard
contract (`feedback_operator_dashboard_contract.md`), which declares six
invariants including "capacity visible" and "OS noise exposed." This proposal
moves those surfaces to Advanced Mode on demand. Reconciliation candidates:

| Option | Description |
|---|---|
| **A** | Status-pill compromise — capacity + OS noise reduced to a single top-bar pill (green/amber/red); drill-down opt-in |
| **B** | Calm-mode toggle — calm and full-cockpit are both first-class surfaces, operator chooses |
| **C** | Amend the contract — accept that "visible" was wrong-resolution language; replace with "available on demand" |
| **D** | Reject this proposal — keep the dashboard contract as written; HELEN OS v2 stays cockpit-shaped |

**No option is selected by this file.** The operator chooses.

It also does **not**:
- Promote any candidate to canon
- Commit any change to git
- Push any change to a remote

---

## §13. Final Receipt

```
authority:             NON_SOVEREIGN
canon:                 DESIGN_CANON
lifecycle:             DOCTRINE
helen_status:          DOCTRINE
implementation_scope:  UX_DESIGN_DOC_ONLY
implementation_status: NOT_IMPLEMENTED
peer_review:           PASS 9/9 (session a7e1460ed050b535f, 2026-04-27)
promoted_on:           2026-04-27
promoted_by:           operator directive
commit_status:         COMMITTED
push_status:           NO_PUSH
reconciliation:        OPEN — §12 option (A/B/C/D) not yet selected by operator
next_verb:             select §12 reconciliation option (A/B/C/D)
                       OR begin implementation spec
```
