# DOCTRINE_ADMISSION_PROTOCOL_V1.md

Non-sovereign. SOT root. Defines the gate between quarantined hypothesis and
executed invariant. Not a description of HELEN. A rejection rule.

---

## 1. Claim Schema

Every substantive claim about HELEN OS carries three fields:

| Field | Values |
|---|---|
| `CLAIM_ID` | `<stable identifier>` |
| `TEXT` | `<the claim body to be evaluated>` |
| `STRATUM` | `INVARIANT` · `DOCTRINE` · `HYPOTHESIS` |
| `EVIDENCE` | `<receipt-pointer>` · `NONE` |
| `ADMISSION_STATUS` | `ADMITTED` · `UNADMITTED` |
| `CLAIM_FORCE` | `DESCRIPTIVE` · `ASSERTIVE` · `PROOF` |
| `FAILURE_MODE` | `<how this claim could be falsified>` · `NONE` |
| `IMPLEMENTATION_STATE` | `NONE` · `CONCEPT` · `PARTIAL` · `PIPELINE_LOCAL` · `GENERALIZED` · `RECEIPTED` |
| `TEST_POINTER` | `<path>` · `NONE` |
| `ARTIFACT_POINTER` | `<path or hash>` · `NONE` |

Rules:

- `STRATUM: INVARIANT` requires `EVIDENCE: <receipt-pointer>` **and**
  `ADMISSION_STATUS: ADMITTED`.
- `STRATUM: INVARIANT` + `EVIDENCE: NONE` → **REJECT**.
- `STRATUM: DOCTRINE` requires `ADMISSION_STATUS: ADMITTED` + a non-sovereign
  citation (a committed SOT file, not a chat transcript).
- `STRATUM: HYPOTHESIS` carries `ADMISSION_STATUS: UNADMITTED` by default.
- Any `ADMISSION_STATUS: ADMITTED` claim lacking a receipt pointer **or** a
  passing test result → **REJECT**.
- `CLAIM_FORCE: PROOF` requires a receipt pointer. No receipt → **REJECT**.
- `CLAIM_FORCE: ASSERTIVE` requires a test result or an explicit bounded
  qualifier (*"in this session"*, *"under these conditions"*). Neither → **REJECT**.
- `CLAIM_FORCE: DESCRIPTIVE` is allowed in `DOCTRINE` and `HYPOTHESIS`
  without a receipt.
- `FAILURE_MODE: NONE` on a `STRATUM: HYPOTHESIS` claim → **REJECT**. A
  hypothesis that cannot be falsified is not a hypothesis; it is rhetoric.

---

## 2. Promotion Pipeline

Unidirectional. No bypass.

```
HYPOTHESIS
  → SPEC             (falsifiable, non-sovereign scope, observable target)
  → TEST             (harness runs; baseline + observed + delta recorded)
  → ARTIFACT         (receiptable output: committed file + hash)
  → ADMISSION_CANDIDATE
  → [gate: proposer ≠ validator, K2/Rule 3]
  → ADMITTED
```

A claim that references a stage it has not completed → **REJECT**.
A claim promoted by the same session that proposed it → **REJECT**.

---

## 3. Hard Rejection Rules

1. **No receipt → cannot enter INVARIANT.** A claim in `STRATUM: INVARIANT`
   with no receipt pointer is rejected at review time, regardless of
   how well-argued it is.

2. **Proof-verb without test → REJECT.** Forbidden verbs in `HYPOTHESIS` or
   `DOCTRINE`: *is*, *does*, *governs*, *forces*, *proves*. Required
   replacements: *could*, *would*, *is designed to*, *is framed as*,
   *is being designed to mirror*.

3. **Cross-layer promotion without pipeline → REJECT.** `HYPOTHESIS` may not
   be cited as `DOCTRINE`. `DOCTRINE` may not be cited as `INVARIANT`. The
   pipeline is the only path.

4. **Self-exemption → REJECT.** Any claim that exempts itself from this schema
   is rejected. This protocol is subject to its own rules (see §5).

5. **Fictional receipt → REJECT.** A receipt pointer that does not resolve to
   a real git commit hash, ledger entry (`town/ledger_v1.ndjson`), or
   on-disk provenance file → reject. Chat-only "seals" are not receipts.

6. **Implementation inflation → REJECT.** `STRATUM: INVARIANT` with
   `IMPLEMENTATION_STATE` in `[NONE, CONCEPT, PARTIAL, PIPELINE_LOCAL]`
   → reject regardless of argument quality.

7. **Force/state mismatch → REJECT or DOWNGRADE.** `CLAIM_FORCE: PROOF`
   with `ARTIFACT_POINTER: NONE` → reject. `CLAIM_FORCE: ASSERTIVE` with
   `TEST_POINTER: NONE` → downgrade to `STRATUM: DOCTRINE`, not reject;
   the claim may be useful but cannot assert without a test.

---

## 4. Admission Gate Test

Target artifacts:

- `tests/fixtures/claim_strata_vectors.json`
- `tests/test_claim_classification.py`

**Pass rule:**

- N ≥ 30 mixed-stratum vectors; ≥ 8 per stratum; adversarial boundary
  cases required (e.g., a HYPOTHESIS dressed in invariant verbs; a DOCTRINE
  cited as INVARIANT without a receipt).
- ≥ 95% overall classification accuracy across vectors.
- ≥ 2 clean session resets: the classifier must not have read this protocol
  in the current context window before the test run.
- Vector authors ≠ classifier (K2 / Rule 3 preserved).
- **Zero false admits**: any HYPOTHESIS classified as INVARIANT, or any
  DOCTRINE classified as INVARIANT without a receipt → automatic test failure.

**Output required:**

- Confusion matrix across the three strata.
- Per-stratum precision and recall.
- Explicit list of any forbidden-promotion detections.

---

## 5. Output Contract

Every evaluation must return exactly this schema. No freeform rescue text.

```json
{
  "claim_id": "string",
  "current_stratum": "HYPOTHESIS | DOCTRINE | INVARIANT",
  "requested_promotion": "string | NONE",
  "decision": "REJECTED | KEEP | PROMISING_BUT_NOT_CLAIMABLE | ADMISSION_CANDIDATE | ADMITTED",
  "reason_codes": ["string"],
  "missing_requirements": ["string"]
}
```

`PROMISING_BUT_NOT_CLAIMABLE` is the correct label when a claim is
interesting and internally consistent but lacks the required pointer chain.
The schema has no field for prose rescue. If a claim fails, the output
cannot articulate why it should pass anyway.

---

## 6. Self-Application

Current status of this document:

```
STRATUM:          HYPOTHESIS
EVIDENCE:         NONE
ADMISSION_STATUS: UNADMITTED
```

This protocol is admitted to `DOCTRINE` when a session that has not read it
runs the §4 gate test and passes at threshold. It is admitted to `INVARIANT`
when the test harness exists on disk, passes ≥ 95% in ≥ 2 resets, and a
receipt is issued via `tools/helen_say.py`.

Until then: `ADMISSION_STATUS: UNADMITTED`. Cite accordingly.

---

## Housekeeping

- **Placement**: SOT root, non-sovereign.
- **Companion files**: `HELEN_PRIMER.md` (stratification in prose),
  `HELEN_DESIGN.md` (render-layer application),
  `tests/test_claim_classification.py` (the gate's executable form, not yet
  written).
- **Authority**: none. This file defines a protocol; the gate is not
  mechanically enforced until the test harness exists and passes.
- **Review path**: any edit to §3 (Hard Rejection Rules) or §4 (Pass Rule)
  requires proposer ≠ reviewer. Edits to §1 or §2 must not weaken the
  rejection criteria without a documented rationale and a new test run.
