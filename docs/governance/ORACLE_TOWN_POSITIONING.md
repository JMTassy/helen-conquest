# Oracle Town: Positioning Note

## The One-Sentence Definition

**Most multi-agent systems try to reduce error through organizational consensus. Oracle Town treats legitimacy as a jurisdictional property: no claim mutates the world unless it satisfies deterministic law, produces admissible evidence, and receives a signed receipt.**

---

## Three Architectures. One Journey.

### 1. Tool Chaining (Single-Agent)
- Example: ReAct agent with sequential tools
- Error handling: Self-review only
- Success rate: ~60% (paper baseline)
- Problem: Agent that made the mistake evaluates the mistake

### 2. Organizational Council (Multi-Agent)
- Example: Isotopes AI Office (Vijayaraghavan et al., 2025)
- Error handling: Cascaded LLM critics with veto authority
- Success rate: ~92% (measured on 522 production sessions)
- Remaining failure: ~8% (irreducible ambiguity)
- Cost: 40% computational overhead
- Problem: Critics are still probabilistic; audit is narrative

### 3. Constitutional Jurisdiction (Oracle Town)
- Error handling: Deterministic policy gates + cryptographic authority
- Legitimacy: No world mutation without signed receipt + policy pinning
- Guarantee: Every state change backed by deterministic law
- Cost: Acceptance gate (high) + determinism requirement (medium)
- Advantage: Errors are prevented, not just detected; failures are auditable, not narratable

---

## Side-by-Side: What's Different

| Dimension | AI Office | Oracle Town |
|-----------|-----------|------------|
| **What it does** | Catches errors before user sees them | Prevents errors from existing (no receipt = no execution) |
| **Verdict mechanism** | LLM critics vote (probabilistic) | Policy gates execute (deterministic) |
| **Authority** | Organizational oversight | Jurisdictional law |
| **Audit trail** | Event-sourced logs | Cryptographically signed receipts + append-only ledger |
| **Acceptance criteria** | Natural language ("looks good") | Machine-checkable ("K0 ∧ K1 ∧ K5 ∧ K7 all pass") |
| **Execution** | "Approved output allowed to run" | "Only with receipt present; policy hash pinned" |
| **Failure class** | ~8% residual (ambiguity) | Ambiguity is illegal (required acceptance criteria) |
| **Scalability** | 40% overhead; heavy-tail distribution | Prune gates by marginal value; no bureaucratic bloat |

---

## Why This Matters

The AI Office paper proves a hard ceiling exists: **~92% success, ~8% irreducible.**

That residual 8% is not error. It is ambiguity.

Most systems accept this as inevitable. Oracle Town makes ambiguity illegal:

**Every claim must include:**
- Success conditions (machine-checkable)
- Disallowed side effects
- Falsifiers ("what would disprove this")
- Rollback plan

**TRI rejects any claim lacking this (K1 fail-closed).**

Result: No ambiguous claims enter the authority layer. The 8% problem disappears not because Oracle Town is smarter than AI Office, but because Oracle Town refuses to accept ambiguous input.

---

## The Integration Strategy

Do **not** replace the paper's insights. Build **on top** of them:

- **Labor (Cheap, Parallel, Adversarial):**
  - Multi-rival proposal generation (OBS/INS/BRF/BRF_COUNTER)
  - Orthogonal checkers: contradictory claims exposed before authority
  - Adopts the paper's "team of rivals" principle

- **Authority (Deterministic, Single, Jurisdictional):**
  - Policy-backed gates (K0-K7, expanding)
  - Deterministic verdicts (no "confidence scores")
  - Cryptographically signed receipts
  - Policy version pinned per run

- **World (Passive, Receipt-Gated):**
  - No mutation without receipt
  - No receipt without deterministic approval
  - Audit trail: every receipt links claim → verdict → policy hash

---

## Three Concrete Upgrades (Completed)

### A. Mandatory Machine-Checkable Acceptance Criteria
- Every claim must include `acceptance_criteria` (JSON structure)
- Missing/incomplete criteria → TRI rejects automatically (K1 fail-closed)
- Directly attacks the 7–8% ambiguity residual

### B. Single Counter-Analytical Labor Role (BRF_COUNTER)
- Generates strongest counter-narrative to main brief
- Identifies top 3 falsifiers (what would disprove main claim)
- Authority stays single and deterministic; rivalry stays in Labor
- Prevents overconfidence without introducing consensus voting

### C. Gate Marginal Value Tracking
- Per-gate metrics: unique blocks, overlaps, cost
- Compute catch rate like the paper does
- Enable pruning (remove low-value gates), not just accumulation
- Avoids bureaucratic bloat that kills most systems

---

## The Hard Truth

The AI Office paper's 92.1% success rate is **not** a victory.

It is the system pointing to its own brittleness.

Oracle Town's different question is not "Can we catch 92% of errors?"

It is: **"Can we make ambiguity itself illegal?"**

The answer is yes. And the mechanism is simple: make acceptance criteria mandatory, deterministic, and machine-checkable.

---

## Next Three Months

- **Week 1–2:** Extend claim schema (done), integrate BRF_COUNTER, add K3–K6 gates (Scope, Chain, Ambiguity, Rollback)
- **Month 2:** Context ray tracing (selective visibility), gate metrics dashboard
- **Month 3:** Ledger outcome loop (did acceptance criteria hold?), policy evolution v2

---

## Final Positioning

> **Oracle Town is not a smarter version of the AI Office. It is a different class of system: not trying to reduce error through better consensus, but preventing illegitimate claims through jurisdictional law.**

The paper validates the structure. Oracle Town goes further and operationalizes legitimacy itself.
