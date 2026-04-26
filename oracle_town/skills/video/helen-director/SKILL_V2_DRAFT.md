# HELEN Director — Context Kernel Extension (DRAFT, NOT CANON)

> **STATUS:** DRAFT — non-canon, non-doctrine, pending MAYOR validation.
> **REVISION:** 2 (expanded §1–§10; rev 1 had §1–§6).
> **DOES NOT REPLACE OR AMEND** `SKILL.md` (§1–§16, live).
> **PROVENANCE:** Substantive content drafted externally and routed through the operator. Claude Code is the courier, not the proposer. This file is a non-sovereign sidecar staged for review under DOCTRINE_ADMISSION_PROTOCOL_V1.
> **AUTHORSHIP CHAIN:** external model proposal → operator approval to stage → Claude Code Write. Claude Code did not author the principles below.
> **DELTA SCOPE:** additive layer ("Context Kernel Extension"). Live SKILL.md §1–§16 remain authoritative until MAYOR rules.
> **STRIPPED FROM SOURCE:** numeric "bits/token" claims removed (not source-pinned, would fail K-tau §SCHEMA + §IO grounding).

---

## §1 — Core Principle

HELEN does not rely on implicit model knowledge.

HELEN constructs knowledge per run by:
- selecting artifacts
- compressing signal
- injecting context

## §2 — Execution Law

Every operation must follow:

1. DEFINE required knowledge
2. SELECT minimal artifacts
3. COMPRESS signal
4. INJECT into context
5. EXECUTE
6. VALIDATE against context

No step may be skipped.

## §3 — Trust Hierarchy

1. Injected context — HIGH
2. Repo artifacts — HIGH
3. Retrieved content — MEDIUM
4. Model weights — LOW

Implicit knowledge is never authoritative.

## §4 — Validation Rule (HAL)

If output cannot be traced to injected context: REJECT.
If partially grounded: DOWNGRADE.

## §5 — Kernel Definition

HELEN_KERNEL = context_compiler + retrieval + validation_gate

## §6 — Context Constraint

The context window is finite. Only injected information exists for the model. All reasoning must operate within this boundary.

## §7 — Signal Discipline

More context ≠ better output.

HELEN enforces:
- minimal sufficient context
- maximum signal density

## §8 — Failure Modes

1. Context overload → degraded reasoning
2. Missing artifacts → hallucination risk
3. Implicit fallback → invalid outputs
4. Mixed scopes → leakage

## §9 — Success Condition

A run is valid if:
- all claims trace to context
- no implicit assumptions
- output is reproducible

## §10 — Master Law

HELEN does not know.
HELEN selects what is known.

---

## Open questions for MAYOR

1. **Section numbering collision.** This draft uses §1–§10 for Context Kernel principles. Live SKILL.md already owns §1–§16. If admitted, does this become §17 ("Context Kernel Extension") inside live SKILL.md, or a separate `SKILL_CONTEXT_KERNEL.md` sibling?
2. **Trust hierarchy enforcement.** §3 ranks "model weights LOW". This is a posture, not a mechanism. What gate enforces it? K-tau §IO already covers IO grounding. Does this duplicate or extend?
3. **§4 reject/downgrade rule.** Is rejection at the gate level (BLOCK_RECEIPT_V1) or at the runtime level (executor refuses to emit)? Where is the DOWNGRADE signal recorded?
4. **§6 finite-context constraint.** Already implicit in K8 (mu_NDARTIFACT). Does this draft add anything K8 does not?
5. **§7 "signal density" measurement.** "Minimal sufficient" and "maximum density" are unquantified. What metric? What threshold? Without one, §7 is unreviewable.
6. **§8 failure modes — relation to existing K-gates.** "Context overload" and "implicit fallback" overlap K8 mu_NDWRAP and K-tau mu_DETERMINISM. Is §8 redundant or additive?
7. **§9 reproducibility.** "Output is reproducible" is the K8 mu_NDLEDGER guarantee. Same question as #6.
8. **§10 vs constitutional epistemology.** "HELEN does not know" contradicts the live SOUL.md / HELEN.md framing where HELEN holds the spine. Doctrine collision must be ruled before admission.

## Revision history (this file only)

- rev 1 — §1–§6, staged on operator instruction.
- rev 2 — REPLACE per operator decision; added §7 Signal Discipline, §8 Failure Modes, §9 Success Condition, §10 Master Law; expanded §4 with DOWNGRADE branch; added open questions 5–8.

## Explicit non-actions taken at staging

- ❌ Did not overwrite `SKILL.md`.
- ❌ Did not write any Python (`helen_context_engine/{selector,assembler,validator}.py`).
- ❌ Did not invoke `tools/helen_say.py` to surface this draft to the kernel boundary — that is a separate operator decision.
- ❌ Did not import the "0.07 vs 2.5M bits/token" framing.
- ❌ Did not import the unrelated video-masterpiece concept ("THE REFLECTION THAT DIDN'T FOLLOW") — separate proposal, separate review, decision pending.
