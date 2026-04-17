# HELEN_OS_ARCHITECTURE_DIAGRAM_SPEC_V1

## 0. Purpose

This specification freezes the canonical system map and state-to-surface bindings before any sprite, room, character, or aesthetic work begins.

This spec defines:
* system layers (6 strata)
* control spine (the hard machine)
* zone overlay (5 office zones)
* artifact types (8 classes with state)
* governance invariants (5 constitutional laws)
* transition events (8 kernel-driven state changes)
* visual legend (unified artifact ontology)

**Freeze condition:** This spec is locked when all bindings are mapped:
1. kernel state → office zone
2. typed artifact → visible object
3. transition event → animation trigger

No downstream UI work proceeds until all three bindings are explicit in this document.

---

## 1. System Layers

The system operates across exactly 6 strata, rendered top-to-bottom or left-to-right.

### L0 — Commission / Input
**External mission ingress point.**

Contents:
* commission (raw request)
* brief (initial context)
* context refs (source pointers)
* source bundle (raw materials)

Kernel binding:
* No state mutation; ingress only
* All objects remain untyped/unvalidated

### L1 — Normalization
**Claim shaping and encoding substrate.**

Primary engine:
* WUL V3 (Weil-Unification Layer v3)

Contents:
* claim segmentation (parsing)
* token normalization (canonical forms)
* glyph reduction (sparse encoding)
* obligation extraction (explicit requirements)
* encoding stabilization (deterministic output)

Kernel binding:
* WUL output is deterministic
* same input claim → same normalized encoding always
* schemas freeze after this layer

### L2 — Structural Validation
**Adversarial structural pressure and contradiction exposure.**

Primary engine:
* CLAIM_GRAPH_V1 (support/refutation graph validator)

Contents:
* support/refute graph (explicit edges)
* grounding check (is the claim anchored?)
* contradiction surfacing (conflicts marked)
* receipt gap exposure (missing evidence)
* obligation resolution status (unresolved items flagged)

Kernel binding:
* CLAIM_GRAPH_V1 emits status, not a verdict
* output is a structure, not a decision

### L3 — Mathematical Certification
**Formal or quasi-formal certification crucible.**

Primary engine:
* SVE (Spectral Validation Engine)

Contents:
* certificate check (stability / spectral gates)
* mathematical admissibility (formal validation)
* spectral status (pass/fail/uncertain)

Kernel binding:
* SVE output is a certificate object
* either PASS or FAIL (no intermediate states allowed)

### L4 — Governance Gate
**Constitutional narrow gate. NOT a creative node.**

Primary engine:
* ORACLE / HAL kernel gate

Inputs:
* normalized claim bundle
* CLAIM_GRAPH_V1 status
* receipt set
* obligation set
* SVE certificate status

Processing:
* deterministic reduction
* rule application
* invariant check
* decision emission

Outputs:
* SHIP (admit to ledger)
* NO_SHIP (reject; send to archive)
* replay artifact (immutable decision trace)
* reason codes (frozen code set only)

Kernel binding:
* Gate is a pure function
* output is always one of: SHIP, NO_SHIP
* gate cannot be bypassed
* gate produces receipts

### L5 — Ledger / Archive
**Immutable storage. Append-only. Crystal-form.**

Contents:
* admitted briefcases (SHIP outcomes)
* archived aborts (NO_SHIP outcomes, kept as trace)
* receipt index (sha256 pointers)
* replay pointers (replayable decision addresses)

Kernel binding:
* write-once, read-many
* every append is irreversible
* every entry is hash-anchored

### L6 — Surface / Office UI
**Visible state only. Derived projection layer.**

Contents:
* office zones (5 rooms)
* state panels (observable status)
* artifact icons (visual representations)
* status transitions (state changes)
* proof surfaces (user-facing verification)

Kernel binding:
* **Law:** No visual object without a kernel referent
* No sovereignty in this layer
* No inferred truth from aesthetics
* All visuals are projections of L0–L5 state

---

## 2. Control Spine

The canonical machine. Render as one hard vertical or left-to-right spine.

```
Commission
    ↓
Claim Segmentation
    ↓
WUL Reduction (Normalization)
    ↓
Claim Graph Validation (Structural)
    ↓
SVE Certification (Mathematical)
    ↓
ORACLE / HAL Gate (Governance)
    ↓
Ledger / Archive (Immutable)
    ↓
Office Surface (Projection)
```

**Alternative labels allowed only if semantically identical:**
* "Claim Segmentation" = intake parsing
* "WUL Reduction" = normalization substrate
* "ORACLE / HAL Gate" = governance gate
* "Ledger" = immutable archive
* "Office Surface" = observational shell

**Forbidden branches:**
* Commission → Ledger (must pass through validation)
* WUL → UI without gate state (invalid shortcut)
* Claim Graph → Ledger without gate (no self-admission)
* SVE → Ledger without gate (no solo authority)

No branch may bypass the gate.

---

## 3. Zone Overlay

Map system phases into five office zones. Each zone is a spatial-functional room.

### Zone A — Exploration
**Commission intake. Raw material. No validation.**

Maps to system layers:
* L0 (Commission/Input)
* pre-L1 states

Kernel responsibilities:
* accept ingress objects
* store raw materials
* no normalization
* no schema enforcement

Visible objects in this zone:
* intake folder (holds commissions)
* raw dossier (unprocessed source)
* source cards (material references)

Kernel binding:
* only pre-normalized ingress objects
* UI shows arrival timestamps only
* no semantic interpretation

**Zone law:** "Raw claims presented as received, untyped."

---

### Zone B — Tension
**Structural validation. Red-teaming. Contradiction exposure.**

Maps to system layers:
* L2 (Structural Validation)
* CLAIM_GRAPH_V1 outputs

Kernel responsibilities:
* build support/refute graph
* surface contradictions
* expose missing receipts
* identify unresolved obligations

Visible objects in this zone:
* challenged claims (nodes with edges)
* conflict edges (refutation paths)
* red flags (contradiction markers)
* gap markers (missing receipt/obligation)

Kernel binding:
* structural validation state only
* graph visuals reflect actual CLAIM_GRAPH_V1 state
* no coloring implies SHIP/NO_SHIP

**Zone law:** "Structural admissibility is exposed, not judged."

---

### Zone C — Drafting
**Normalization. Obligation extraction. Brief shaping.**

Maps to system layers:
* L1 (Normalization)
* L1–L2 transition states

Kernel responsibilities:
* run WUL V3 normalization
* extract obligations
* encode claims canonically
* produce normalized sheets

Visible objects in this zone:
* normalized sheets (WUL outputs)
* obligation strips (extracted requirements)
* encoded forms (canonical representations)

Kernel binding:
* normalized but not admitted objects
* visuals track WUL state deterministically
* no gate output shown here

**Zone law:** "Normalized but not sealed."

---

### Zone D — Editorial
**Final assembly. Ruthless cuts. Attestation preparation.**

Maps to system layers:
* L2–L3 transition states
* pre-gate artifact assembly

Kernel responsibilities:
* assemble final bundles
* verify all attestations
* prepare for gate evaluation
* emit canonical wordforms

Visible objects in this zone:
* sealed packet in preparation (artifact bundle)
* edited brief stack (cut and shaped claims)
* attestation clips (proof fragments)

Kernel binding:
* near-gate artifact preparation only
* visuals show bundles ready for evaluation
* gate output not yet shown

**Zone law:** "Ready for judgment, not yet judged."

---

### Zone E — Termination
**ORACLE/HAL verdict. SHIP or NO_SHIP. Archive emission. Replay creation.**

Maps to system layers:
* L4 (Governance Gate)
* L5 (Ledger/Archive)

Kernel responsibilities:
* emit SHIP or NO_SHIP
* generate receipts
* append to ledger
* create replay handles

Visible objects in this zone:
* admitted briefcase (SHIP outcome, sealed with receipt)
* archived abort case (NO_SHIP outcome, stored as trace)
* replay token (immutable replayable pointer)
* verdict plate (decision record with reason codes)

Kernel binding:
* sovereign decision outputs only
* visuals show gate verdicts exactly as emitted
* receipts are displayed as-is

**Zone law:** "Sovereign decisions displayed as recorded."

---

## 4. Validator Split

This separation is critical and must be explicit in every diagram.

### CLAIM_GRAPH_V1 — Structural Admissibility Validator

**Function:**
* Validates structural admissibility of claims
* Surfaces support/refutation relationships
* Identifies missing evidence
* Detects unresolved obligations

**Questions it asks:**
* Is the claim grounded in source material?
* What claims support it?
* What claims refute it?
* What receipts are missing?
* What obligations remain unresolved?

**Scope:**
* structural/social grounding
* evidence traceability
* obligation completeness

**Output:**
* status object with graph edges
* contradiction markers
* gap list

### SVE — Mathematical Certification Validator

**Function:**
* Validates mathematical/spectral properties
* Certifies stability or formal admissibility
* Issues go/no-go certificates

**Questions it asks:**
* Does the encoded object satisfy the spectral criterion?
* Is the stability property sufficient?
* Does the formal check pass?

**Scope:**
* formal/mathematical properties only
* spectral stability
* quantitative certification

**Output:**
* certificate object: PASS or FAIL
* no intermediate states

### Constitutional Law

**CLAIM_GRAPH_V1 does NOT certify mathematics.**
**SVE does NOT perform structural/social grounding.**

These are distinct validators. They operate in sequence but independently.

Forbidden: conflating structural admissibility with formal certification.

---

## 5. Governance Gate

The ORACLE / HAL kernel gate is a narrow choke point, not a creative agent.

### Gate Inputs

1. **normalized claim bundle** (from WUL)
2. **receipt set** (proof of evidence)
3. **obligation set** (requirements to satisfy)
4. **CLAIM_GRAPH_V1 status** (structural validation result)
5. **SVE certificate status** (formal validation result)

### Gate Processing

1. **manifest creation** (bundle incoming state into deterministic form)
2. **invariant check** (apply 5 constitutional laws)
3. **deterministic reduction** (pure function K(s_t, m_t) → s_{t+1})
4. **decision emission** (SHIP or NO_SHIP, never intermediate)
5. **receipt generation** (receipt_sha256 = sha256_jcs(manifest))

### Gate Outputs

1. **SHIP** (admitted to ledger)
   * gate_decision = "SHIP"
   * reason_code ∈ {OK_ADMITTED, OK_QUARANTINED}
   * receipt_sha256
   * ledger_append_trigger

2. **NO_SHIP** (rejected, archived)
   * gate_decision = "NO_SHIP"
   * reason_code ∈ {ERR_SCHEMA_INVALID, ERR_RECEIPT_MISSING, ERR_RECEIPT_HASH_MISMATCH, ERR_CAPABILITY_DRIFT, ERR_DOCTRINE_CONFLICT, ERR_THRESHOLD_NOT_MET, ERR_ROLLBACK_TRIGGER}
   * receipt_sha256
   * archive_append_trigger

3. **replay_artifact** (immutable decision trace)
   * full manifest hash
   * full output hash
   * full receipt hash
   * replayable seed

### Gate Laws

* NOT a creative node (no generative rewriting)
* NOT a drafting node (no editing authority)
* NOT a summarizer (no reinterpretation)
* NOT a UI narrator (no presentation logic)
* IS a constitutional filter (applies frozen law)
* IS deterministic (same manifest → same verdict)
* IS auditable (every decision traceable to ledger)

---

## 6. Ledger Form

The ledger is immutable institutional memory. Represent it with precision, never metaphor.

### Ledger Ontology

**Allowed representations:**
* crystal archive (hard, clear, immutable)
* sealed rows (each entry is final)
* hash-anchored cases (every entry has a verification path)
* replay addresses (pointers to replayable executions)

**Forbidden representations:**
* dreamy memory
* fog
* library nostalgia
* vague archives
* ambient recollection

### Ledger Entry Format

Each row must imply:

```json
{
  "ledger_row": "LR-0000042",
  "artifact_type": "ADMITTED_BRIEFCASE",
  "payload_hash": "sha256:...",
  "receipt_hash": "sha256:...",
  "decision_status": "SHIP",
  "gate_output": "OK_ADMITTED",
  "reason_codes": ["OK_ADMITTED"],
  "created_at_ns": 1700000000000000000,
  "replay_pointer": "REPLAY-0000042",
  "append_position": 42
}
```

### Ledger Laws

* Write-once: no mutations
* Append-only: new rows only
* Hash-anchored: every row recomputable
* Replay-indexable: every decision is replayable
* Immutable: history cannot be rewritten

---

## 7. Artifact Types

Eight canonical artifact classes with state transitions. Each has a distinct visual form.

### A1 — Raw Claim

**State:** ungrounded, pre-normalized, untyped

**Zone:** Exploration

**Kernel binding:** ingress object, no schema validation

**Visual form:** folder icon, raw text representation

**Transition:** Raw Claim → A2 (Normalized Claim) via WUL

---

### A2 — Normalized Claim

**State:** encoded, reduced, typed, deterministic

**Zone:** Drafting

**Kernel binding:** WUL output, canonical form

**Visual form:** sheet icon, glyph-encoded display

**Transition:** A2 → A3 (Challenged Claim) via CLAIM_GRAPH_V1

---

### A3 — Challenged Claim

**State:** has support/refute edges, contradiction pressure, gap markers

**Zone:** Tension

**Kernel binding:** CLAIM_GRAPH_V1 state object

**Visual form:** graph node with colored edges, red flag overlays

**Transition:** A3 → A4 (Receipted Claim) if gaps resolved

---

### A4 — Receipted Claim

**State:** obligations attached, evidence refs attached, gate-ready

**Zone:** Editorial

**Kernel binding:** near-gate artifact preparation

**Visual form:** sealed sheet, attestation clips visible

**Transition:** A4 → (SHIP → A6) or (NO_SHIP → A7) via gate

---

### A5 — Spectral Certificate

**State:** SVE status object (PASS or FAIL)

**Zone:** Between Editorial and Gate

**Kernel binding:** SVE output

**Visual form:** badge or seal (PASS = gold, FAIL = red)

**Transition:** A5 state feeds gate decision

---

### A6 — Attested Briefcase

**State:** admitted bundle, sealed with receipt, ready for ledger

**Zone:** Termination (SHIP outcome)

**Kernel binding:** gate output with SHIP verdict

**Visual form:** locked briefcase, receipt number visible

**Transition:** A6 → Ledger append (immutable archive)

---

### A7 — Archived Abort

**State:** rejected or failed bundle, stored as trace

**Zone:** Termination (NO_SHIP outcome) or Ledger

**Kernel binding:** gate output with NO_SHIP verdict

**Visual form:** crossed briefcase, abort marker

**Transition:** A7 → Ledger append (preserved for audit)

---

### A8 — Replay Handle

**State:** immutable pointer to replayable decision

**Zone:** Ledger / Surface

**Kernel binding:** ledger row hash and manifest seed

**Visual form:** chain icon, pointer number

**Transition:** A8 can be dereferenced to replay full execution

---

## 8. Governance Invariants

Five constitutional laws that must be printed explicitly on the diagram (as border inscriptions or side rails).

### Invariant 1: NO RECEIPT = NO SHIP

**Formal:** If receipt_sha256 ∉ ledger, then decision ≠ SHIP

**Meaning:** No artifact can be admitted without a verified receipt. Unproven claims cannot ship.

**Enforcement:** Gate rejects any manifest without receipt field.

---

### Invariant 2: HER observes, proposes, never mutates

**Formal:** ∀ HER output: does not modify kernel_state

**Meaning:** The interpretive interface (HER) can observe state, propose new manifests, and explain decisions. It cannot mutate kernel state.

**Enforcement:** HER layer is strictly read-only for kernel state.

---

### Invariant 3: No visual object without a kernel referent

**Formal:** ∀ visible object in UI: ∃ corresponding kernel_state or L0–L5 artifact

**Meaning:** Every UI element must correspond to an actual kernel data structure. No inferred or decorative truth.

**Enforcement:** UI layer only renders projections of real state.

---

### Invariant 4: Creativity proposes; certification decides

**Formal:** production systems propose; ORACLE/HAL gate decides; ledger records

**Meaning:** The system is divided into three phases: proposal (creative), decision (certified), and recording (immutable).

**Enforcement:** gate is the only write point to ledger.

---

### Invariant 5: Same inputs → same verdict

**Formal:** ∀ m, m' ∈ ManifestSpace: m = m' ⟹ K(s, m) = K(s, m')

**Meaning:** Deterministic replay is guaranteed. The same manifest always produces the same decision.

**Enforcement:** manifest → gate reduction is a pure function.

---

## 9. Transition Events

Eight kernel-driven state changes that are animation-worthy.

### E1 — Commission Received

**Trigger:** new ingress object exists in L0

**State change:** empty slot → raw claim object in Zone A

**Animation:** commission card appears in Exploration zone

**Kernel binding:** L0 state update only

---

### E2 — Claim Normalized

**Trigger:** WUL reduction completed

**State change:** raw claim → normalized claim (A2)

**Animation:** sheet appears in Drafting zone, glyph forms appear

**Kernel binding:** L1 deterministic output

---

### E3 — Claim Challenged

**Trigger:** CLAIM_GRAPH_V1 emits support/refute structure

**State change:** A2 → A3, graph edges appear

**Animation:** edges draw on claim node, red flags appear for gaps

**Kernel binding:** L2 structural validation state

---

### E4 — Receipt Gap Exposed

**Trigger:** obligation unresolved or evidence missing

**State change:** A3 state enriched with gap markers

**Animation:** gap markers appear on challenged claim, red highlights

**Kernel binding:** L2 obligation/receipt index

---

### E5 — Certificate Issued

**Trigger:** SVE status emitted (PASS or FAIL)

**State change:** A5 certificate object created

**Animation:** badge or seal appears, coloring reflects PASS/FAIL

**Kernel binding:** L3 SVE output

---

### E6 — Gate Evaluated

**Trigger:** ORACLE/HAL emits SHIP or NO_SHIP

**State change:** A4 → (A6 if SHIP) or (A7 if NO_SHIP)

**Animation:** verdict plate appears in Termination zone, briefcase locks or closes

**Kernel binding:** L4 gate decision output

---

### E7 — Ledger Appended

**Trigger:** immutable archive row created

**State change:** A6 or A7 → ledger entry

**Animation:** briefcase moves to Ledger zone, receipt number appears, row glows

**Kernel binding:** L5 append-only write

---

### E8 — Replay Handle Emitted

**Trigger:** replayable pointer created

**State change:** ledger row → replay token (A8)

**Animation:** chain icon appears, linked to ledger row

**Kernel binding:** L5 replay pointer generation

---

## 10. Animation Law

**Core rule:** No animation may imply constitutional change unless one of the eight transition events has occurred.

**Forbidden animations:**
* briefcase moving without E6 (gate verdict)
* claim changing zones without corresponding E1–E5
* visuals implying SHIP/NO_SHIP without E6
* ledger row appearing without E7

**Allowed animations:**
* fade-in of new objects on event trigger
* edge drawing on graph structure changes
* color changes reflecting state properties
* smooth transitions between zones on E1–E8

---

## 11. Surface Rules

The office UI is a projection layer only. Not sovereign.

### Rule 1: Kernel Referent
**No zone may display an object whose kernel referent does not exist.**

Example violation: showing a "SHIP" verdict before E6 (gate verdict) has occurred.

### Rule 2: Decision Color
**No state color may imply SHIP/NO_SHIP unless gate output (L4) exists.**

Example violation: coloring a claim green to suggest admission before gate evaluation.

### Rule 3: Zone Crossing
**No object may move from zone to zone without a corresponding transition event.**

Example violation: moving A3 to Zone D without E5 (certificate issued).

### Rule 4: Demo Mode
**Demo mode must remain visibly marked as non-kernel truth.**

Example: if replaying a decision for illustration, mark it as "replay demo" not "live kernel."

---

## 12. Diagram Composition

The next deliverable must use exactly three simultaneous views in one sheet or section.

### View A — Institutional Flow
**Hard boxes and arrows showing system architecture.**

Elements:
* L0–L6 strata as boxes
* control spine as main arrow
* validator separation (two distinct branches)
* gate as choke point

Purpose: show the machine structure.

### View B — Office-Space Overlay
**The five zones mapped behind or around the flow.**

Elements:
* five zones as rooms or regions
* artifacts positioned in their zones
* transition events as arrows between zones

Purpose: show the spatial-functional organization.

### View C — Artifact Legend
**Canonical types and their state classes.**

Elements:
* A1–A8 artifacts listed
* state transitions shown (A1 → A2 → A3 → ... → A6/A7 → A8)
* visual icons for each type

Purpose: freeze the artifact ontology before implementation.

---

## 13. Freeze Condition

This spec is **LOCKED** when all of the following are true:

✅ 1. Every office zone maps to one kernel layer (A→L0, B→L2, C→L1, D→L2–L3, E→L4–L5)

✅ 2. Every visible object (A1–A8) maps to a typed artifact with frozen state

✅ 3. Every animation maps to a transition event (E1–E8)

✅ 4. CLAIM_GRAPH_V1 and SVE are explicitly separated (distinct validators)

✅ 5. ORACLE / HAL is represented as a narrow gate (not creative)

✅ 6. Ledger is represented as immutable append-only archive (crystal form, not metaphor)

✅ 7. All five invariants are printed on diagram borders

✅ 8. No sprite, character, or aesthetic design has begun

Once frozen, downstream work can proceed:
* Phase-to-Zone Binding table
* CLAIM_GRAPH_V1 visual grammar
* SVE certificate visual language
* Sprite taxonomy and motion
* Asset/theme system
* Office decoration

---

## 14. Next Artifact

After this spec is approved and frozen, the next artifact is:

**PHASE_TO_ZONE_BINDING_TABLE_V1.md**

This document maps:
* each phase of the 5-phase pipeline → zone(s)
* each artifact state → visual representation
* each transition event → motion/animation type

That table operationalizes this diagram spec.

---

**Status:** READY FOR DIAGRAM GENERATION

**Downstream artifacts are BLOCKED until this spec is frozen.**

**Do not begin sprite design, character naming, or asset creation.**

---

**Spec frozen by:** HELEN OS Kernel Authority
**Date:** 2026-03-12
**Authority:** Constitutional decree
