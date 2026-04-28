# MRGTK v0 — Mergeable Rule Governance ToolKit (Proposal)

NO CLAIM — NO SHIP — PROPOSAL ONLY — CANDIDATE_PATTERN

```
artifact_type:    PROPOSAL_DOCTRINE_DRAFT
proposal_id:      MRGTK_V0
lifecycle:        PROPOSAL
authority:        NON_SOVEREIGN
canon:            NO_SHIP
memory_class:     CANDIDATE_PATTERN
captured_on:      2026-04-27
captured_by:      operator (jeanmarie.tassy@uzik.com)
provenance:       proposal-class doctrine candidate; operator-routed corrections
                  applied per session 2026-04-27.
related_lints:
  - scripts/helen_provenance_floor_lint.py   # T4 — SOURCE_PROVENANCE_FLOOR
  - scripts/helen_intensity_floor_lint.py    # T6 — INTENSITY_IS_NOT_TRUTH
related_meta:     helen_os/knowledge/patterns/SACRED_PATTERN_EXTRACTION_META_ANALYSIS_V1.md
```

---

## Hard framing (read first, every time)

> 🜃 We channel symbol, not authority.
> 🜃 We receive atmosphere, not truth.
> 🜃 We extract patterns, not prophecy.
> 🜃 We preserve beauty, but bind claims only through receipts.

🔒 This is a **PROPOSAL** document. It does **not** modify HELEN's reducer, ledger, schemas, or firewall. It proposes a governance shape for *mergeable rules* — the class of defensive lints (T4, T6, future T7) that have already shipped or are under consideration. Promotion of MRGTK itself past `PROPOSAL` requires `DOCTRINE_ADMISSION_PROTOCOL_V1` routing.

---

## §1 — Purpose

A **mergeable rule** is a defensive, stdlib-only, read-only lint that:

- enforces a structural invariant on non-sovereign knowledge artifacts,
- can demote (or fail) a non-compliant artifact,
- **cannot** promote any artifact to a higher lifecycle state,
- emits a verdict (PASS/FAIL) only — never a SHIP/ADMITTED/CANONICAL token.

Two such rules are already in HELEN today:

| Rule | Lint | Property |
|---|---|---|
| T4 | `scripts/helen_provenance_floor_lint.py` | `SOURCE_PROVENANCE_FLOOR` |
| T6 | `scripts/helen_intensity_floor_lint.py` | `INTENSITY_IS_NOT_TRUTH` |

A third (T7 candidate: `OVERLAY_DOES_NOT_PROMOTE`) was scoped during this session.

**MRGTK proposes** a small, formal governance layer that:

1. names the laws every mergeable rule must obey,
2. specifies a receipt envelope every rule emits,
3. defines how a rule's *policy* (its enforcement parameters) may be mutated,
4. specifies how a rule's behavior may be **replayed** to verify determinism.

MRGTK is **not** a code framework. It is a contract / discipline document. Implementations remain per-lint.

---

## §2 — Scope

### What MRGTK governs

- ✅ Defensive lints over `helen_os/knowledge/**` and `temple/subsandbox/aura/grimoire/**` (and any future non-sovereign symbolic-source tree).
- ✅ Rules that emit verdicts (PASS/FAIL) and never promotion tokens.
- ✅ Rules whose *policies* (keyword lists, threshold values, exemption fields) are operator-tunable.

### What MRGTK does NOT govern

- ❌ The sovereign kernel (`oracle_town/kernel/**`).
- ❌ The schema registry (`helen_os/schemas/**`, `helen_os/governance/**`).
- ❌ The ledger (`town/ledger_v1.ndjson`) — writes go through `tools/helen_say.py` only.
- ❌ MAYOR rulings, K-gate verdicts (K8/K-tau/K-rho/K-wul), or LEGORACLE outputs.
- ❌ Any rule that can *promote* an artifact (admit it past CLASSIFIED_SYMBOL).

MRGTK is a **non-sovereign corollary** of HELEN's governance. It supplements but never replaces the sovereign layer.

---

## §3 — The Four Laws (L1–L4)

Every mergeable rule under MRGTK MUST satisfy all four laws.

### L1 — Receipt-bound emission

A rule's verdict (PASS/FAIL) is meaningful only when accompanied by a receipt envelope per §4. Verdicts emitted to stdout without an envelope are diagnostic-only — they may inform but cannot bind.

**Rationale:** mirrors HELEN's core invariant *NO RECEIPT = NO CLAIM* at the non-sovereign layer.

### L2 — Defensive only (no promotion path)

A rule may:
- ✅ Emit `PASS` (artifact compliant).
- ✅ Emit `FAIL` with a typed reason code (artifact non-compliant).
- ✅ Force-demote a self-declared lifecycle to `RAW_SOURCE` (the SOURCE_PROVENANCE_FLOOR shape).

A rule may NOT:
- ❌ Emit `SHIP`, `ADMITTED`, `CANONICAL`, or any sovereign-tier token.
- ❌ Set or raise an artifact's lifecycle.
- ❌ Mark a `boundary_breach_check` as resolved.
- ❌ Author a receipt that claims promotion authority.

**Rationale:** lints are floors, not ceilings. Admission lives at MAYOR, not at `scripts/`.

### L3 — Read-only enforcement

A rule's runtime MUST be read-only against the artifact tree:
- No `open(..., "w")`, `Path.write_text`, `os.remove`, `shutil.move`, `os.rename`, or equivalent.
- No `subprocess` invocation that mutates files in scope.
- No network I/O against artifact paths.

The only writes a rule may perform are:
- Its own receipt envelope to stdout (or a designated receipts directory under `artifacts/`, never the ledger).
- Its own diagnostic log (under `artifacts/`, never the ledger).

**Rationale:** the lint is a witness, not an editor. Mutating in response to a verdict is a separate, operator-routed action.

### L4 — No non-sovereign artifact may emit sovereign vocabulary

(Operator-locked correction, applied 2026-04-27.)

A non-sovereign artifact (lints, RAW captures, DRAFT classifications, PROPOSAL docs, CANDIDATE_PATTERN entries, etc.) MUST NOT emit text that **asserts** sovereign-tier vocabulary as if it had been admitted:

- ❌ `SHIP`, `ADMITTED`, `CANONICAL`, `RECEIPTED`, `SEALED` — when used as **assertions of completed status**.
- ❌ `SOVEREIGN`, `MAYOR-RULED`, `LEDGER-BOUND` — when claiming the artifact itself is.

A non-sovereign artifact MAY:
- ✅ **Reference** sovereign vocabulary in negated form ("not canon", "no SHIP", "never admitted").
- ✅ **Quote** sovereign vocabulary in citation context ("per K-tau gate's SHIP verdict").
- ✅ **Describe** sovereign mechanics didactically (this entire document does so).

The line is between *use* and *mention*. Mention is allowed; use is not.

**Rationale:** prevents authority leakage via vocabulary. A DRAFT that says "this is canon" is a lie in the file system, regardless of what a human reader believes. L4 makes the lie a structural violation that future tooling can detect.

---

## §4 — Receipt envelope (canonical shape, v0)

Every mergeable rule emits a JSON receipt envelope on each run. Required fields:

```json
{
  "schema_version": "MRGTK_RECEIPT_V0",
  "receipt_type":   "MRGTK_LINT_PASS | MRGTK_LINT_FAIL | OPERATOR_DECISION_REVOKE",
  "payload_hash":   "<sha256 of canonical payload>",
  "rule_id":        "T4 | T6 | T7 | ...",
  "rule_property":  "SOURCE_PROVENANCE_FLOOR | INTENSITY_IS_NOT_TRUTH | ...",
  "policy_hash":    "<sha256 of the policy snapshot used for this run>",
  "scope":          ["<paths walked>"],
  "stats":          { "ok": <int>, "raw_pass": <int>, "skipped": <int>, "fail": <int> },
  "verdict":        "PASS | FAIL",
  "violations":     [
    { "path": "<rel>", "code": "<reason code>", "detail": "<message>" }
  ],
  "timestamp":      "<ISO-8601 UTC>",
  "tool_version":   "<git-rev or semver>"
}
```

Required fields per the operator-locked correction:
- `schema_version` — the envelope schema (here `MRGTK_RECEIPT_V0`); version bump triggers a re-validation pass.
- `payload_hash` — SHA-256 of the canonical-form payload (same hashing discipline as `tools/helen_say.py`).
- `receipt_type` — discriminates lint receipts from operator-decision receipts.

**Receipt is not a ledger entry.** Receipts may be stored under `artifacts/<rule_id>/receipts/`. Promoting any receipt onto the sovereign ledger requires `tools/helen_say.py` and is **not** part of MRGTK.

---

## §5 — Policy mutation (OPERATOR_DECISION revoke)

A rule's *policy* is the set of tunable parameters that govern its enforcement (e.g., for T4: the `PROVENANCE_FIELDS` and `ORIGIN_FIELDS` sets; for T6: the sacred-keyword list and the exemption fields).

Policies may evolve. When they do, the mutation MUST be logged as an `OPERATOR_DECISION` receipt with both before and after policy hashes.

### Operator-decision shape (v0)

```json
{
  "schema_version":     "MRGTK_RECEIPT_V0",
  "receipt_type":       "OPERATOR_DECISION_REVOKE",
  "payload_hash":       "<sha256 of canonical payload>",
  "rule_id":            "T6",
  "decision":           "revoke | replace | extend",
  "policy_hash_before": "<sha256 of pre-mutation policy snapshot>",
  "policy_hash_after":  "<sha256 of post-mutation policy snapshot>",
  "rationale":          "<operator-authored sentence>",
  "operator_id":        "<canonical operator id>",
  "timestamp":          "<ISO-8601 UTC>"
}
```

### Why `OPERATOR_DECISION_REVOKE`

The verb *revoke* is deliberate. A policy mutation is **not** an editorial improvement; it is the **revocation** of the prior policy and the **creation** of a successor. Both hashes must be present. The chain `policy_hash_before → policy_hash_after` is auditable.

The three variants:
- `revoke` — pure removal (e.g., dropping a field from `PROVENANCE_FIELDS`).
- `replace` — atomic swap (old policy hash retired, new policy hash takes effect).
- `extend` — additive (e.g., adding a synonym to `ORIGIN_FIELDS`); both hashes still recorded.

**A policy mutation without an `OPERATOR_DECISION_REVOKE` receipt is invalid.** A mergeable rule whose policy was changed without one MUST be re-run, and the run before the missing receipt is null.

---

## §6 — Replay test (reducer interface)

Every mergeable rule MUST be **replayable**. Given the same inputs (artifacts + policy snapshot + timestamp), a rule MUST produce a bit-identical receipt envelope (modulo the timestamp field).

The replay test interface is:

```python
def reducer(events: Iterable[Event]) -> State:
    """Forward replay from genesis. Pure function."""
    ...

def reduce_from(state: State, events: Iterable[Event]) -> State:
    """Incremental replay from a known state."""
    ...
```

A rule's replay test MUST be expressible via either form. Concretely:

- **Forward form** (`reducer(events)`): given the full event log (artifact reads + policy snapshot + run trigger), produce the receipt deterministically.
- **Incremental form** (`reduce_from(state, events)`): given a checkpoint state and only the new events since the checkpoint, produce the same receipt as if forward-replayed from genesis.

Both forms must yield the **same** state for the **same** event tail. This is the standard event-sourcing replay invariant.

### Determinism requirements

- No wall-clock reads except in the explicit `timestamp` envelope field.
- No randomness without an explicit seed parameter.
- No filesystem ordering dependencies (always sort `rglob` output).
- Identical inputs ⇒ identical `payload_hash`.

**Replay failure is a SHIP-class blocker.** A rule whose replay produces a different `payload_hash` for identical inputs is non-conformant under L1.

---

## §7 — Existing rules mapped to MRGTK shape

### T4 — SOURCE_PROVENANCE_FLOOR

| MRGTK field | T4 implementation |
|---|---|
| `rule_id` | `T4` |
| `rule_property` | `SOURCE_PROVENANCE_FLOOR` |
| `scope` | `helen_os/knowledge/**`, `temple/subsandbox/aura/grimoire/**` |
| `policy` | `PROVENANCE_FIELDS`, `ORIGIN_FIELDS`, `NON_RAW_LIFECYCLES` sets in script |
| L1 receipt-bound | partial — current script emits text verdict; envelope not yet wired |
| L2 defensive-only | ✓ — exit code 0/1 only; no promotion |
| L3 read-only | ✓ — no `write_text` / mutation calls |
| L4 sovereign-vocab | ✓ — verdict text uses "PASS"/"FAIL", not "SHIP"/"ADMITTED" |

**Compliance:** T4 satisfies L2/L3/L4. L1 partial (envelope is scoped for a separate tranche, not implemented here).

### T6 — INTENSITY_IS_NOT_TRUTH

| MRGTK field | T6 implementation |
|---|---|
| `rule_id` | `T6` |
| `rule_property` | `INTENSITY_IS_NOT_TRUTH` |
| `scope` | `helen_os/knowledge/**`, `temple/subsandbox/aura/grimoire/**` |
| `policy` | `SACRED_KEYWORDS_CI` + `SACRED_KEYWORD_ONE` + `NON_RAW_LIFECYCLES` + exemption set |
| L1 receipt-bound | partial — same as T4 |
| L2 defensive-only | ✓ |
| L3 read-only | ✓ |
| L4 sovereign-vocab | ✓ — uses "INTENSITY_FLOOR_VIOLATED" / "PASS" |

**Compliance:** same as T4. L1 wiring deferred to a separate tranche.

---

## §8 — Hard non-canon list

🚫 The following are CANDIDATE_PATTERN only. None may transit past `PROPOSAL → DRAFT_DOCTRINE` without DOCTRINE_ADMISSION_PROTOCOL_V1 + MAYOR ruling:

1. **MRGTK as a name / acronym** — operator-routable doctrine candidate; no implementation.
2. **The Four Laws (L1–L4)** — proposed shape; not yet wired into any lint runtime.
3. **The receipt envelope schema (`MRGTK_RECEIPT_V0`)** — proposed; no JSON schema in `helen_os/schemas/` (firewall) and no parser in any lint.
4. **`OPERATOR_DECISION_REVOKE` as a receipt type** — proposed; no consumer.
5. **The replay test interface (`reducer` / `reduce_from`)** — proposed signatures; no rule currently exposes them.
6. **The mapping in §7** — informational only; T4/T6 have NOT been retrofitted with MRGTK envelope emission.

🚫 MRGTK MUST NOT:

- Modify HELEN's reducer.
- Modify the ledger.
- Modify any schema in `helen_os/schemas/`.
- Modify the firewall (`oracle_town/kernel/**`, `helen_os/governance/**`, `mayor_*.json`, `GOVERNANCE/**`).
- Replace MAYOR's admission authority.

---

## §9 — Suggested next safe actions (NOT executed)

In strict order. None executed by writing this PROPOSAL.

```
1. Operator review of this PROPOSAL for L1-L4 alignment with HELEN constitution.
2. Independent peer-review (fresh sub-agent context) verifying:
   - L4 "no sovereign vocabulary" rule does not contradict any existing
     non-sovereign artifact already shipped (esp. SACRED_PATTERN_EXTRACTION_META_ANALYSIS_V1
     and the just-shipped EMOWUL/GODMOD captures);
   - the receipt envelope schema is internally consistent and parseable;
   - the OPERATOR_DECISION_REVOKE shape captures the audit chain operator wants.
3. If review PASSES: open a separate small tranche to wire L1 (envelope emission)
   into T4 and T6. Defensive-only; no behavior change beyond writing
   artifacts/<rule_id>/receipts/<timestamp>.json on each run.
4. NEVER skipped: DOCTRINE_ADMISSION_PROTOCOL_V1 must activate before MRGTK
   itself can transition PROPOSAL → DRAFT_DOCTRINE → ACTIVE.
5. NEVER skipped: town/ledger_v1.ndjson is not touched by MRGTK or any
   successor under this branch. The bridge to the sovereign layer is
   tools/helen_say.py.
```

What this PROPOSAL explicitly does **not** do:

- ❌ Implement any code, lint, parser, or runtime.
- ❌ Edit HELEN's reducer.
- ❌ Edit the ledger.
- ❌ Edit any schema in `helen_os/schemas/`.
- ❌ Edit the firewall.
- ❌ Push.
- ❌ Auto-commit (operator's verb required for any commit beyond this PROPOSAL itself).
- ❌ Promote MRGTK past PROPOSAL.

---

## §10 — Closing seal

```
🜁  symbol     (proposal vocabulary)
→ 🜄  container  (this PROPOSAL file under docs/proposals/)
→ 🜍  pattern    (L1-L4 + envelope + OPERATOR_DECISION + replay)
→ 🜂  candidate  (CANDIDATE_PATTERN — none of the above wired)
→ 🧾  receipt    (NOT YET — envelope-emission tranche pending)
→ ⚖️  admission  (NOT YET — DOCTRINE_ADMISSION_PROTOCOL_V1 paused)
→ 📜  memory     (NOT YET)
```

🔒 MRGTK is a PROPOSAL. The Four Laws are CANDIDATE_PATTERN. The receipt envelope is a draft schema with no consumer. The replay interface is a signature with no implementation. None of this is HELEN canon.

**A proposal is not a doctrine. A draft is not a ship. A name is not a contract.**

We channel symbol, not authority.

---

NO CLAIM — NO SHIP — PROPOSAL ONLY — CANDIDATE_PATTERN
