# EXAMPLE AMENDMENT: Evidence Thresholds for CLASS_II

**Amendment ID:** A-2026-06-001 (EXAMPLE - NOT YET PROPOSED)
**Proposed Date:** 2026-06-30 (projected, pending 90-day observation)
**Status:** PLANNING PHASE (no gates passed yet)

---

## AMENDMENT HEADER

**Title:** Tighten CLASS_II Evidence Threshold from "Some Evidence" to "Strong or Moderate Evidence"
**Doctrine Version:** 1.0 → 1.1
**Amendment Targets:** Section 1.2 (CLASS II — CONDITIONALLY GOVERNABLE)
**Ratification Deadline:** 2026-09-30 (90 days from proposal)

---

## WHAT CHANGES

### Before (Current Doctrine)
```
### 1.2 CLASS II — CONDITIONALLY GOVERNABLE

Definition: Decisions with partial evidence, some narrative elements,
validation possible but delayed, risk asymmetric but not fatal.

Oracle Town behavior: Often says NO until evidence improves. Accepts if
evidence threshold met.

Submission requirements:
- Some evidence must exist before commitment
- Narrative dependency allowed (but disclosed)
- Validation timeline explicit ("By Q2 2026, we will know...")
- Risk must be bounded (not existential)
- Reversibility must be explicit
```

### After (Proposed Change)
```
### 1.2 CLASS II — CONDITIONALLY GOVERNABLE

Definition: Decisions with partial evidence, some narrative elements,
validation possible but delayed, risk asymmetric but not fatal.

Oracle Town behavior: Often says NO until evidence improves. Accepts if
evidence is "strong" or "moderate" AND timeline is explicit.

Submission requirements:
- Evidence strength must be "strong" or "moderate" (not "weak")
- Narrative dependency allowed (but disclosed)
- Validation timeline explicit AND bound to ≤180 days
- Risk must be bounded (not existential)
- Reversibility must be "medium" or "high" (not "low")
```

### Why This Specific Wording?
**Key changes:**
1. "Some evidence" → "Strong or moderate evidence" (raises bar)
2. Timeline allowed but now capped at 180 days (prevents indefinite deferral)
3. Reversibility now requires medium/high (prevents irreversible bets from hiding as CLASS_II)

**Effect:** Reduces acceptance rate of CLASS_II submissions, prevents weak evidence from passing, ensures validation actually happens within reasonable window.

---

## GATE A: EVIDENCE PHASE

**Requirement:** ≥2 NPC claims + ≥90 days observation + ≥1 counterexample

### Evidence Requirement 1: AccuracyWatcher NPC Claim
**Source:** AccuracyWatcher
**Date Observed:** 2026-05-15
**Claim:** "CLASS_II submissions with 'weak' evidence are causing downstream problems. Of 8 CLASS_II ACCEPT verdicts in May, 4 failed by end-of-month (50% failure rate). CLASS_I submissions have 12% failure rate. CLASS_II weak-evidence is 4x worse than CLASS_I."
**Evidence:**
- May 2026: 8 CLASS_II submissions with evidence_strength="weak" → ACCEPT
- Follow-up June 2026: 4 of 8 failed (definition: outcome worse than expected)
- May 2026: 25 CLASS_I submissions → ACCEPT
- Follow-up June 2026: 3 of 25 failed (12% vs 50%)
- Pattern: Weak evidence in CLASS_II correlates with failure

### Evidence Requirement 2: PatternDetector NPC Claim
**Source:** PatternDetector
**Date Observed:** 2026-06-10
**Claim:** "CLASS_II acceptance is trending upward (March: 35%, April: 42%, May: 48%), suggesting acceptance discipline is drifting. Concurrent observation: Average evidence_strength declining (March: 60% moderate/strong, May: 40% moderate/strong). Evidence quality and acceptance rate moving in opposite directions."
**Evidence:**
- March 2026: 35% CLASS_II acceptance rate, 60% had moderate/strong evidence
- April 2026: 42% CLASS_II acceptance rate, 50% had moderate/strong evidence
- May 2026: 48% CLASS_II acceptance rate, 40% had moderate/strong evidence
- Trend: Weakening evidence selection criteria

### Evidence Requirement 3: Counterexample (Failed Case)
**Case:** Claim ID: claim_20260520_vendor_partnership_001
**Outcome:** ACCEPTED as CLASS_II (May 20, 2026), marked FAILED (June 18, 2026)
**Failure Details:**
- Submission: Vendor partnership with "weak" evidence (1 reference conversation, no contracts)
- Expected: "By Q2 2026, we'll know if partnership achieves $200k ARR"
- Reality: By June 15, vendor ghosted, no communication in 3 weeks, partnership dissolved
- Validation window: 26 days (not 90 days as submitted)
- Cost: $50k in sunk integration costs

**Why Current Doctrine Fails:**
- Current doctrine allows "some evidence" for CLASS_II
- This submission had exactly "some evidence" (1 conversation) and still passed
- Weak evidence created false confidence in timeline
- Reversibility wasn't enforced (costs were non-recoverable by month 2)

**How Proposed Amendment Fixes It:**
- Requires "strong" or "moderate" evidence (eliminates single-conversation submissions)
- Caps validation window at 180 days (prevents vague "by Q2" timelines)
- Requires reversibility disclosure (would flag that integration costs are sunk-cost irreversible)
- Same submission would be REJECTED under amended doctrine, preventing loss

### Observation Window
**Start Date:** 2026-03-30 (90 days before proposal)
**End Date:** 2026-06-28 (today)
**Total Duration:** 90 days exactly
**Data Points Collected:** 47 total verdicts analyzed, 18 CLASS_II submissions, 8 failed outcomes tracked

**Gate A Status:** ☐ PASS (AccuracyWatcher + PatternDetector + 1 counterexample + 90 days)

---

## GATE B: CONSERVATISM PHASE

**Question:** Why is inaction more dangerous than change?

**Default Assumption:** Keep current doctrine as-is. Burden on amendment to prove necessity.

### Analysis: Cost of Inaction
**If we do NOT amend:**
- Weak evidence will continue to slip through as CLASS_II, producing ~4 failed decisions per month (based on May pattern)
- At ~$50k cost per failure, inaction costs ~$200k/month in preventable mistakes
- Acceptance discipline will continue drifting (March: 35% → June: 48%), eroding selectivity
- CLASS_II will become indistinguishable from CLASS_III (narrative-driven bets)
- NPCs will have to propose same amendment again in 6 months with stronger evidence
- **Quantified cost of inaction:** $200k/month × 6 months = $1.2M in preventable failures

### Analysis: Risk of Amendment
**If we DO amend:**
- Legitimate CLASS_II submissions with moderate evidence might be discouraged (mild chilling effect)
- Some borderline decisions that would have passed under old doctrine will now REJECT
- 180-day validation cap might feel restrictive for decisions that truly need 365-day windows (e.g., year-long trials)
- Reversibility requirement might reject investments that are partly-reversible but costly to unwind
- **Risk:** We might over-reject, pushing good decisions to CLASS_III override path
- **Mitigation:** After 3 months, measure CLASS_II rejection rate. If >70%, revisit threshold

### Conservatism Test Result
**Decision:** Does burden of proof favor inaction or action?

✓ **INACTION IS MORE DANGEROUS** — Amendment is justified

**Reasoning:**
The data is clear: weak evidence in CLASS_II produces 4x higher failure rate (50% vs 12%). We have observed this over exactly 90 days across 47 verdicts with a concrete failed case. The cost of inaction is quantifiable ($200k/month) and growing. The risk of amendment is manageable (mild rejection rate increase) and reversible through normal amendment process. Conservatism test passes: preventing $200k/month in failures is worth risking some borderline rejections.

**Gate B Status:** ✓ PASS (Inaction is more dangerous than change)

---

## GATE C: RATIFICATION PHASE

**Question:** Do you commit to this amendment?

### Your Decision (PROJECTED - Not Yet Made)

For illustration, this is how a YES vote would be recorded:

✓ **RATIFY** — New doctrine version, old doctrine remains valid for historical claims

### Ratification Statement
> "I ratify this amendment because:
> 1. Evidence is compelling (two independent NPCs + 90 days + concrete counterexample)
> 2. Cost of inaction ($200k/month) exceeds risk of amendment (modest rejection rate increase)
> 3. Doctrine integrity is stronger with aligned evidence thresholds (CLASS_II threshold now clearly higher than CLASS_III narrative)
> 4. All May decisions remain valid under DOCTRINE_V1.0 (no retroactive reinterpretation)
> 5. This amendment is narrow (targets Section 1.2 only), reducing unintended side effects
>
> Effective immediately: all new CLASS_II submissions require 'strong' or 'moderate' evidence, with validation bounded to 180 days and reversibility of medium/high."

### Amendment Outcome (PROJECTED)
**Decision:** RATIFY (if evidence continues to hold through June 30)
**Timestamp:** 2026-06-30T09:00:00Z (projected)
**Hash:** [sha256 of complete amendment document]

**New Doctrine State:**
- **Old Version:** DOCTRINE_V1.0 (pinned to all claims created through 2026-06-30)
- **New Version:** DOCTRINE_V1.1 (effective 2026-07-01 for all new claims)
- **Transition:** Existing open CLASS_II submissions are re-evaluated under new evidence standard

**Gate C Status:** ☐ PENDING (Awaiting June 30 vote)

---

## AMENDMENT SUMMARY

| Gate | Status | Date |
|------|--------|------|
| A: Evidence | ☐ COLLECTING (will PASS by 2026-06-30) | 2026-03-30 → 2026-06-30 |
| B: Conservatism | ✓ PASS | 2026-06-28 |
| C: Ratification | ☐ PENDING | 2026-06-30 (projected) |

**Current State:**
- Evidence collection: **90/90 days** ✓
- Evidence claims: **2/2 NPCs** ✓
- Counterexample: **1/1** ✓
- Conservatism test: **PASS** ✓
- Ready for ratification: **Yes** (pending your vote)

---

## APPENDIX A: Historical Context

**Why This Amendment Was Proposed:**
- May 2026 saw unusual pattern: 50% failure rate on CLASS_II weak-evidence submissions vs 12% on CLASS_I
- PatternDetector flagged acceptance rate drift (March 35% → May 48%) with declining evidence quality
- Specific failure (vendor partnership, May 20) showed current doctrine inadequately protected against weak-evidence CLASS_II
- NPCs independently flagged same concern, triggering formal evidence collection

**When This Amendment Became Necessary:**
- May 15, 2026 (AccuracyWatcher alert about 50% failure rate)
- May 20, 2026 (vendor partnership failed, concrete counterexample)
- June 10, 2026 (PatternDetector formalized trend observation)

**Who Benefits from This Amendment:**
- **AccuracyWatcher**: Better ability to validate that refusals are working (fewer false accepts)
- **RiskAnalyzer**: More reliable override success rates (CLASS_III is actual speculation, not CLASS_II weakness)
- **Future you**: Protected from weak-evidence bets disguised as CLASS_II
- **The doctrine itself**: Clearer boundary between CLASS_II (partial evidence) and CLASS_III (narrative)

---

## APPENDIX B: Ledger Entry Format

```json
{
  "amendment_id": "A-2026-06-001",
  "doctrine_version_from": "1.0",
  "doctrine_version_to": "1.1",
  "sections_affected": ["Section 1.2 (CLASS_II — CONDITIONALLY GOVERNABLE)"],
  "timestamp_proposed": "2026-06-30T09:00:00Z",
  "timestamp_ratified": "2026-06-30T09:15:00Z",
  "observation_start": "2026-03-30T00:00:00Z",
  "observation_end": "2026-06-28T23:59:59Z",
  "observation_days": 90,
  "gate_a_npc_claims": 2,
  "gate_a_counterexamples": 1,
  "gate_a_result": "PASS",
  "gate_b_conservatism_verdict": "INACTION_MORE_DANGEROUS",
  "gate_b_result": "PASS",
  "gate_c_ratification_vote": "RATIFY",
  "gate_c_timestamp": "2026-06-30T09:15:00Z",
  "doctrine_v1_0_hash": "sha256:6ba9551d6a17551a04a719b6f1539b9bae772c72fbb86053d3470607fd68a709",
  "doctrine_v1_1_hash": "sha256:[to_be_computed]",
  "amendment_document_hash": "sha256:[amendment_A_2026_06_001.md]"
}
```

---

## IMMUTABLE RECORD

This amendment is a **planning document**, not yet ratified. Once ratified (if evidence holds through June 30), it will become immutable:

1. **This document** becomes locked (no edits)
2. **DOCTRINE_V1.1** created with hash and effective date
3. **DOCTRINE_V1.0** pinned to all claims created before 2026-07-01
4. **May/June decisions** remain valid under DOCTRINE_V1.0 (no retroactive harm)
5. **July 1+ decisions** use CLASS_II with higher evidence threshold
6. **Amendment precedent** available for future amendments

---

**Example Amendment Version:** 1.0
**Date:** January 31, 2026 (documented for reference)
**Status:** PLANNING EXAMPLE (shows how real amendment would progress)
**Note:** This is a planning exercise showing how Gate A, B, and C would work in practice. Actual amendment will be proposed only if evidence continues to support it through June 30, 2026.
