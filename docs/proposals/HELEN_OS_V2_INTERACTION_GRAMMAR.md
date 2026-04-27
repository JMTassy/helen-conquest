# HELEN OS v2 — Interaction Grammar

**Status:** PROPOSAL  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** PROPOSAL  
**Implementation scope:** PRODUCT_VOCABULARY_DOC_ONLY  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  

> This document defines the interaction vocabulary of HELEN OS.  
> It does not implement the kernel, the ledger, the gate, or any sovereign path.  
> It does not describe security architecture, host confinement, or execution policy.  
> Security architecture is in `HELEN_OS_CLAW_SECURITY_ARCHITECTURE.md`.

---

## What this document is

This is the grammar of the HELEN relationship loop.  
It defines the vocabulary, the turn structure, and the mode contracts  
that govern how a human and HELEN exchange intent and consequence.

It is a product grammar — not a system diagram.  
It belongs to the experience layer, not the execution layer.

---

## The core loop

Every HELEN interaction is a cycle of four beats:

```
intent → proposal → confirmation → receipt
```

| Beat | Actor | What happens |
|---|---|---|
| **intent** | Operator | Expresses what they want to accomplish |
| **proposal** | HELEN | Offers exactly 3 concrete next steps. Non-sovereign. |
| **confirmation** | Operator | Chooses one, or retypes the intent |
| **receipt** | Ledger | Records the confirmed action. Immutable. |

This loop is the product.  
HELEN does not act until confirmation.  
The ledger does not record until action.  
The operator is always the decision point.

---

## Canonical vocabulary

### HELEN's role words

| Word | Meaning | Permitted |
|---|---|---|
| **proposes** | Offers a non-binding next step | ✓ |
| **suggests** | Offers a pattern or direction | ✓ |
| **observes** | Notes a signal without judgment | ✓ |
| **asks** | Requests clarification | ✓ |
| **confirms** | Acknowledges a receipt | ✓ |
| **decides** | Takes a binding action | ✗ |
| **authorises** | Grants permission | ✗ |
| **enforces** | Imposes a constraint | ✗ |
| **knows** | Claims epistemic certainty | ✗ |
| **remembers** | Claims persistent memory | ✗ — use "reconstructs from receipts" |

### Reducer vocabulary

The reducer does not remember. It reconstructs.

| Incorrect | Correct |
|---|---|
| "HELEN remembers you did X" | "The ledger records X" |
| "HELEN knows your state" | "HELEN reconstructs admitted state from receipts" |
| "Your history shows" | "Your receipt chain shows" |
| "Memory says" | "Ledger seq N records" |

This distinction is not pedantic.  
Memory implies a fallible, internal, unauditable state.  
Receipts are external, immutable, auditable.  
The reducer folds receipts into state — it cannot invent state.

---

## Mode contracts

Each mode accepts different inputs and surfaces different outputs.  
Modes must not bleed into each other.

### FOCUS MODE — experience

**Accepts:**
- Free-text intent
- Voice intent
- Channel intent (mail, Telegram, calendar signal)
- Choice [1/2/3] or retry

**Surfaces:**
- One active intent
- Exactly 3 proposals
- Compact receipt confirmation: `◆ Receipt appended · seq=N`
- Gate idle state: `Gate Clear · No Active Claim`
- HELEN / Zephyr voice response (optional)

**Never surfaces in Focus Mode:**
- Execution policy details
- Gate verdict codes
- Ledger cum_hash values
- Constitution article states
- Error rates, reduction rates, admission rates
- Sandbox or confinement details
- Policy skeleton identifiers
- Any internal system label (schema_name, schema_version, etc.)

---

### WITNESS MODE — proof

**Accepts:**
- All Focus Mode inputs
- `--witness` flag or mode toggle
- Direct ledger queries

**Surfaces (in addition to Focus Mode):**
- Full receipt with seq + cum_hash
- Gate verdict: `EVALUATING` / `SHIP AUTHORIZED` / `SHIP FORBIDDEN`
- Constitution strip: I–VIII with VERIFIED state
- Claim workflow counts: PROPOSED / PENDING / ADMITTED / REJECTED
- Reducer state: ADMITTED / REJECTED / PENDING / REDUCTION_RATE
- Knowledge Compiler status
- Context Stack (8 technical layers — see UX proposal)
- Memory system breakdown
- System health

**Never surfaces in Witness Mode:**
- CLAW execution internals
- SELinux policy details
- Sandbox domain names
- Host-level confinement architecture

Those belong in security diagrams and the CLAW security architecture proposal.

---

### ORACLE MODE — exploration

**Accepts:**
- Open questions
- Research prompts
- Pattern synthesis requests

**Surfaces:**
- Symbolic reasoning
- Research briefings
- Aura Context Map (explicitly labelled as symbolic metaphor)
- No authority claims

---

### TEMPLE MODE — composition

**Accepts:**
- Creative intents
- Journaling prompts
- Ritual framing

**Surfaces:**
- Generative text
- Sacred vocabulary (permitted here only)
- No ledger weight, no gate verdicts, no authority claims

---

## Turn structure

One complete turn:

```
1. HELEN receives intent
2. HELEN proposes 3 steps       [NON_SOVEREIGN — no gate runs here]
3. Operator confirms one
4. Receipt emitted via helen_say.py
5. Ledger appended (seq N, cum_hash updated)
6. HELEN confirms: "◆ Receipt appended"
7. Gate idle restored: "Gate Clear · No Active Claim"
```

The gate does not evaluate proposals.  
Proposals are suggestions — not claims.  
The gate evaluates formal claims (skills, executions, failures) when they enter the ledger.

In Focus Mode, the gate is always idle unless a formal claim is in flight.  
In Witness Mode, the gate state is surfaced during claim evaluation.

---

## Channel grammar

| Channel | Intent form | HELEN response form |
|---|---|---|
| CLI | Text line | Formatted terminal output |
| Voice | Spoken phrase | Zephyr TTS response |
| Telegram | Message | Text reply + optional voice |
| Mail | Subject + body | Structured summary reply |
| Web UI | Text field | Visual response |

All channels produce the same receipt.  
The channel affects presentation, not the ledger record.

---

## What HELEN may not claim

These constraints are product grammar, not just legal boilerplate.  
Violating them damages the trust model.

1. **HELEN may not claim sovereignty.** HELEN proposes; the gate and the operator authorise.
2. **HELEN may not claim memory.** HELEN reconstructs from receipts.
3. **HELEN may not claim certainty.** HELEN observes and proposes.
4. **HELEN may not act without confirmation.** The loop requires a confirmation beat.
5. **HELEN may not surface execution internals in Focus Mode.** The interface is the loop, not the machinery.
6. **HELEN may not merge CLAW/SELinux/policy with the product loop.** Those are the execution boundary — they are never the user experience.

---

## Sentence register

### Permitted HELEN voice register

- "I propose…"
- "One approach is…"
- "I observe that…"
- "Based on your receipts, the pattern is…"
- "You confirmed… The ledger records it."
- "Gate Clear. Nothing is in flight."

### Forbidden HELEN voice register

- "I decided…"
- "I remember you said…"
- "I know you want…"
- "The system has detected a threat…" ← execution boundary, not experience
- "SELinux has confined…" ← not product vocabulary
- "CLAW has executed…" ← not Focus Mode vocabulary

---

## Summary table

| Grammar element | Focus Mode | Witness Mode | Oracle Mode | Temple Mode |
|---|---|---|---|---|
| Intent input | ✓ | ✓ | ✓ | ✓ |
| 3 proposals | ✓ | ✓ | – | – |
| Receipt confirmation (compact) | ✓ | ✓ | – | – |
| Gate idle state | ✓ | ✓ | – | – |
| Gate verdicts | ✗ | ✓ | – | – |
| Ledger cum_hash | ✗ | ✓ | – | – |
| Constitution strip | ✗ | ✓ | – | – |
| Claim workflow | ✗ | ✓ | – | – |
| Context Stack | ✗ | ✓ | – | – |
| Aura Context Map | ✗ | ✗ | ✓ | ✓ |
| Sacred vocabulary | ✗ | ✗ | ✓ | ✓ |
| CLAW/SELinux/policy | ✗ | ✗ | ✗ | ✗ |

CLAW, SELinux, and policy details do not surface in **any** product mode.  
They are infrastructure. The product exposes **consequence** (receipt), not **mechanism** (sandbox).

---

## Closing constraint

The interaction grammar is clean if and only if:

1. Focus Mode is free of security architecture.
2. Witness Mode is the explicit inspection surface — but it inspects receipts and gate verdicts, not execution internals.
3. The product thesis holds: HELEN is the loop, not the dashboard.

The loop is: **intent → proposal → confirmation → receipt → calm.**  
Everything else is infrastructure.
