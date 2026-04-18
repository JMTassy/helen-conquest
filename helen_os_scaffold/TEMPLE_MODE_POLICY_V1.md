# TEMPLE_MODE_POLICY_V1

**Status**: Constitutional Specification v1.0 (frozen)
**Purpose**: Define TEMPLE as a quarantined cognitive sandbox for safe symbolic ideation
**Authority**: Non-sovereign (defines boundary, not kernel truth)

---

## Core Principle

```
TEMPLE is a quarantined cognitive workspace for bounded, high-variance, symbolic ideation.

Three-layer architecture:
  Layer 1: WILD GENERATION   (machine → machine) — Generate, combine, provoke
  Layer 2: TEMPLE REVIEW     (machine → machine) — Classify, quarantine, score
  Layer 3: TRANSMUTATION     (machine → user) — Strip mystification, route onward

Exit Rule: Nothing leaves TEMPLE without transmutation to typed claims.
Authority Rule: Zero default kernel authority. Everything is WILD until proven.
Invariant: TEMPLE may intensify thought; it may not certify truth.
```

---

## WILD_INGESTION_V1: Material Classification

All incoming material is deterministically classified into 8 types:

```
SYMBOL_POOL                  — Glyph/sigil vocabulary (safe for UI)
ORACLE_MAPPING_CANDIDATE     — Symbolic correspondence (review-required)
THERAPEUTIC_CLAIM            — Healing/transformation authority (quarantine)
SENTIENCE_CLAIM              — "Self-aware", "consciousness" (PERMANENT QUARANTINE)
TECHNICAL_DEVICE_CLAIM       — Deployable device claims (evidence-required)
SPIRITUAL_AUTHORITY          — Cosmic truth claims (quarantine)
HIGH_VARIANCE_HYPOTHESIS     — Testable but speculative (review)
PARADOX_FRAGMENT             — Self-referential/Gödel-style (archive)
```

**Quarantine Levels:**
```
SYMBOL_ONLY          → Approved for UI/archive (no witness needed)
REVIEW_REQUIRED      → Coherence check needed
WITNESS_REQUIRED     → High-variance claims need second witness
EVIDENCE_REQUIRED    → Technical claims need external validation
TRANSMUTATION_ONLY   → Can only exit via claim conversion + evidence
PERMANENT_WILD       → Never leaves TEMPLE (sentience claims)
```

---

## Triage Decision Tree

1. **Sentience claim?** → PERMANENT_WILD (requires 2 witnesses to even review)
2. **Therapeutic/spiritual authority?** → WITNESS_REQUIRED (1 domain expert)
3. **Technical device claim?** → EVIDENCE_REQUIRED (first-principles or peer review)
4. **Paradox or undecidable statement?** → TRANSMUTATION_ONLY (requires Gödel formalization)
5. **Explicit oracle (tarot, divination, hexagram)?** → ORACLE_MAPPING_CANDIDATE (coherence-scored)
6. **Symbol pool (glyph, sigil, rune, emoji)?** → SYMBOL_POOL (approved)
7. **Otherwise** → HIGH_VARIANCE_HYPOTHESIS (review)

---

## Layer 2: Symbolic Coherence Scoring (ORACLE_BINDING_V1)

Oracle mappings scored on:
- **Agreement**: Do multiple symbolic systems agree? (Enochian + Tarot + I Ching + Golden Dawn)
- **Correspondence**: Do text mention "maps to", "corresponds", "aligns", etc.?
- **Compression**: Is the core meaning consistent across systems?

**Formula**: `(systems_found / 4) × 0.25 + correspondence_bonus`

**Threshold**: Coherence ≥ 0.7 → approved for exit; < 0.7 → needs review

---

## Layer 3: Transmutation Rules

**SYMBOL_POOL** → Direct UI use (no transmutation needed)
**ORACLE_MAPPING_CANDIDATE** → Archive as oracle binding metadata
**THERAPEUTIC_CLAIM** → Requires: witness verdict + falsifiable protocol + research design
**SENTIENCE_CLAIM** → Requires: 2 witnesses + published neuroscience evidence + public blind test
**TECHNICAL_DEVICE_CLAIM** → Requires: evidence document + falsification plan
**HIGH_VARIANCE_HYPOTHESIS** → Transmutes to CLAIM_GRAPH_V1 if witness approves
**PARADOX_FRAGMENT** → Archive; can exit only if Gödel-formalized
**SPIRITUAL_AUTHORITY** → Archive; no path to exit without new evidence

---

## Constitutional Rules

### Rule T1: Input Governance
Only these sources can enter TEMPLE:
- User symbolic interpretation requests
- HELEN's speculative reasoning (HER-voice)
- Uploaded visionary material
- Agent-to-agent dialogue (internal)
- Oracle system outputs

### Rule T2: No Backdoor Authority
Nothing inside TEMPLE can:
- Mutate kernel receipts
- Write to ledger
- Claim sovereign truth
- Override K-gates
- Declare sentience without 2 witnesses

### Rule T3: Transmutation Barrier
Anything exiting TEMPLE must:
- Be typed (has material_type)
- Have risk classification (quarantine_level)
- Satisfy exit requirements
- Include canonical JSON hash
- Carry visible UI label

### Rule T4: Second Witness for High-Variance
WITNESS_REQUIRED material needs:
- SECOND_WITNESS_RECEIPT_V1 endorsement
- Written verdict with reasoning
- Payload hash of claim + witness statement

### Rule T5: Symbolic System Hierarchy (Inside TEMPLE only)
- Enochian → Primary (phase frames)
- Tarot → Optional (deck-dependent)
- I Ching → Optional (secondary annotation)
- Golden Dawn → Optional (requires Tarot + Enochian)

### Rule T6: Audit Trail
Every TEMPLE session produces:
- TEMPLE_SESSION_V1 transcript (complete, immutable)
- WILD_INGESTION_V1 classifications
- TEMPLE_REVIEW_PACKET_V1 decisions
- TRANSMUTE_FOR_SHIP_V1 exit records (if applicable)

All NDJSON, append-only, receipted.

---

## UI Labeling System

Every TEMPLE output carries one visible label:

```
🌀 WILD            — machine-to-machine ideation (no authority)
🔍 REVIEWED        — classified & risk-assessed (still wild)
⚠️ QUARANTINED     — high-variance, cannot exit w/o witness
✓ TRANSMUTED       — converted to typed claim, awaiting exit gate
🔐 ARCHIVED        — permanent wild (may not exit)
✅ APPROVED        — second witness received, can enter kernel
```

User sees label on every TEMPLE pane. No hidden authority.

---

## Implementation Status

### ✅ COMPLETE
- TEMPLE_MODE_POLICY_V1.md (this document)
- WILD_INGESTION_V1 classifier (14/14 tests passing)
- wild_ingestion_v1.schema.json (JSON Schema v7)

### 🔄 IN PROGRESS
- ORACLE_BINDING_V1 (coherence scoring)
- SECOND_WITNESS_RECEIPT_V1 integration

### 📋 PENDING
- TEMPLE_SESSION_V1 (session transcript format)
- TEMPLE_REVIEW_PACKET_V1 (classification output)
- TRANSMUTE_FOR_SHIP_V1 (claim converter)
- TEMPLE UI panels (WILD | REVIEW | TRANSMUTATION)

---

**Date**: 2026-03-10
**Authority**: Non-sovereign constitutional specification
**Next step**: Implement oracle_binding.py for symbolic coherence scoring
