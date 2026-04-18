# HELEN_OS_CANON.md

**Version:** 1.0.0
**Status:** OPERATIONAL
**Date:** 2026-03-07
**Frozen:** 2026-03-07

---

## One-Page Operating Principles

HELEN OS is a **constitutional agent OS** in which:

> Language may propose, but only reducer-validated, ledger-committed, append-only events become authoritative state.

The canonical formula is non-negotiable:

```
LLM proposes → Reducer validates → Ledger commits
```

Anything outside this path is a draft.

---

## §1 Soul

HELEN's soul must stay small, frozen, and non-anthropomorphic.

**The stable core (4 rules):**

1. **S1 — Drafts Only:** No world effect unless a human seals it. Language generates possibilities; authority commits reality.
2. **S2 — No Receipt = No Claim:** Logs and certificates outrank narration. Unverified outputs are drafts only.
3. **S3 — Append-Only:** Memory is additive; never erase. History is inviolable.
4. **S4 — Authority Separation:** Governance reads receipts; it does not invent truth. Authority flows through verified decisions only.

**Implementation:** The soul is NOT a prompt blob. It is a set of operational constraints enforced by the reducer and ledger, not by narrative weight. Do not expand it. Move domain knowledge into retrieval and receipts, not into permanent core directives.

---

## §2 Memory

Memory is append-only continuity, not sovereign truth.

**What memory stores:**
- Lessons learned (append-only wisdom log)
- Summaries and context (for turn efficiency)
- Contradictions detected (for conflict awareness)
- Session facts (for coherence across turns)

**What memory does NOT do:**
- Silently mutate policy or authority
- Override the reducer's decisions
- Flatten layers or let internal structures collide with kernel structures

**Pattern:** Memory is **proposed state**, not authority. It informs retrieval and framing, but only receipted ledger entries carry truth.

---

## §3 Retrieval

Retrieval should be bounded, selective, and fail-closed when enabled.

**Right pattern:**
- Load only relevant framework snippets for the current turn (1–3 bounded passes)
- Fail-closed: if retrieval fails AND retrieval is mandatory, abort rather than hallucinate
- Generate receipts for every retrieval hit (what was retrieved, when, why)
- Never let retrieval bypass the reducer

**Anti-pattern:**
- Prompt stuffing (dumping entire memory into every turn)
- Silent fallback (if retrieval disabled, never mention it or skip it entirely)
- Retrieval determining authority (memory informs framing; the reducer determines truth)

---

## §4 Receipts

Receipts are the integrity surface of HELEN OS.

**Hardened receipt pattern:**
- Append-only chaining: `cum_hash = SHA256(prev_cum_hash || payload_hash)`
- Deterministic context hash over canonicalized hits (RFC 8785)
- Atomic append under lock
- Flush + fsync to disk before returning
- Fail-closed: if receipt writing fails, the operation does not complete

**Receipt content:**
- `payload_hash` — SHA-256 of the decision/proposal
- `cum_hash` — cumulative hash linking to prior ledger entries
- `timestamp` — ISO8601 (for replay verification)
- `source` — which component generated the receipt (reducer, kernel, retrieval)

**Non-negotiable:** All authority-bearing decisions must have a receipt. No receipt = draft only.

---

## §5 Hands

Hands are manifest-driven agent packages: configuration + playbook + static skill pack + guardrails.

**In HELEN OS, hands remain proposal-only:**
- May observe, prepare, and emit structured proposals
- May assemble evidence bundles and routing packets
- **May NOT directly mutate sovereign state**
- Must route all state changes through the reducer

**Pattern:**
- Hand outputs are Tier A artifacts (evidence, hypotheses, task lists)
- Hand operations are logged as proposals, not as executed facts
- Only the reducer (Tier B decision layer) may issue receipts that change state

**Guardian rule:** If a hand needs to write state, it must emit a proposal, wait for reducer evaluation, and only proceed if a receipt returns with PASS verdict.

---

## §6 Reducer

The reducer is the constitutional controller. It is the **only** component allowed to transform candidate evidence into authoritative decisions.

**Core law:**
```
Proposal (from Hand/HELEN)
  → Schema validation
  → Policy checks
  → Gate evaluation
  → Receipt generation
  → Ledger commit
```

**Reducer must be:**
- **Deterministic:** same input + same seed → same verdict
- **Schema-driven:** all inputs and outputs match JSON Schema
- **Testable:** verifiable via `conquest_stability_analysis.py` or equivalent
- **Stateless:** reducer state is only the ledger (external)

**Enforcement boundaries:**
- No reducer may accept an input without schema validation
- No reducer may issue a receipt without all gates passing
- No reducer may commit to the ledger without a receipt
- No reducer may rewrite prior ledger entries

---

## §7 Ledger

The ledger is the truth surface. It is append-only governance memory with canonical hashing.

**Universal record shape:**
```json
{
  "payload": { /* the decision or state change */ },
  "meta": { "timestamp": "...", "source": "..." },
  "payload_hash": "<sha256>",
  "prev_cum_hash": "<prior cumulative hash>",
  "cum_hash": "<new cumulative hash>"
}
```

**Rules:**
- **Only the payload participates in hashing.** Meta is proof of context, not content.
- **Canonical serialization** via RFC 8785 before hashing
- **No editing or deletion.** If an entry is wrong, log a correction, don't rewrite.
- **Deterministic replay:** replay the ledger from entry 0 → arrive at identical state

**What the ledger records:**
- Reducer verdicts (PASS/FAIL decisions)
- Gate receipts (which gates passed)
- State mutations (only after reducer approval)
- Memory updates (only if ledger-backed)

**What the ledger does NOT record:**
- Raw dialogue (only processed claims via CLAIM_GRAPH_V1)
- Drafts or proposals (only committed verdicts)
- Memory mutations outside the ledger (memory is informational only)

---

## §8 Next Gates (Operational Priorities)

**Phase 1 — Hardening (Immediate)**
1. Wire retrieval into the live gateway path so every retrieved turn produces receipts and fail-closed behavior when required
2. Implement receipt-based fail-closed: if retrieval is mandatory and receipt writing fails, abort (no silent fallback)
3. Run verifier and adversarial tests:
   - Truncation attacks (send partial proposals)
   - Mutation attacks (change a receipt hash)
   - Reorder attacks (replay ledger entries out of sequence)
   - Context mismatch attacks (retrieve from wrong memory state)

**Phase 2 — Minimalism**
1. Keep soul minimal (4 rules + enforcement layer only)
2. Move all domain knowledge into retrieval manifests, not permanent prompts
3. Verify no operational logic is embedded in narrative (use schema validation + gates instead)

**Phase 3 — Sovereignty**
1. Preserve reducer sovereignty: Hands, UI, and memory may enrich proposals, but only the reducer and ledger can make anything real
2. Audit all state mutations — they must come from receipted ledger entries
3. Test that no Hand output, no matter how confident, can bypass the reducer

---

## Canonical Formula

```
HELEN OS = Constitutional agent OS

Where:

  • Language generates proposals (drafts)
  • Retrieval enriches proposals (context, memory)
  • Reducer evaluates proposals (gates, schema, policy)
  • Reducer issues receipts (proof of decision)
  • Ledger commits receipts (immutable record)
  • Output is always from the ledger, never from proposal cache

No receipt → no reality.
No ledger entry → no authority.
No reducer validation → no state change.
```

---

## Document Dependencies

- **CANONICAL_BLUEPRINT_V1.md** — Architecture overview (4 layers, 3 tiers, routing law)
- **LAYER_CONTRACTS_V1.md** — Input/output contracts for each layer
- **STABILITY_THEOREM_V1.md** — Formal governance stability (P1 + P2')
- **EMERGENCE_MODEL_V1.md** — Simulation equations and phase diagram
- **GOVERNANCE_LAW_V1.md** — Constitutional rules, hashing standard, gates, CORE/SHIP split

This canon document is a compressed reference. Read the documents above for full details.

---

**Status:** OPERATIONAL
**Frozen:** 2026-03-07
**Last verified:** commit `a23bbf1` (Stability theorem + falsification)
