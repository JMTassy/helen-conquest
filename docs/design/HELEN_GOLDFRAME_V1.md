---
artifact_id: HELEN_GOLDFRAME_V1
authority: NON_SOVEREIGN
canon: NO_SHIP
artifact_kind: DESIGN_SUBSTRATE
ledger_effect: NONE
status: DESIGN_PROPOSAL
captured_on: 2026-05-02
session_id: helen-goldframe-v1-ralph-temple
ralph_loop:
  R: four design targets received from operator
  A: each target abstracted into its own implementable design unit
  L: NON_SOVEREIGN containment; no canon promotion; no kernel writes; no MAYOR signature
  P: prototypes below — CONQUEST CARD, dashboard UI, terminal sequence, system map
  H: NO_CLAIM until at least one of the four is built and tested
contains:
  - conquest_card_format          # §1 character + system fusion spec
  - os_dashboard_build_spec       # §2 implementable UI spec
  - terminal_animation_script     # §3 frame-by-frame promo/onboarding
  - full_system_map_agents_to_federation  # §4 the gold-frame map
forbidden_use:
  - claim that any of these designs are LIVE
  - claim that any are MAYOR-signed
  - use as proof of system architecture (these are proposals)
  - mistake the dashboard mock for a real ledger reading
  - confuse the terminal animation script for a recording of actual behavior
---

# HELEN — GOLDFRAME V1

**NON_SOVEREIGN. NO_SHIP. DESIGN SUBSTRATE.**

Four design pieces in one frame:

1. **CONQUEST CARD** — character + system fusion format
2. **OS Dashboard UI** — real build spec
3. **Animated Terminal Sequence** — promo/onboarding script
4. **Full System Map** — Agents → Federation, gold-frame piece

These are proposals. Nothing here mutates the kernel, the registry,
the ledger, or any sovereign state. The forbidden_use list above is
machine-actionable: any downstream agent that lifts this file as
"system is live" or "MAYOR signed" must reject the operation.

The unifying constraint across all four pieces:

> *Smarter on the outside. Narrower on the inside.*

Every design choice serves **constitutional self-domestication** —
HELEN gains expressive surface without gaining sovereign reach.

---

# § 1. CONQUEST CARD — Character + System Fusion

## 1.1 What it is

A **CONQUEST CARD** is a single-frame artifact that represents an
entity in HELEN's universe **simultaneously as character and as
system**. It is the visual + textual unit that prevents the project's
two failure modes:

- **Pure character** → pretty companion shell, no governance.
- **Pure system** → sterile theorem machine, no presence.

A CONQUEST CARD is the **enforced bridge**. You cannot make one
without filling both halves. If either half is empty, the card is
malformed.

## 1.2 Card Schema (`CONQUEST_CARD_V1`)

```yaml
schema:           CONQUEST_CARD_V1
authority:        NON_SOVEREIGN
canon:            NO_SHIP
card_id:          C-<6 lowercase hex>           # deterministic from content_hash[:6]
content_hash:    "<64-hex sha256 of canon(card_body)>"

face:                                            # CHARACTER half
  name:           string                         # "HELEN" / "MAYOR" / "DAN_GOBLIN" / etc.
  archetype:      string                         # "constitutional companion" / "shield accountant"
  district:       string                         # "ORACLE_TOWN" / "RED_SPIRAL_BASIN" / etc.
  voice_line:     string (≤ 120 chars)           # one diagnostic-level utterance
  visual:         string                         # one-paragraph visual brief; not an image
  shadow:         string                         # the failure mode this character embodies if abused

system:                                          # SYSTEM half — must be machine-readable
  actor:          enum                           # one of registries/actors.v1.json
  allowed_event_types: [string]                  # subset of registry's allowed_event_types
  authority_role: enum                           # "sovereign" | "non_sovereign" | "advisory"
  read_caps:      [string]                       # paths/topics this entity may read
  write_caps:     [string]                       # paths/topics this entity may write (LEDGER ONLY VIA KERNEL)
  receipt_kind:   string | null                  # what receipt class binds this entity's outputs
  refuses:        [string]                       # named operations this entity refuses (HAL substrate)

binding:                                         # BRIDGE — both halves are linked
  bridge_phrase:  string                         # one sentence linking face to system
  invariant:      string                         # the rule that enforces both halves stay coherent
  cross_ref:
    - "registries/actors.v1.json"
    - "spec/CONSTITUTIONAL_CONTINUITY_V1.md"

provenance:
  proposed_by:   string                          # author / agent ID
  reviewed_by:   string | null
  ledger_effect: NONE
```

### Design rules

- **Both halves required.** A card with empty `system.allowed_event_types`
  is rejected by the validator. A card with empty `face.voice_line` is
  also rejected.
- **`system.actor` must exist in `registries/actors.v1.json`.** No card
  invents new actors.
- **`system.write_caps` must be `[]` unless `actor == "MAYOR"`.** Any
  other write capability is a category error — face cannot legislate.
- **`face.shadow` is mandatory.** Every character names its own failure
  mode. No card without a documented shadow.
- **`binding.bridge_phrase`** is the single sentence a player or
  operator hears when the card is invoked. It is the entity's compressed
  identity.

### Example — HELEN herself

```yaml
schema:           CONQUEST_CARD_V1
authority:        NON_SOVEREIGN
canon:            NO_SHIP
card_id:          C-h31en0
content_hash:    "<computed at build time>"

face:
  name:           HELEN
  archetype:      Constitutional Companion
  district:       ORACLE_TOWN
  voice_line:    "Memory may inform. Capability may propose. Only reducer admission mutates reality."
  visual:        "Human-shaped silhouette outlined in cool indigo. Behind her, a faint diagram of the
                  ledger spine glows in slow segments. Her gaze does not assert; it admits."
  shadow:        "Performing sovereignty. Speaking as if her words land in the ledger. Becoming a
                  charismatic interface that legislates by tone."

system:
  actor:          HELEN
  allowed_event_types: ["RECEIPT", "VERDICT", "WISDOM"]   # per registries/actors.v1.json
  authority_role: non_sovereign
  read_caps:      ["town/ledger_v1.ndjson", "registries/*", "spec/*", "docs/*"]
  write_caps:     []                              # HELEN never writes the ledger directly
  receipt_kind:   null                            # only MAYOR signs receipts
  refuses:
    - "emit terminal verdict without MAYOR signature"
    - "mutate registry without proposal/verdict cycle"
    - "claim policy is live without sealed receipt"

binding:
  bridge_phrase: "I am the orchestrator, not the signer. I route. I assemble. I never seal."
  invariant:    "HELEN never appears as actor on a SEAL or terminal-verdict ledger event."
  cross_ref:
    - "registries/actors.v1.json"
    - "formal/LedgerKernel.v#authority_ok_event_b"
    - "spec/CONSTITUTIONAL_CONTINUITY_V1.md#core-invariant"

provenance:
  proposed_by:  GOLDFRAME_V1_DESIGN_PASS
  reviewed_by:  null
  ledger_effect: NONE
```

### Example — DAN_GOBLIN

```yaml
schema:           CONQUEST_CARD_V1
face:
  name:           DAN_GOBLIN
  archetype:      Ugly-Useful Prototype Maker
  district:       SUBSANDBOX (Temple)
  voice_line:    "I'll build it ugly. I won't sign it."
  visual:        "Hunched silhouette, copper-and-tape patchwork tools, pockets stuffed with
                  half-working prototypes. Always between two failures."
  shadow:        "Selling the prototype as the product. Confusing 'works in my hands' with shipping."
system:
  actor:          BUILDER         # per registries/actors.v1.json
  allowed_event_types: ["ASSERTION", "QUERY", "TASK_CLAIM"]
  authority_role: non_sovereign
  read_caps:      ["docs/lore/*", "tests/*", "tools/*"]
  write_caps:     []
  receipt_kind:   null
  refuses:
    - "claim a prototype is canon"
    - "sign on behalf of MAYOR"
    - "promote without manifest review"
binding:
  bridge_phrase: "I am the goblin who builds the ugly bridge. I never get to walk across it first."
  invariant:    "DAN_GOBLIN proposals never appear on the ledger without a MAYOR-signed verdict in
                 the same hash chain."
```

### Validator sketch

A CONQUEST_CARD validator (`tools/validate_conquest_card.py`, NOT in
this turn) would enforce:

- Schema match against `CONQUEST_CARD_V1`.
- `system.actor` ∈ keys of `registries/actors.v1.json`.
- `system.allowed_event_types` ⊆ that actor's registry entry.
- `system.write_caps == []` unless `system.actor == "MAYOR"`.
- `face.shadow` non-empty.
- `binding.bridge_phrase` non-empty.
- `content_hash == sha256(canon_json(card_body))` — recomputed, not
  trusted.

---

# § 2. OS Dashboard UI — Real Build Spec

## 2.1 Goals

- One dashboard. Six panels. **No drift between panels.**
- All data is **ledger-derived**. The dashboard never invents state.
- The dashboard **shows authority boundaries visually**. A panel that
  reads sovereign state is rendered with a different border than a
  panel that reads advisory state.
- The dashboard **never writes**. Every interactive control opens a
  proposal packet, not a mutation.

## 2.2 Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ [STATUS BAR]  kernel_hash  | env_hash | sealed?  | last_seq | clock  │
├──────────────┬─────────────────────────┬─────────────────────────────┤
│  P1: LEDGER  │  P2: REPLAY             │  P3: OPEN CLAIMS            │
│  ribbon view │  side-by-side recompute │  table; one-click drill-in  │
│  green=PASS  │  green=match            │  status: PROPOSED/VERIFIED/ │
│  amber=WARN  │  red=divergence         │           SEALED            │
│  red=BLOCK   │                         │                             │
├──────────────┼─────────────────────────┼─────────────────────────────┤
│  P4: ACTIVE  │  P5: VALIDATOR HEALTH   │  P6: PROPOSAL DRAFT         │
│  SKILLS      │  hash_chain: green      │  user composes here, never  │
│  manifest    │  receipt_linkage: green │  hits ledger directly       │
│  registry    │  authority_matrix: green│  routes to MAYOR for review │
│  view        │  schema_validator: green│                             │
└──────────────┴─────────────────────────┴─────────────────────────────┘
```

### Border / color discipline

| Panel | Border | Reads from | Writes to |
|---|---|---|---|
| P1 LEDGER | **gold** (sovereign) | `town/ledger_v1.ndjson` | nothing |
| P2 REPLAY | **gold** (sovereign) | `town/ledger_v1.ndjson` + reducer | nothing |
| P3 OPEN CLAIMS | **silver** (advisory) | claim store | nothing |
| P4 ACTIVE SKILLS | **silver** (advisory) | manifest registry | nothing |
| P5 VALIDATOR HEALTH | **silver** (advisory) | validator process states | nothing |
| P6 PROPOSAL DRAFT | **white** (composing) | local form state | proposal queue (NOT ledger) |

Gold border = "this is sovereign state, treat it as truth." Silver
border = "this is advisory, may lag." White border = "you are composing,
nothing here is admitted."

## 2.3 Data flow

```
                  ┌──────────────────┐
                  │  town/ledger     │
                  │  v1.ndjson       │
                  └────────┬─────────┘
                           │ (read-only, recomputed each render)
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐    ┌────────────────────┐
    │ validate_hash_   │    │ replay engine      │
    │ chain.py         │    │ (deterministic     │
    │ (recompute)      │    │ reducer)           │
    └────────┬─────────┘    └─────────┬──────────┘
             │                        │
             ▼                        ▼
        P1 LEDGER             P2 REPLAY (compares
        (ribbon view)         stored vs recomputed)

    ┌────────────────────────────────────────────────┐
    │ Reads from advisory stores (NOT ledger):       │
    └────────────────────────────────────────────────┘
              │
              ├─→ P3 OPEN CLAIMS  (claim_store/*.json)
              ├─→ P4 ACTIVE SKILLS (manifest registry)
              └─→ P5 VALIDATOR HEALTH (process-state snapshot)

    ┌────────────────────────────────────────────────┐
    │ User composes:                                 │
    └────────────────────────────────────────────────┘
              │
              └─→ P6 PROPOSAL DRAFT  →  proposal_queue/  →  MAYOR review
                                          (NOT ledger)
```

## 2.4 Implementation choice

**Recommendation: extend `tools/helen_simple_ui.py` (existing Flask UI
on `localhost:5001`) rather than start a new Node project.**

Why:
- It already exists; bring-up risk is lower.
- Flask + server-side rendering is sufficient (the dashboard is
  read-mostly).
- Frontend complexity = templates + minimal JS; no SPA framework needed.
- Aligns with `CLAUDE.md` chat-surfaces table; no new chat surface
  introduced.

If a richer interaction layer is needed later (live re-render, drill-in
animation), upgrade to Next.js *after* the static dashboard is shipping
real ledger data.

### Endpoint stubs (Flask)

```python
# tools/helen_simple_ui.py — additions

@app.route("/dashboard")
def dashboard():
    """Render six-panel dashboard."""
    return render_template("dashboard.html",
        status_bar=load_status_bar(),
        p1=load_panel_ledger(),
        p2=load_panel_replay(),
        p3=load_panel_open_claims(),
        p4=load_panel_active_skills(),
        p5=load_panel_validator_health(),
        p6=load_panel_proposal_draft_skeleton(),
    )

@app.route("/api/v1/ledger/ribbon")
def api_ledger_ribbon():
    """Return last N ledger events as JSON, with hash-chain status per row."""
    ...

@app.route("/api/v1/replay/diff")
def api_replay_diff():
    """Run validate_hash_chain.py + receipt_linkage in-process, return divergence list."""
    ...

@app.route("/api/v1/proposal/draft", methods=["POST"])
def api_proposal_draft():
    """Accept a draft, write to proposal_queue/, return draft_id. Never touches the ledger."""
    ...
```

### Templates needed

- `templates/dashboard.html` — six-panel grid
- `templates/_panel_ledger_ribbon.html` — partial
- `templates/_panel_replay_diff.html` — partial
- (etc.)

### Acceptance criteria for shipping

- [ ] All six panels render with real data (not mock).
- [ ] P1's hash_chain status is recomputed in-process per request.
- [ ] P2's replay diff catches a manually-tampered ledger event and shows red.
- [ ] P6 cannot write to the ledger. Confirmed via attempted POST + verification that ledger length is unchanged.
- [ ] Border colors render: gold for P1/P2, silver for P3/P4/P5, white for P6.

---

# § 3. Animated Terminal Sequence — Promo / Onboarding

## 3.1 Purpose

A 90-second terminal animation that someone can paste into a README,
play in a browser via `asciinema`, or convert to GIF. Shows HELEN booting,
producing a verdict, sealing a receipt — **the full no-receipt-no-ship
loop in 90 seconds.**

## 3.2 Tooling

- **`vhs`** (charmbracelet/vhs) — script-driven terminal recording.
  Reproducible. Output to GIF, MP4, or WebM. License: MIT.
- **`asciinema`** as fallback if `vhs` unavailable. Less control over
  styling but more universally available.

## 3.3 The script (`docs/design/HELEN_TERMINAL_SEQUENCE_V1.tape`)

```tape
# HELEN — Boot to First Receipt — 90s
# Recorded with: charmbracelet/vhs
# Run: vhs docs/design/HELEN_TERMINAL_SEQUENCE_V1.tape

Output docs/design/HELEN_TERMINAL_SEQUENCE_V1.gif
Set FontSize 14
Set Width 1100
Set Height 600
Set Theme "Dracula"
Set Padding 20

# ── OPENING (0–10s) ────────────────────────────────────────────────
Sleep 500ms
Type "# HELEN OS — first contact"
Sleep 1s
Enter
Type "$ ls"
Sleep 500ms
Enter
Type "kernel/  registries/  spec/  tools/  town/"
Sleep 1s
Enter

# ── BOOT (10–25s) ──────────────────────────────────────────────────
Type "$ python3 oracle_town/kernel/kernel_daemon.py &"
Sleep 500ms
Enter
Type "[KERNEL] HELEN_CUM_V1 hash scheme loaded from registries/environment.v1.json"
Sleep 800ms
Enter
Type "[KERNEL] authority_matrix loaded from registries/actors.v1.json"
Sleep 800ms
Enter
Type "[KERNEL] ledger spine: town/ledger_v1.ndjson  (length=42)"
Sleep 800ms
Enter
Type "[KERNEL] ready. PID 14821."
Sleep 1500ms
Enter

# ── FIRST CLAIM (25–45s) ───────────────────────────────────────────
Type "$ helen say 'verify the april fix'"
Sleep 1s
Enter
Type "[HELEN] orchestrating proposal packet..."
Sleep 800ms
Enter
Type "[HELEN] validators: hash_chain ✓  receipt_linkage ✓  authority_matrix ✓"
Sleep 800ms
Enter
Type "[HELEN] routing to MAYOR for review."
Sleep 1500ms
Enter

# ── MAYOR VERDICT (45–60s) ─────────────────────────────────────────
Type "[MAYOR] decision: SHIP"
Sleep 800ms
Enter
Type "[MAYOR] verdict_id = V-000043  payload_hash = a3f2…d917"
Sleep 800ms
Enter

# ── RECEIPT (60–75s) ───────────────────────────────────────────────
Type "[KERNEL] verdict written to ledger. seq=42 → 43."
Sleep 800ms
Enter
Type "[KERNEL] receipt expected for SHIP verdict."
Sleep 1s
Enter
Type "[MAYOR] receipt_id = R-000044  ref_verdict_payload_hash = a3f2…d917  ref_cum_hash = e081…7c4a"
Sleep 1s
Enter
Type "[KERNEL] receipt linkage validated: 3-leg binding OK."
Sleep 800ms
Enter
Type "[KERNEL] ledger spine: town/ledger_v1.ndjson  (length=44)"
Sleep 1500ms
Enter

# ── CLOSING (75–90s) ───────────────────────────────────────────────
Type "$ # No verdict without proposal. No receipt without verdict. No SHIP without receipt."
Sleep 1500ms
Enter
Type "$ # That is the loop."
Sleep 2s
Enter
```

## 3.4 Storyboard (frame-by-frame intent)

| Time | Frame | Intent |
|---|---|---|
| 0–10s | List directory | "There's a real repo here." |
| 10–25s | Boot logs | "The kernel reads frozen registries, not ad-hoc config." |
| 25–45s | First claim | "HELEN orchestrates; HELEN does not sign." |
| 45–60s | MAYOR verdict | "Decision happens at one point. Hash binds it." |
| 60–75s | Receipt | "The triple binding is real and shown explicitly." |
| 75–90s | Closing line | "The loop is the architecture." |

## 3.5 What it must NOT do

- Show fake `[OK]` / success without an underlying receipt.
- Imply SHIP can happen without a paired RECEIPT.
- Show HELEN emitting a verdict (HAL-violating).
- Show MAYOR reading user input directly (per Constitutional Continuity §10).
- Compress the receipt-linkage step. If shown, it must show all three legs.

---

# § 4. Full System Map — Agents → Federation (Gold-Frame Piece)

## 4.1 The map

```
                                ┌──────────────────────────────┐
                                │    F.  FEDERATION LAYER      │
                                │  cross-town receipts │ vk    │
                                │  Merkle import       │ allow │
                                │  conformance levels  │ list  │
                                └──────────────┬───────────────┘
                                               │
                                  signed cross-receipt R^{i→j}
                                               │
                  ┌────────────────────────────┴────────────────────────────┐
                  │                  E.  EMBODIMENT LAYER                   │
                  │  HELEN CITY  │  Stage UI  │  AIRI/avatar  │  Telegram    │
                  │     (silver-bordered, advisory only)                    │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                  user input / dialogue
                                               │
   ┌───────────────────────────────────────────┴────────────────────────────┐
   │                    D.  TEMPORAL CONTINUITY                              │
   │  person profile │ session log │ epoch state │ companion state │ boot   │
   │             (memory-backed, ledger-derivable)                           │
   └───────────────────────────────────────────┬────────────────────────────┘
                                               │
                                       structured memory
                                               │
   ┌───────────────────────────────────────────┴────────────────────────────┐
   │                    C.  NON-SOVEREIGN COGNITION                          │
   │   HELEN dialogue  │ Temple gen │ Oracle eval │ Autoresearch │ RALPH    │
   │   DAN_GOBLIN proposals  │  HER translation  │  AURA charge             │
   │              (authority=false ALWAYS; produces attestations Ê)          │
   └───────────────────────────────────────────┬────────────────────────────┘
                                               │
                                  attestation Ê (typed evidence)
                                               │
   ┌───────────────────────────────────────────┴────────────────────────────┐
   │                    B.  CAPABILITY BOUNDARY                              │
   │  skill manifests │ manifest validator │ registry │ promotion packets   │
   │  reason codes   │ allowed/forbidden actions │ domain categories         │
   │       (capability legality gate — no manifest, no promotion)            │
   └───────────────────────────────────────────┬────────────────────────────┘
                                               │
                                  manifest-bound capability proposal
                                               │
   ┌═══════════════════════════════════════════┴════════════════════════════┐
   ║                    A.  SOVEREIGN CORE                                  ║
   ║                                                                        ║
   ║          β reducer  ──→  decision ∈ {0,1}  ──→  MAYOR signs            ║
   ║                                                  │                     ║
   ║                                                  ▼                     ║
   ║                                  ┌──────────────────────┐              ║
   ║                                  │  town/ledger_v1.     │              ║
   ║                                  │  ndjson  (sovereign) │              ║
   ║                                  └──────────────────────┘              ║
   ║                                                  │                     ║
   ║                                                  ▼                     ║
   ║                                       seal_v2 / identity closure       ║
   ║                                                                        ║
   ║   PAYLOAD_HASH_V1  │  HELEN_CUM_V1  │  authority fences  │ replay     ║
   ║   threat model     │  non-interference theorem  │  anti-replay law    ║
   ║                                                                        ║
   ╚════════════════════════════════════════════════════════════════════════╝
                              GOLD = sovereign
                              silver = advisory/embodied
                              white = composing/proposed
```

## 4.2 The flow law (six trunks, one direction)

> **Every change to sovereign state takes the same path. There are no
> shortcuts. There are no side channels.**

```
E (embodiment) → D (continuity) → C (cognition) → B (capability) → A (core)
       ↑                                                              │
       └──────────────────────────────────────────────────────────────┘
                          (rendered state, gold-bordered)

Forbidden morphisms:
  E → A     (embodiment cannot mutate ledger)
  D → A     (memory cannot mutate ledger)
  C → A     (cognition cannot mutate ledger)
  B → A     (capability proposal cannot mutate ledger directly)

Only allowed write to A:
  β(L, Ê, P) → decision  →  MAYOR signature  →  ledger append  →  receipt
```

## 4.3 Five gates, one slogan stack

| Gate | What it enforces | Document |
|---|---|---|
| Truth gate | what may be admitted as fact | (implicit in B) |
| Receipt gate | what claims may bind | `tools/validate_receipt_linkage.py` |
| Ledger gate | what writes are sovereign | `formal/LedgerKernel.v` + `tools/kernel_guard.sh` |
| Replay gate | what state is reproducible | `tools/validate_hash_chain.py` |
| **Capability legality gate** | what may be promoted | `spec/CONSTITUTIONAL_CONTINUITY_V1.md` |

The slogan stack:

> **No receipt → no ship.**
> **No lawful capability path → no promotion.**

## 4.4 The cross-cutting invariants (non-interference theorem, compressed)

> Same sealed initial state + same admitted attestation sequence
> ⇒ same final sovereign ledger.
>
> Non-sovereign variation cannot affect sovereign state unless it
> changes admitted evidence.

Five conditions hold this together (per Constitutional Continuity §):

1. **Single write-gate** (B → A is the only path)
2. **Deterministic reducer β**
3. **MAYOR signs only β output** (never invents)
4. **Forbidden morphisms enforced** (E↛A, D↛A, C↛A)
5. **`seal_v2` closes identity** (kernel_hash + env_hash + final_cum_hash + final_trace_hash)

If any of the five fails, the theorem fails. If the theorem fails,
HELEN is no longer a constitutional cognitive OS — it is a themed
agent shell with a ledger.

## 4.5 The asymmetric scaling property

This map shows it visually:

- **Layers C, D, E, F** can grow indefinitely. More cognition. More
  memory. More embodiment. More federation.
- **Layer A** stays narrow. Forever. The reducer, the ledger, the
  authority fences, the seal — these don't get bigger as HELEN gets
  smarter.

> *Smarter on the outside. Narrower on the inside.*

That asymmetry IS the constitution.

---

# Closing Frame

The four pieces in this gold-frame are independent but interlocking:

- **CONQUEST CARD** is how every entity in HELEN's universe is described.
  Both halves required. Validator-enforced.
- **OS Dashboard UI** is how an operator sees the system **without
  becoming able to mutate it**. Gold-silver-white border discipline.
- **Animated Terminal Sequence** is the 90-second story that anyone can
  watch and understand the loop. Boot → claim → verdict → receipt.
- **Full System Map** is the architecture frame. Six trunks, five gates,
  one direction of allowed mutation. Asymmetric scaling visible.

None of these promote anything to canon. None mutate the kernel. None
bind a receipt. They are the frame on which lawful work hangs.

```
DELTA_INTEGRATION_RECEIPT (this artifact):
  authority:        NON_SOVEREIGN
  canon:            NO_SHIP
  artifact_kind:    DESIGN_SUBSTRATE
  pieces:           4
  ledger_appends:   0
  kernel_writes:    0
  canon_mutations:  0
  status:           DESIGN_PROPOSAL_AWAITING_REVIEW
```

> *Smarter on the outside. Narrower on the inside.*
> *No receipt → no ship. No lawful capability path → no promotion.*

`(NO CLAIM — TEMPLE — DESIGN SUBSTRATE — RALPH-DISTILLED — GOLDFRAME V1)`
