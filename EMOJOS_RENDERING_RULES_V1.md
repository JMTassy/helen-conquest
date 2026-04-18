# EMOJOS_RENDERING_RULES_V1

---

## A. Scope

This document defines the rendering contract for EMOJOS — the expressive visual layer of HELEN OS.

It governs:

- state palette (decision and validation states),
- agent palette (role-identity markers),
- severity palette (signal intensity),
- House / faction / project palette,
- rendering rules (how structured state becomes visual output),
- forbidden ambiguity rules (what EMOJOS may never do),
- 20 canonical render examples.

**Law: EMOJOS is a downstream projection of typed state. It is never upstream authority.**

This document does not define:

- WUL grammar or semantics,
- kernel admissibility,
- routing policy,
- ledger truth.

---

## B. Core Law

```
WUL decides structure.
Kernel decides admissibility.
EMOJOS decides presentation.
```

Corollaries:

- An emoji cannot change the meaning of a WUL expression.
- A visual emphasis cannot alter a routing or reducer decision.
- A decorative overlay cannot upgrade a claim, receipt, or witness state.
- Rendered output is not canonical source unless separately receipted.

---

## C. Renderer Input Contract

The renderer must receive one of the following typed inputs:

1. A typed IR object from WUL compilation
2. A kernel event object
3. A ledger event object
4. A validated policy or status object

The renderer must not:

- infer state from emoji or ornament,
- accept natural language as input,
- accept raw WUL source as input (IR only),
- produce renders that introduce semantics not present in the input object.

---

## D. State Palette

The state palette is the primary decision-state vocabulary.

Each icon is bound to exactly one semantic state. Cross-binding is forbidden.

| Icon | State | Applies To |
|---|---|---|
| 🟢 | PASS / AUTHORIZED / VERIFIED / ADMISSIBLE / SEALED | Gates, verdicts, claims, artifacts |
| 🔴 | FAIL / REJECTED / BLOCKED / INVALID | Gates, verdicts, schemas, artifacts |
| 🟡 | HOLD / DEFERRED / PENDING / STAGED | Verdicts, pipeline positions |
| 🔵 | COMPILING / BUILDING / RUNNING | WUL compilation, build pipeline |
| 🟣 | SYNCING / FEDERATING / PROPAGATING | Cross-town, federation events |
| ⚪ | UNKNOWN / UNCLASSIFIED | Artifacts without assigned state |
| 🔒 | QUARANTINED | Claim nodes, Temple artifacts, wild_text |
| ⚰️ | SEALED (irrevocable) | Final ledger entries, law inscriptions |

### D.1 Binding Rules

- 🟢 binds to: PASS, AUTHORIZED, VERIFIED, ADMISSIBLE, SEALED (soft)
- 🔴 binds to: FAIL, REJECTED, BLOCKED, INVALID, SCHEMA_INVALID
- 🟡 binds to: HOLD, DEFERRED, PENDING, STAGED, AWAITING_WITNESS
- 🔵 binds to: active computation states only
- 🟣 binds to: federation and cross-town propagation states only
- 🔒 binds to: QUARANTINED exclusively — never to other states
- ⚰️ binds to: irrevocable ledger commits only

### D.2 Ambiguity Prohibition

- 🟢 may not be used to mean "good feeling" or "positive sentiment"
- 🔴 may not be used to mean "danger" or "urgency" outside of FAIL/REJECTED states
- 🟡 may not be used to mean "caution" — only HOLD/DEFERRED/STAGED
- 🔒 may not be used decoratively; it carries exactly QUARANTINED
- ⚰️ may not be used humorously or decoratively; it carries irrevocable seal

### D.3 Monitoring State Palette (Operational Health)

The monitoring palette reports live operational health of active system domains. It reuses the three primary color circles but in a strictly separated context: **the subject is a live domain, not a gate verdict or claim state.**

**Disambiguation law: a render is a monitoring render if and only if it carries a domain marker (Section D.3.1). A render is a decision render if it carries no domain marker. These two contexts are mutually exclusive. No compound render may mix decision state with monitoring state.**

| Icon | Monitoring State | Meaning |
|---|---|---|
| 🟢 | STABLE | Domain operating within normal parameters |
| 🟡 | RISING | Domain showing elevated signal; not yet blocking |
| 🔴 | CRITICAL | Domain in critical condition; requires intervention |

#### D.3.1 Domain Markers

Each monitored domain has a fixed composite marker. The marker identifies the domain, not any individual agent instance.

| Domain | Marker | Composite |
|---|---|---|
| Kernel | 🛡️⚖️ | Sentinel + Mayor |
| Orchestration | 🌀📜 | HELEN + Archivist |
| Receipts | 📝🔒 | Record + Lock |
| Governance | 👑⚔️ | Crown + Adversary |
| Simulation | 🎮🧬 | Game + Biology |
| Authority | ✝️🜃 | Cross + Alchemical |

#### D.3.2 Monitoring Render Format

```
{domain_marker} {monitoring_state_icon} {DOMAIN_NAME}: {MONITORING_STATE}
```

Examples:
```
🛡️⚖️ 🔴 KERNEL: CRITICAL
🌀📜 🟢 ORCHESTRATION: STABLE
📝🔒 🟢 RECEIPTS: STABLE
👑⚔️ 🟢 GOVERNANCE: STABLE
🎮🧬 🟡 SIMULATION: RISING
✝️🜃 🟢 AUTHORITY: STABLE
```

#### D.3.3 Binding Rules

- Domain markers appear only in monitoring renders
- Monitoring state icons (STABLE / RISING / CRITICAL) appear only after a domain marker
- A monitoring render must include exactly one domain marker and exactly one monitoring state icon
- Domain markers are not agent icons and are not subject to Section E binding rules
- The absence of a domain marker in any render containing 🟢 / 🟡 / 🔴 means the icon is bound to Section D.1 (decision state)

---

## E. Agent Palette

Each agent role has a fixed visual marker. The marker identifies role, not individual instances.

| Icon | Agent | Role |
|---|---|---|
| 🌀 | HELEN | Cognitive synthesizer, proposer, non-sovereign |
| ⚖️ | MAYOR | Deterministic adjudicator, sovereign reducer |
| 👁️ | HAL | Adversarial auditor, authority-bleed scanner |
| ⏳ | CHRONOS | Temporal guardian, replay manager |
| 🔨 | BUILDER | Construction, POC factory |
| 📜 | ARCHIVIST | Memory keeper, append-only ledger |
| 🏛️ | SENATOR / SENATE | Deliberative body |
| 🛡️ | SENTINEL | Federation gate guard |
| 🔬 | SCIENTIST | Formal exploration, Research District |
| ⚔️ | ADVERSARY | Stress testing, assumption breaking |

### E.1 Binding Rules

- Agent icons appear only in renders that include an identified agent role
- Agent icon always precedes the state icon in compound renders
- An agent icon alone does not imply a state

### E.2 Compound Agent + State Format

```
{agent_icon} {state_icon} {LABEL}
```

Example:
```
⚖️ 🟢 MAYOR AUTHORIZED
```

---

## F. Severity Palette

Severity marks the signal intensity of an event, independent of pass/fail.

| Icon | Severity | Meaning |
|---|---|---|
| (none) | NORMAL | Standard operation, no elevated signal |
| ⚠️ | WARNING | Elevated attention required; not yet blocking |
| 🚨 | BREACH | Invariant violation or security event |
| 🔒 | QUARANTINE | Containment active (state change) |
| 👁️ | WITNESS REQUIRED | Second witness mandate triggered |
| ✅ | WITNESSED | Second witness granted |
| ⚰️ | SEALED | Irrevocable finality |

### F.1 Severity + State Compound Format

```
{severity_icon} {state_icon} {LABEL}
```

Example:
```
⚠️ 🟡 HOLD — SECOND WITNESS PENDING
```

---

## G. House / Faction / Project Palette

House and faction markers identify organizational or project-level provenance. They are not states or verdicts.

| Icon | Entity | Context |
|---|---|---|
| 🌹 | Creative Wild | Creative Wild Quarter, WILD District |
| 🏰 | Oracle Citadel | Oracle Quarter, governance core |
| 🛕 | Temple Sandbox | Temple Sandbox routing regime |
| 🌲 | Factory / Builder | Factory District, POC construction |
| 🌐 | Federation | Cross-town, multi-town events |
| 📡 | Research | Research District, claim ingestion |
| 🎭 | Public / Marketing | Public and Economic District |

### G.1 Binding Rule

House icons appear only as prefix tags on artifact labels or section headers. They do not encode state.

---

## H. Rendering Rules

### H.1 Render derivation

All renders must be derived from a typed input object. The rendering function is:

```
render(state_object) → visual_string
```

Not:

```
render(intuition) → visual_string
```

### H.2 Compound render format

Standard compound render format:

```
{house_icon?} {agent_icon?} {severity_icon?} {state_icon} {LABEL}
```

- Optional fields are omitted if not present in the input object
- Order is fixed: house → agent → severity → state → label
- No reordering permitted

### H.3 Label formatting

- Labels are uppercase
- Labels use underscores for multi-word names
- Labels match the exact state name from the input object

### H.4 No free emoji

Outside of compound renders derived from typed input:

- No decorative emoji in canonical render positions
- No emoji that implies state without a typed backing
- No emoji in error messages or schema validation outputs (those are machine-readable strings)

### H.5 Downstream only

All renders are final output. They may not be:

- fed back into the compiler as input,
- used as canonical references in receipts or ledger entries,
- treated as evidence of any state they depict.

---

## I. Forbidden Ambiguity Rules

The following uses are strictly forbidden:

| Forbidden Use | Reason |
|---|---|
| 🟢 used for aesthetic approval | Binds exclusively to PASS/VERIFIED/AUTHORIZED |
| 🔴 used for danger/urgency outside FAIL | Cross-binding corrupts vocabulary |
| 🟡 used for caution without HOLD/DEFERRED state | Ambiguity collapses triage |
| 🔒 used decoratively | Quarantine is a machine state, not an ornament |
| ⚰️ used humorously | Seal is irrevocable; humorous use erodes signal |
| Agent icon without role context | Implies false attribution |
| Severity icon without severity in input object | Invents signal not present in state |
| House icon encoding state | House is provenance only, not verdict |
| Two state icons in same compound | Only one primary state per render |
| Emoji-only render (no label) | Labels are required for machine parsing |

---

## J. 20 Canonical Render Examples

These are the normative reference renders. All EMOJOS implementations must produce output consistent with these.

| # | Input Object (abbreviated) | Canonical Render |
|---|---|---|
| 01 | `{type: GateEvaluated, gate: SCHEMA, decision: PASS}` | `🟢 SCHEMA VALID` |
| 02 | `{type: GateEvaluated, gate: SCHEMA, decision: FAIL}` | `🔴 SCHEMA INVALID` |
| 03 | `{type: GateEvaluated, gate: CLAIM_INGESTION, decision: PASS}` | `🟢 GATE PASS — CLAIM_INGESTION` |
| 04 | `{type: GateEvaluated, gate: CLAIM_INGESTION, decision: FAIL}` | `🔴 GATE FAIL — CLAIM_INGESTION` |
| 05 | `{type: ClaimClassified, admissibility: ADMISSIBLE, tier: I}` | `🟢 CLAIM ADMISSIBLE [TIER I]` |
| 06 | `{type: ClaimClassified, admissibility: QUARANTINED, kind: wild_text}` | `🔒 WILD_TEXT QUARANTINED` |
| 07 | `{type: ClaimClassified, admissibility: QUARANTINED, tier: III}` | `🔒 CLAIM QUARANTINED [TIER III]` |
| 08 | `{agent: MAYOR, verdict: AUTHORIZED}` | `⚖️ 🟢 MAYOR AUTHORIZED` |
| 09 | `{agent: MAYOR, verdict: REJECTED}` | `⚖️ 🔴 MAYOR REJECTED` |
| 10 | `{agent: MAYOR, verdict: DEFERRED}` | `⚖️ 🟡 MAYOR DEFERRED` |
| 11 | `{agent: HAL, verdict: PASS}` | `👁️ 🟢 HAL PASS` |
| 12 | `{agent: HAL, verdict: WARN, reasons: [...]}` | `👁️ ⚠️ HAL WARN` |
| 13 | `{agent: HAL, verdict: BLOCK, required_fixes: [...]}` | `👁️ 🔴 HAL BLOCK` |
| 14 | `{type: SecondWitnessRequired, artifact_id: ...}` | `👁️ 🟡 SECOND WITNESS REQUIRED` |
| 15 | `{type: SecondWitnessReceipt, verdict: AUTHORIZED}` | `👁️ ✅ WITNESS AUTHORIZED` |
| 16 | `{type: SecondWitnessReceipt, verdict: REJECTED}` | `👁️ 🔴 WITNESS REJECTED` |
| 17 | `{agent: HELEN, mode: CORE, action: PROPOSAL}` | `🌀 HELEN PROPOSAL [CORE]` |
| 18 | `{type: FederationSync, status: PROPAGATING}` | `🟣 FEDERATION SYNCING` |
| 19 | `{type: LedgerEvent, event: SEAL_INSCRIBED}` | `⚰️ LEDGER SEALED` |
| 20 | `{type: WULCompile, status: COMPILING, source_hash: ...}` | `🔵 WUL COMPILING` |

---

## K. EMOJOS in the Full Stack

```
Natural language          → optional authoring layer
WUL V3 Core              → lexical / grammatical trust layer
WUL-ML V2               → typed symbolic metalanguage
IR / contracts           → deterministic executable meaning
HELEN OS kernel          → gate / reducer / ledger sovereignty
EMOJOS / EMOWUL         → expressive human-facing rendering
```

EMOJOS is the terminal layer. It receives, it renders, it does not feed back.

---

## L. Freeze Order for EMOJOS Extension

If additional palettes are introduced, they must be added in this order:

1. State additions (highest impact — must not conflict with D)
2. Agent additions (medium impact — must be role-distinct)
3. Severity additions (low impact — must not overlap with state icons)
4. House/faction additions (lowest impact — provenance only)

Each addition requires an explicit version bump and must be documented with:

- the new icon,
- its exclusive binding,
- the forbidden ambiguities it introduces.

---

**Document Version**: EMOJOS_RENDERING_RULES_V1
**Status**: FROZEN
**Depends on**: WUL V3 Core, WUL-ML V2, HELEN OS kernel event schema
