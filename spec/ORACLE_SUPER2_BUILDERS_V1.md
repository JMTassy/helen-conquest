# ORACLE SUPER 2: BUILDERS — Constitutional Specification V1

**Status:** DRAFT_FREEZE_CANDIDATE
**Date:** 2026-03-11
**Companion:** HELEN_KERNEL_DOCTRINE_V1 (governance receiver)

---

## 0. Purpose and Positioning

ORACLE SUPER 2: BUILDERS is a disciplined execution architecture that converts structured disagreement into finished artifacts, while leaving truth adjudication to the ORACLE/HELEN kernel.

**Clean split:**
- **BUILDERS** = production machine
- **HELEN / ORACLE** = admissibility and constitutional kernel

BUILDERS cannot emit `SHIP`/`NO_SHIP`. HELEN decides admissibility. BUILDERS hands off artifacts; HELEN decides.

---

## 1. Mission

Convert a bounded work mandate into a typed artifact bundle, then halt.

| | Value |
|---|---|
| Input | One `BUILDERS_BRIEF_V1` object |
| Process | Structured disagreement under role discipline |
| Output | Artifact bundle or abort report |
| Non-goal | Verdict authority |

---

## 2. Constitutional Boundary

### BUILDERS MAY:
- Decompose work
- Generate claims
- Draft artifacts
- Critique drafts
- Compress to a final artifact candidate
- Abort when coherence threshold is not met

### BUILDERS MAY NOT:
- Emit `SHIP` / `NO_SHIP`
- Self-attest truth
- Mutate doctrine
- Bypass receipts
- Turn narrative into authority
- Emit sovereign verdict tokens

Any BUILDERS artifact containing sovereign verdict semantics MUST be rejected by HELEN at ingest.

---

## 3. Builder Brief Contract

The brief is the root object and the execution contract for the run. It is not "prompt text."

Defined by `schemas/builders_brief_v1.schema.json`.

**Required fields:**
- `schema_version`
- `brief_id` (unique per run)
- `domain`
- `objective`
- `audience`
- `output_type`
- `constraints`
- `iteration_budget`

**Law:** No free-text hidden instructions outside this object. Seed must be explicit if determinism is expected.

---

## 4. Fixed Builder Roles

Role purity is load-bearing. No role may blur. Five roles for MVP:

### FOREMAN
- Process authority only.
- Decomposes subject, assigns work, enforces phase changes, interrupts loops.
- **CANNOT:** write final artifact, judge truth.
- **CANNOT:** emit content claims.

### RESEARCHER
- Evidence gatherer: facts, sources, comparisons.
- No interpretation-heavy synthesis.
- No final structure authority.

### SKEPTIC
- Mandatory adversary.
- Attacks assumptions, exposes contradictions, identifies missing evidence.
- **CANNOT:** provide solutions.
- **CANNOT:** emit content claims.
- If there is no tension, the system is lying.

### WRITER
- Drafts prose from accepted claims only.
- Turns claims into paragraphs, marks gaps.
- **CANNOT:** invent new claims.

### EDITOR
- Compressive authority — the decisive differentiator.
- Merges drafts, resolves contradictions, cuts 30–50%, declares completion or abort.
- Only EDITOR may emit `rewrite` claims that supersede accepted draft content.
- Only EDITOR may emit terminal decision (deliver/abort).

---

## 5. Claim Market V1

Claims replace chat. Agents submit typed work claims that can be accepted, rejected, merged, or ignored.

Defined by `schemas/builders_claim_v1.schema.json`.

**Claim types:**
- `structure` — organizational proposals
- `content` — factual or argumentative statements
- `critique` — attacks on existing claims
- `evidence` — source references and support material
- `rewrite` — replacement of accepted draft content (EDITOR only)

**Role restrictions:**
- SKEPTIC: critique and evidence only
- FOREMAN: structure only
- RESEARCHER: evidence and content only
- WRITER: content and structure only
- EDITOR: all types including rewrite

---

## 6. Five-Phase Work Pipeline

Phase order is **frozen**. No looping back.

```
Exploration → Tension → Drafting → Editorial Collapse → Delivery|Abort
```

| Phase | Goal | Key roles |
|-------|------|-----------|
| 1. Exploration | Generate options, facts, fragments, candidate structures | All, parallel |
| 2. Tension | Expose weak claims and hidden assumptions | SKEPTIC-led |
| 3. Drafting | Transform accepted claims into artifact structure and prose | WRITER + RESEARCHER |
| 4. Editorial Collapse | Irreversible compression — stop debate, force coherence | EDITOR only |
| 5. Delivery or Abort | Only two valid endings | EDITOR emits terminal |

**Critical:** A system without an explicit halting condition, abort state, and compressive authority is not a production system; it is a dialogue engine. BUILDERS must halt decisively.

---

## 7. Artifact Bundle Output

A valid BUILDERS run produces exactly:

| File | Always? |
|------|---------|
| `artifact_bundle.json` | Yes |
| `claims_log.json` | Yes |
| `phase_log.json` | Yes |
| `final_artifact.md` or `.json` | If deliver |
| `abort_report.json` | If abort |

Even in production mode, the output must already be shaped for later HELEN tribunal ingestion.

---

## 8. Abort as First-Class Outcome

Abort is **not** an exception. It is one of two lawful terminal states.

BUILDERS MUST abort when:
- Contradictions remain unresolved after Editorial Collapse
- Evidence is insufficient to support the objective
- Budget (max_phases, max_claims, max_runtime_seconds) is exhausted
- Coherence threshold is not met

Abort is a strength signal, not weakness. Silence (neither deliver nor abort) is invalid.

---

## 9. Workspace Memory Model

Production requires mutable workspace memory, not constitutional memory.

```
/claims/
/drafts/
/sources/
/logs/
```

**File-first, overwritable.** No sacred history. BUILDERS workspace is not the HELEN ledger.

ORACLE/HELEN uses append-only, immutable ledger for governance.
BUILDERS uses mutable workspace for production.

---

## 10. Receiptable Handoff to HELEN/ORACLE

Every artifact candidate MUST expose a `HELEN_HANDOFF_V1` object:

```json
{
  "schema_version": "HELEN_HANDOFF_V1",
  "handoff_id": "...",
  "source_system": "ORACLE_SUPER_2_BUILDERS",
  "run_id": "...",
  "brief_id": "...",
  "artifact_bundle_ref": "artifact_bundle.json",
  "final_artifact_ref": "final_artifact.md",
  "claims_log_ref": "claims_log.json",
  "phase_log_ref": "phase_log.json",
  "abort_report_ref": null,
  "payload_sha256": "hex",
  "source_refs": [],
  "evidence_refs": [],
  "open_risks": [],
  "non_sovereign_attestation": {
    "verdict_emitted": false,
    "truth_claimed": false,
    "doctrine_mutated": false
  }
}
```

**The handoff MUST NOT contain:** `SHIP`, `NO_SHIP`, sovereign truth claims, doctrine updates, or receipt authorization.

---

## 11. HELEN Validation Order for Ingested BUILDERS Output

```
1. Validate HELEN_HANDOFF_V1
2. Resolve referenced BUILDERS_RUN_V1
3. Resolve referenced BUILDERS_BRIEF_V1
4. Validate all referenced BUILDERS_CLAIM_V1 entries
5. Recompute payload hashes
6. Verify no sovereign fields appear
7. Route to CLAIM_GRAPH_V1
8. Enter invariant engine / reducer path
```

---

## 12. Cross-Schema Laws

**Law A — Identity:** `brief_id`, `run_id`, `claim_id`, `handoff_id` must all be namespace-unique.

**Law B — Role Separation:** BUILDERS roles may create claims and artifacts. Only HELEN may adjudicate admissibility.

**Law C — Deterministic Termination:** Every `BUILDERS_RUN_V1` ends in exactly one of: `deliver` or `abort`. Missing `termination.kind` is invalid.

**Law D — Artifact Completeness:** A valid `HELEN_HANDOFF_V1` must point to artifact bundle, final artifact or abort report, claims log, and phase log.

**Law E — No Verdict Leakage:** Any BUILDERS artifact containing sovereign verdict semantics MUST be rejected by HELEN at ingest.

**Law F — Canonicalization:** All schemas include `"canonicalization": "JCS_SHA256_V1"`. This field is constitutive.

---

## 13. What Must Stay Out of BUILDERS MVP

Do not include:
- Binary verdict logic
- Sacred ledger semantics
- Constitutional update machinery
- Proto-conscious narrative layers
- Live doctrine mutation
- Autonomous civilization logic

Keep the MVP aggressively narrow.

---

## 14. Success Criteria

BUILDERS MVP is real when it can do three things reliably:

1. Turn one bounded brief into one coherent artifact candidate.
2. Halt with either `deliver` or `abort`.
3. Export a typed bundle that HELEN can later inspect.

---

## 15. Upgrade Path

```
Brief
 → Foreman
 → Specialists (Researcher, Skeptic, Writer)
 → Claim Market
 → Draft
 → Skeptic pass
 → Editor compression
 → Artifact bundle
 → HELEN_HANDOFF_V1
 → HELEN/ORACLE tribunal (optional)
```

---

## 16. Relation to ORACLE SUPERTEAM

| System | Role | Authority |
|--------|------|-----------|
| ORACLE SUPERTEAM | Governance kernel | Sovereign |
| ORACLE SUPER 2: BUILDERS | Production machine | Non-sovereign |

BUILDERS sits under ORACLE SUPERTEAM, not beside it. ORACLE SUPERTEAM remains the governance kernel that judges receipted obligations rather than doing the production itself.

---

## 17. Companion Schemas

- `schemas/builders_brief_v1.schema.json`
- `schemas/builders_claim_v1.schema.json`
- `schemas/builders_run_v1.schema.json`
- `schemas/helen_handoff_v1.schema.json`

---

*This is a CORE-mode draft. No sovereign ledger mutation. No SHIP gate passed.*
*S2 — NO RECEIPT = NO CLAIM. This document is a production spec, not a governance decision.*
