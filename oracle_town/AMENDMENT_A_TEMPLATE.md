# AMENDMENT PROPOSAL TEMPLATE

**Amendment ID:** A-[DATE]-[SEQUENCE]
**Proposed Date:** [YYYY-MM-DD]
**Status:** DRAFT / EVIDENCE PHASE / CONSERVATISM PHASE / RATIFICATION PHASE / ACCEPTED / REJECTED

---

## AMENDMENT HEADER

**Title:** [Concise name of change]
**Doctrine Version:** 1.0
**Amendment Targets:** [List sections: e.g., "Section 2 (Acceptance Rate Law)", "Section 8 (Can Be Amended)"]
**Ratification Deadline:** [≥90 days from today]

---

## WHAT CHANGES

### Before (Current Doctrine)
```
[Exact text from DOCTRINE_V1.0 being modified]
```

### After (Proposed Change)
```
[Exact proposed replacement text]
```

### Why This Specific Wording?
[Explain the semantic difference between before and after]

---

## GATE A: EVIDENCE PHASE

**Requirement:** ≥2 NPC claims + ≥90 days observation + ≥1 counterexample

### Evidence Requirement 1: NPC Claim #1
**Source:** [NPC name]
**Date Observed:** [YYYY-MM-DD]
**Claim:** [Exact claim text from NPC observation]
**Evidence:**
- [Specific data point 1]
- [Specific data point 2]
- [Specific data point 3]

### Evidence Requirement 2: NPC Claim #2
**Source:** [NPC name]
**Date Observed:** [YYYY-MM-DD]
**Claim:** [Exact claim text from NPC observation]
**Evidence:**
- [Specific data point 1]
- [Specific data point 2]

### Evidence Requirement 3: Counterexample (Failed Case)
**Case:** [Decision ID or description]
**Outcome:** [What happened]
**Why Current Doctrine Fails:** [Explain gap in current doctrine]
**How Proposed Amendment Fixes It:** [Explain how new wording resolves issue]

### Observation Window
**Start Date:** [90 days ago minimum]
**End Date:** [Today]
**Total Duration:** [≥90 days]
**Data Points Collected:** [Count of verdicts, outcomes, observations analyzed]

**Gate A Status:** ☐ PASS (≥2 NPCs + ≥90 days + ≥1 counterexample)

---

## GATE B: CONSERVATISM PHASE

**Question:** Why is inaction more dangerous than change?

**Default Assumption:** Keep current doctrine as-is. You must prove amendment is necessary.

### Analysis: Cost of Inaction
**If we do NOT amend:**
- [Consequence 1: What will continue to happen wrong?]
- [Consequence 2: What opportunity will be missed?]
- [Consequence 3: What risk remains unaddressed?]
- [Quantify if possible: "~€X cost per decision", "affects Y% of submissions"]

### Analysis: Risk of Amendment
**If we DO amend:**
- [Risk 1: What could go wrong?]
- [Risk 2: What precedent does this set?]
- [Risk 3: How does this interact with other doctrine sections?]
- [Mitigation: How will we detect if amendment is failing?]

### Conservatism Test Result
**Decision:** Does burden of proof favor inaction or action?

☐ **INACTION IS MORE DANGEROUS** — Amendment is justified
☐ **AMENDMENT IS MORE RISKY** — Keep current doctrine

**Reasoning:** [Explain which side of the test this amendment passes]

**Gate B Status:** ☐ PASS (Burden of proof met for change)

---

## GATE C: RATIFICATION PHASE

**Question:** Do you commit to this amendment?

This is your vote. It is logged, timestamped, and irreversible.

### Your Decision
☐ **REJECT** — Cannot re-propose for 180 days
☐ **CONDITIONALLY ACCEPT** — Applies to future submissions only, sunset date: [DATE]
☐ **RATIFY** — New doctrine version, old doctrine remains valid for historical claims

### Ratification Statement
[Your explicit commitment to this amendment in your own words]

**Example:**
> "I ratify this amendment because the evidence is compelling (three independent NPCs observed the same pattern over 120 days), and the cost of inaction (continued acceptance of speculative claims as CLASS_I) is higher than the risk of tightening evidence thresholds by 5%."

### Amendment Outcome
**Decision:** [Your vote above]
**Timestamp:** [ISO 8601]
**Hash:** [sha256 of this entire amendment document]

If RATIFY:
- **New Version:** DOCTRINE_V1.1
- **Effective Date:** [Today + 1]
- **Old Version:** DOCTRINE_V1.0 remains valid for all claims created under it

If CONDITIONALLY ACCEPT:
- **Scope:** New submissions only (retroactive application forbidden)
- **Sunset Date:** [You specified above]
- **Transition:** What happens when sunset arrives?

If REJECT:
- **Re-proposal Block:** Until [Date + 180 days]
- **Reasoning:** [Brief explanation for your own records]

**Gate C Status:** ☐ COMPLETE (Ratification recorded)

---

## AMENDMENT SUMMARY

| Gate | Status | Date |
|------|--------|------|
| A: Evidence | ☐ PASS / ☐ FAIL | [DATE] |
| B: Conservatism | ☐ PASS / ☐ FAIL | [DATE] |
| C: Ratification | ☐ RATIFY / ☐ CONDITIONAL / ☐ REJECT | [DATE] |

**Overall Result:**
- ✓ ACCEPTED (all gates PASS + ratified)
- ✗ REJECTED (any gate FAIL or you REJECT at C)
- ⏳ DEFERRED (waiting for evidence or conservatism resolution)

---

## APPENDIX A: Historical Context

**Why This Amendment Was Proposed:**
[Narrative of events, decisions, or patterns that led to this proposal]

**When This Amendment Became Necessary:**
[Key decision date or event that triggered consideration]

**Who Benefits from This Amendment:**
[Which NPC(s), which class of decisions, which scenarios]

---

## APPENDIX B: Ledger Entry

```json
{
  "amendment_id": "A-[DATE]-[SEQUENCE]",
  "doctrine_version_from": "1.0",
  "doctrine_version_to": "1.1",
  "sections_affected": ["Section 2", "Section 8"],
  "timestamp_proposed": "2026-01-31T00:00:00Z",
  "timestamp_ratified": "[ISO 8601]",
  "gate_a_evidence_count": 3,
  "gate_a_observation_days": 120,
  "gate_b_conservatism_result": "PASS",
  "gate_c_ratification_vote": "RATIFY",
  "ratification_hash": "sha256:...",
  "new_doctrine_hash": "sha256:..."
}
```

---

## IMMUTABLE RECORD

Once this amendment is RATIFIED:
1. **This document** becomes immutable (no edits allowed)
2. **DOCTRINE_V1.1** is created with new hash and effective date
3. **DOCTRINE_V1.0** remains pinned to all claims created under it
4. **Future amendments** reference this one as precedent
5. **Audit trail** shows complete evolution of doctrine over time

**No retroactive reinterpretation of old claims under new doctrine.**

---

**Amendment Template Version:** 1.0
**Date:** January 31, 2026
**Status:** READY FOR USE
