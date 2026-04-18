# Oracle Town: 5 Essential Questions

These questions determine whether a proposed change, feature, or integration is compatible with Oracle Town's governance model.

---

## Question 1: Does this introduce text-based authority?

**What to check:**
- Does any natural language output influence SHIP/NO_SHIP decisions?
- Does any prose, log message, or comment carry implicit authority?
- Can an agent's "reasoning" override receipt requirements?

**Red flags:**
- "The model concluded it was safe to ship"
- "Based on analysis, we recommend proceeding"
- "Confidence score exceeds threshold"

**Pass condition:**
Only `Mayor(policy, briefcase, ledger)` produces decisions. All upstream text is non-authoritative.

---

## Question 2: Can this bypass the receipt requirement?

**What to check:**
- Does a SHIP path exist that doesn't require signed attestations?
- Can obligations be satisfied by anything other than cryptographic proof?
- Is there an "emergency override" or "admin bypass"?

**Red flags:**
- "Skip attestation for trusted sources"
- "Auto-approve if tests pass" (without signed receipt)
- "Manual override button"

**Pass condition:**
NO_RECEIPT = NO_SHIP. No exceptions. No shortcuts. No overrides.

---

## Question 3: Is authority separation preserved?

**What to check:**
- Can any single component both propose AND decide?
- Can Creative Town / Swarm outputs influence Mayor directly?
- Can Factory modify the briefcase or policy?

**Red flags:**
- CT outputs consumed by Mayor (without Intake filtering)
- Factory attestations that reference "should ship"
- Any component reading AND writing to decision artifacts

**Pass condition:**
- CT/Swarm: propose only
- Intake: filter only
- Factory: attest only
- Mayor: decide only

---

## Question 4: Is this deterministic and replayable?

**What to check:**
- Given identical inputs, will the same output always result?
- Are all artifacts canonicalized (JSON sort_keys, separators, UTF-8)?
- Do any decisions depend on timestamps, random values, or external state?

**Red flags:**
- `datetime.now()` in decision logic
- `random.choice()` anywhere in the pipeline
- LLM-generated verdicts (non-deterministic)
- Floating-point comparisons in satisfaction logic

**Pass condition:**
```
replay(policy, briefcase, ledger) × N → 1 unique decision_digest
```

---

## Question 5: Does this weaken fail-closed semantics?

**What to check:**
- What happens when validation fails? Does the system continue or halt?
- What happens when a required class is missing? Default to SHIP or NO_SHIP?
- What happens when signatures don't verify? Silent skip or hard reject?

**Red flags:**
- `except: pass` in validation code
- "Soft" failures that log but continue
- Default values that assume success
- "Best effort" attestation checking

**Pass condition:**
- Parse fails → REJECT
- Schema fails → REJECT
- Signature fails → REJECT
- Quorum fails → NO_SHIP
- Key revoked → NO_SHIP
- Evidence missing → NO_SHIP

Ambiguity → REJECT. Default → NO_SHIP.

---

## Quick Reference Matrix

| Proposal Type | Q1 | Q2 | Q3 | Q4 | Q5 |
|--------------|----|----|----|----|-----|
| New CT agent | Check authority language | N/A | Must stay non-sovereign | Must be filterable | N/A |
| New attestor class | N/A | Must require signatures | Must not decide | Canonical signing | Fail-closed on invalid |
| Swarm integration | No authority tokens | Handoff requires Intake | Swarm → CT only | SBD must be stable | Guardrails block handoff |
| Policy change | N/A | Must preserve NO_RECEIPT rule | Must be governed | Must pin hashes | Must not add overrides |
| Mayor modification | Zero text authority | Zero bypass paths | Decision only | Pure function | Fail-closed always |

---

## Usage

Before approving any PR, design doc, or integration:

1. Ask all 5 questions explicitly
2. Document the answers
3. If ANY answer is "no" or "unclear" → block until resolved
4. If all answers are "yes" with evidence → proceed

---

## Example: Evaluating "Add confidence scores to proposals"

| Question | Answer | Status |
|----------|--------|--------|
| Q1: Text authority? | Confidence scores are authority language | ❌ FAIL |
| Q2: Receipt bypass? | Could be used to skip attestation | ❌ FAIL |
| Q3: Authority separation? | Gives CT implicit decision power | ❌ FAIL |
| Q4: Deterministic? | N/A (blocked earlier) | — |
| Q5: Fail-closed? | N/A (blocked earlier) | — |

**Verdict:** REJECT. Confidence scores violate K0 (text has no authority).

---

## Example: Evaluating "Add new SECURITY attestor class"

| Question | Answer | Status |
|----------|--------|--------|
| Q1: Text authority? | No, attestors sign, don't decide | ✅ PASS |
| Q2: Receipt bypass? | No, adds more receipt requirements | ✅ PASS |
| Q3: Authority separation? | Attestors propose, Mayor decides | ✅ PASS |
| Q4: Deterministic? | Signatures are deterministic | ✅ PASS |
| Q5: Fail-closed? | Invalid SECURITY attestation → NO_SHIP | ✅ PASS |

**Verdict:** APPROVE. New attestor class strengthens governance.

---

**These 5 questions are the constitutional filter for Oracle Town.**
