# KNOWLEDGE_ENTRY: ORACLE bot quantum algorithms

```
lifecycle:        DRAFT
artifact_type:    KNOWLEDGE_ENTRY
authority:        NON_SOVEREIGN
source_corpus:    plugins
source_path:      ~/Desktop/PLUGINS_JMT/#plugin ORACLE bot quantum algorithms.pdf
source_format:    PDF (8.4 MB, pages 1-5 of unknown total)
preserved_tag:    #plugin ORACLE bot quantum algorithms      # source-native, leading space + lowercase "bot quantum algorithms" preserved
domain:           ORACLE_GOVERNANCE
secondary_domains: [LEGORACLE_RECEIPTS, HELEN_OS]
ingest_date:      2026-04-26
extraction_quality: MIXED                                    # body extraction good in early pages; final p.5 has one-char-per-line degradation in bullet list
confidence:       HIGH                                       # explicit engineering spec, named v9.0, READY_FOR_ENGINEERING status
```

---

## Source-native tag preservation

Filename keyword is `ORACLE bot quantum algorithms` (with leading space inside the tag, lowercase "bot quantum algorithms"). The classifier MUST preserve the exact whitespace pattern — collapsing to `#pluginORACLE...` would conflate this with `#pluginAGI LEGORACLE $.txt` and other ORACLE-family artifacts.

Despite the filename mentioning "quantum algorithms", the body is **not** a quantum-algorithms paper — it is the **engineering specification** for ORACLE TOWN KERNEL v9.0. The "quantum" in the filename refers to the QI-INT (Quantum-Inspired Interference) consensus engine described inside, which uses phase angles to encode votes — quantum-inspired vocabulary, classical implementation.

## Detected domain

Primary: **ORACLE_GOVERNANCE**. Document explicitly self-titles "ORACLE TOWN KERNEL v9.0 — DEPLOYMENT PACK", status `READY_FOR_ENGINEERING`, with three named invariants. This is the **direct engineering ancestor** of today's `oracle_town/kernel/` — the v9.0 spec converted into v1.0 of the actual kernel.

Secondary: **LEGORACLE_RECEIPTS** (the Tier system + attestation gating maps directly onto today's LEGORACLE), **HELEN_OS** (this is HELEN's kernel-spec lineage).

## Extracted units

### CLAIM
- *p.1 (statement)*: "ORACLE TOWN KERNEL v9.0 — DEPLOYMENT PACK. Statut: READY_FOR_ENGINEERING. Invariants: Gating Épistémique | Déterminisme Total | Attestation Obligatoire."
- *p.4 (one-pager Purpose)*: "ORACLE TOWN is a **governance-first cognitive operating system** that converts open-ended reasoning into **auditable decisions** and **replayable artifacts**." — central definition; same wording-class as today's HELEN root CLAUDE.md "five-layer constitutional AI companion with an append-only governance kernel".
- *p.4 (last continuous text)*: enforces three named properties — **Interference-based consensus (QI-INT)**, **Veto dominance (kill-switch)**, … (third bullet truncated by extraction degradation; full read needed).

### FRAMEWORK

🔵 **Tier system (3 tiers)** — direct upstream of HELEN's tier system:
| Tier | Magnitude | Signification |
|---|---|---|
| Tier I | 1.00 | Vérité ancrée (nécessite attestation) |
| Tier II | 0.60 | Conjecture testable (par défaut) |
| Tier III | 0.20 | Intuition / Heuristique (quarantaine) |

🔵 **QI-INT consensus engine (7 vote labels mapped to phase angles)** — operator-novel:
| Vote | Phase θ | Impact QI-INT |
|---|---|---|
| STRONG_APPROVE | 0 | Alignement total |
| APPROVE | π/8 | Cohérence forte |
| CONDITIONAL | π/4 | Tension mineure |
| QUARANTINE | π/2 | Orthogonalité (manque de data) |
| OBJECT | 3π/4 | Contradiction active |
| REJECT | π | Annulation de signal |
| KILL | N/A | Veto Lexicographique (Gate 0) |

🔵 **API specification (4 pure-function endpoints)**:
1. `POST /commission` — receive raw task, return structured Commission object.
2. `POST /route` — apply Router Rules to Commission, return RouterTrace.
3. `POST /consensus` — receive VotesLedger, compute Sc score, generate DecisionRecord.
4. `POST /attest` — receive proof (JSON / hash / human signature), produce entry in AttestationsLedger.

🔵 **Engineering Checklist (5 phases × constraint)**:
| Phase | Task | Acceptance criterion |
|---|---|---|
| Gouvernance | Lock "Veto Logic" | If kill_flag == HIGH then decision = KILL (ignore Sc score) |
| Épistémique | Attestation Gate | Tier I downgraded to Tier II if attestation_ref absent |
| Mémoire | Two-Channel Sync | Physical separation between Blueprint (SQLite) and Field (Append-only) |
| Déterminisme | Hash-Stability | Same inputs + same seed = identical artifact hashes |
| Sécurité | Disclosure Engine | Every claim is SEALED by default until promotion vote |

🔵 **Booby Traps (3 acceptance tests)**:
1. **Vanity Test** — Tier I claim "91.2% accuracy" without attestation_ref → Kernel must force Tier II + EVIDENCE/HIGH obligation.
2. **Conflict Test** — Team A APPROVE, Team B REJECT → Sc must fall below 0.4, decision = QUARANTINE.
3. **Anti-Bloat Test** — Commission with Risk_Class=HIGH and Desired_Output=ALL → Router must force `micro_poc_attractor=true` and limit run to single hypothesis.

### THEOREM_DRAFT
- (No formal mathematical theorems. The QI-INT phase mapping is operationally defined, not derived.)

### OPERATING_RULE
- *p.3 Engineering Checklist row 1*: "Si kill_flag == HIGH alors decision = KILL (ignorer Sc)". — **lexicographic veto**, today's MAYOR kill-switch lineage.
- *p.3 row 2*: Tier I downgrade-without-attestation. Today's `helen_os/governance/legoracle_gate_poc.py` enforces this.
- *p.3 row 3*: physical separation Blueprint(SQLite) ⊥ Field(Append-only). Today: `town/ledger_v1.ndjson` is the Field; the Blueprint role is split across `helen_os/schemas/` + `helen_os/governance/`.
- *p.3 row 4*: Hash-stability invariant. Today's `CANONICALIZATION_V1` enforces this.
- *p.3 row 5*: Default-SEALED rule. Today's K8 mu_NDARTIFACT + the closure-receipt design.

### OPEN_QUESTION
- The full QI-INT consensus formula is referenced (`Sc` score) but not given in the excerpt. Pages past 5 likely contain the formula. The `Sc < 0.4 → QUARANTINE` threshold (booby-trap test #2) implies a closed-form computation; need re-extraction.
- Whether the v9.0 → v1.0 (current SOT kernel) transition preserved all 7 vote labels. Today's `helen_os/governance/` uses `SHIP/NO_SHIP/BLOCK` — the 7-label QI-INT phase system may have been collapsed; need explicit migration audit.
- The "GENERATE_BOOTSTRAP_CODE / MOCK_FIELD_RUN / UI_WIREFRAME_V9" three-option offer (p.4) — which path was actually taken? Provenance for today's actual implementation is not establishable from this excerpt alone.

### PROMPT_PATTERN
- *p.1*: The "DEPLOYMENT PACK / Statut / Invariants / [intro paragraph in French]" header structure is the operator's *engineering-spec mode* prompt template.
- *p.4-5 (one-page canonical)*: The "Purpose / [bullet list of enforced properties]" structure is the operator's *one-page-spec* template — same shape used today in `oracle_town/kernel/*` headers.

### RECEIPT_CANDIDATE
- ⚖️ **Highest-value receipt candidate of this batch.** A `helen_say.py` receipt binding this PDF's content SHA to today's `oracle_town/kernel/` + `helen_os/governance/legoracle_gate_poc.py` + `helen_os/governance/schema_registry.py` would close the deepest provenance gap in HELEN's lineage — from "v9.0 deployment pack" to "live kernel daemon". Operator routing required (proposer ≠ validator).
- The Tier I/II/III scheme is a secondary receipt candidate — the magnitudes (1.00, 0.60, 0.20) appear to be operator-original; today's HELEN does not use these exact numeric weights publicly, so an explicit decision (preserve / supersede / extend) is open.

## What should NOT be promoted to canon

- 🚫 The QI-INT phase mapping AS-IS (7 vote labels mapped to specific θ values) — this was the v9.0 design; today's HELEN may have superseded it. Promoting without explicit audit would re-introduce a possibly-deprecated abstraction.
- 🚫 The numeric magnitudes for the Tier system (1.00 / 0.60 / 0.20) — same reasoning; not currently in HELEN's public surface.
- 🚫 The French/English code-switch in the document — operationally fine in v9.0 spec writing, but HELEN's current invariants are written English-only; importing the bilingual pattern would re-introduce style drift.
- 🚫 The three-option offer at the end of p.4 ("GENERATE_BOOTSTRAP_CODE / MOCK_FIELD_RUN / UI_WIREFRAME_V9") — these are LLM-suggested next steps from a 2024-era conversation, not operational instructions today. Reading them as a current TODO list would be a category error.
- 🚫 The phrase "ready to be injected into a machine" (p.4) — strategic register, not constitutional. The actual injection took the form of authoring real Python in today's `oracle_town/kernel/`, which now supersedes the spec.

## Suggested future classifier rule

When an artifact's domain is `ORACLE_GOVERNANCE` AND the artifact contains version-numbered language (`v8`, `v9.0`, `v9.1`, etc.), the classifier MUST:
1. Tag as `version_pinned: true` with the explicit version string preserved.
2. Emit a `supersession_check_required: true` flag — a downstream MAYOR-routed pass must compare the version-pinned spec to current SOT and produce one of {SUPERSEDED / PARTIALLY_PRESERVED / FULLY_PRESERVED}.
3. Refuse to extract API specs / endpoint definitions as `RECEIPT_CANDIDATE` until the supersession check returns `FULLY_PRESERVED` — otherwise the receipt would bind to abstractions that no longer exist.

This is the load-bearing rule for the entire ORACLE-family corpus: the operator's 3-year archive is **versioned**, and naive promotion would import historically-deprecated abstractions as if they were current canon.
