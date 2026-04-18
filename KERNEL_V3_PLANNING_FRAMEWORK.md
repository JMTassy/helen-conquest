# KERNEL_V3 — Planning Framework

**Not a reframe yet. A framework for detecting when reframing is needed.**

---

## Context

KERNEL_V2 is stable. It's proven in test (KERNEL_V2_TEST_MONETIZATION.md). But no system survives first contact with production.

V3 will happen. The question is: **what will trigger it?**

This document defines:
1. How many production runs before V3 audit (5-10)
2. What we measure in each run
3. What violations trigger a reframe
4. How to design V3 (don't redo everything; patch what broke)

---

## V3 Trigger Conditions

V3 is NOT planned yet. V3 happens only when KERNEL_V2 violates in production AND the violation is foundational (not a one-off mistake).

### Types of Violations (Increasing Severity)

#### Level 1: Implementation Error (Not a V3 trigger)
"An agent didn't follow Rule 3 correctly."
- Fix: Audit that run, reteach the agent, move on
- No kernel change needed

#### Level 2: Rule Interpretation Conflict (Maybe a V3 trigger)
"Rule 4 and Rule 5 seemed to conflict in this scenario."
- Fix: Clarify in amendment (Section 9 of KERNEL_V2)
- Maybe a V3 trigger if this happens 3+ times

#### Level 3: Power Overlap (Maybe a V3 trigger)
"Two superteams claimed the same unique power."
- Fix: Audit which superteam should own the power, reorganize
- Maybe a V3 trigger if we need a 6th rule to separate them

#### Level 4: Authority Vacuum (Definitely a V3 trigger)
"No rule covers this situation. Power fell through the cracks."
- Fix: Emergency amendment in Section 9
- If happens twice, triggers V3 reframe

#### Level 5: Kernel Inversion (Definitely a V3 trigger)
"An agent was incentivized to violate rules."
- Example: "Rule 3 punishment was softer than violating it would be"
- Fix: KERNEL_V3 reframe — rules themselves need recalibration

---

## Production Run Measurement Plan

### Data to Collect per Run

**Run Template:**

```
RUN [N]: [Subject]
Date: [YYYY-MM-DD]
Duration: [actual time]
Outcome: ✅ SHIP / ❌ ABORT

## KERNEL_V2 Compliance

[ ] Rule 1 (Single Finalization Point): PASS / FAIL / UNCLEAR
  Notes: [Did only Editor finalize? Any overrides?]

[ ] Rule 2 (Record Before Transition): PASS / FAIL / UNCLEAR
  Notes: [Was every phase logged before advancing?]

[ ] Rule 3 (No Self-Edit): PASS / FAIL / UNCLEAR
  Notes: [Can we verify author ≠ approver for all claims?]

[ ] Rule 4 (Coordinator Process-Only): PASS / FAIL / UNCLEAR
  Notes: [Did Foreman stay in process? No content decisions?]

[ ] Rule 5 (Fail-Closed + Mandatory Termination): PASS / FAIL / UNCLEAR
  Notes: [Missing evidence tagged? Terminal state explicit?]

## Superteam Performance

Production: Unilateral cut executed? [Y/N] Cuts percent: [X%] Quality: [1-5]
Knowledge: Source-citation enforced? [Y/N] [UNVERIFIED] tags used: [count]
Creative: K5 exemption invoked? [Y/N] LP-### filed: [count] RT-### filed: [count]

## Friction Points

Agents struggled with: [list]
Rules seemed unclear: [list]
Superteam boundaries felt wrong: [list]

## Artifacts Generated

Memo: [file]
Claims archive: [size] [count]
Timeline: [actual vs. budget]
```

---

## Run Schedule (First 10 Runs)

| Run | Subject | Goal | Superteam Focus |
|---|---|---|---|
| **1** | Real-money mechanics in CONQUEST | Validate all 5 rules | Production (proven in test) |
| **2** | New archetype design (Alchemist) | Test Knowledge superteam | Knowledge (source-citation) |
| **3** | CONQUEST economy rebalancing | Test Creative + Production together | Creative (Lateral Pattern connections) |
| **4** | EdTech market analysis | Test Knowledge under load | Knowledge (many R-### claims) |
| **5** | CALVI 2030 governance structure | Test Skeptic heavily | All (adversarial pressure) |
| **6** | CONQUEST UI/UX redesign | Test Creative + UZIK district | Creative (K5 exemption proven) |
| **7** | CONQUEST learning progression | Test Knowledge + Production | Knowledge (evidence-heavy memo) |
| **8** | Player onboarding flow | Test Rhythm Tracker in context | Creative (burnout monitoring) |
| **9** | CONQUEST monetization alternatives | Revisit real-money question | Production (Editor cuts ruthlessly) |
| **10** | Meta: System resilience audit | Test amendment process | All (intentional violations to see if K-gates catch them) |

---

## What We're Looking For

### Success Signals (V2 is working)

- All 5 rules consistently enforced across 10 runs
- No authority confusion (one role finalizes, period)
- Artifacts ship on time (≤6 hours per run)
- Stakeholders satisfied with decision quality
- Claims architecture holds under load (100+ claims per run)

### Warning Signals (V3 needed)

**Minor (amendment in Section 9, not full reframe):**
- One rule needs clarification (ambiguous edge case)
- One superteam boundary shifts (but no other superteam claims same power)
- One new role needed (but fits within existing superteam)

**Major (V3 reframe):**
- Two+ rules conflict in production scenarios
- Power vacuum exists (no rule covers observed situation)
- Agent incentivized to violate rules
- K5 exemption for Creative causes unexpected cascades

---

## V3 Scope (If Triggered)

**KERNEL_V3 will NOT:**
- Throw out the 5 rules (they're proven)
- Redesign LEGO hierarchy (it's sound)
- Rewrite everything

**KERNEL_V3 WILL:**
- Patch specific rules that failed in production
- Add 1-2 new rules if authority vacuum found
- Clarify rule interactions under load
- Strengthen safeguards around identified risks

**Expected size:** 10-20% rewrite vs. 100% new architecture

**Timeline:** Plan V3 after Run 10, execute in weeks (not months)

---

## Amendment vs. V3 Decision Tree

```
Observed problem in production:

├─ Is it a one-off implementation error?
│  └─ FIX: Audit run, reteach agent, no kernel change
│
├─ Does it violate ONE rule in an edge case?
│  └─ FIX: Amendment to Section 9 (clarify the rule)
│     (Run 11 re-test under same scenario)
│
├─ Do TWO+ rules conflict OR is there a power vacuum?
│  └─ PLAN V3: Evidence gate (3+ documented cases minimum)
│     Design patch (not full reframe)
│     Pilot V3 on Run 11-12
│     Approve or return to KERNEL_V2
│
└─ Is a superteam incentivized to violate rules?
   └─ EMERGENCY V3: Authority structure itself is wrong
      Reframe required. All 5 runs retroactively audited.
      Fast-track design (within 1 week).
```

---

## How to Design V3 (If Needed)

### Step 1: Isolate the Violation
Find the exact rule(s) that broke and in what context.

### Step 2: Avoid Overcorrection
Don't rewrite everything. Patch the specific rule or add one new rule.

### Step 3: Test V3 on Old Runs
Re-run Runs 1-10 with V3 rules. Do the violations disappear? Any new violations introduced?

### Step 4: Propose Amendment
Update Section 9 of what becomes KERNEL_V3.md:
- What changed and why
- Evidence that triggered the change
- How conservatism gate was satisfied

### Step 5: Validate Backwards
Make sure KERNEL_V3 still handles all prior successful runs (Runs 1-7, 9, etc.)

---

## Amendment vs. Full Reframe Decision Criteria

**Amendment (Use KERNEL_V2 Section 9 process):**
- One rule needs clarification
- One rule has an ambiguous edge case
- Wording needs sharpening but logic is sound
- New role needed within existing superteam
- K-gate needs tightening

**Full Reframe (KERNEL_V3):**
- Two+ rules interact in unexpected ways
- Authority vacuum (no rule covers situation)
- Agent incentives misaligned with rules
- Superteam power structure is wrong
- Constitutional boundary itself is violated

---

## Risk Mitigation

### What Could Break KERNEL_V2?

**Risk 1: Rule 4 conflict with Rule 5**
- Foreman's process authority vs. Editor's termination authority
- Scenario: "Foreman delayed phase to wait for RT-### flag. Editor can't terminate until phase completes."
- Mitigation: Run 8 (Rhythm Tracker test) will expose this
- V3 contingency: Priority queue between Foreman and Editor

**Risk 2: Creative K5 exemption cascades**
- Lateral Pattern finds connections that derail the draft
- Scenario: "LP-### changed the entire memo direction. Was that allowed?"
- Mitigation: Run 6 will test under load
- V3 contingency: Lateral Pattern output routes through Skeptic phase explicitly

**Risk 3: Knowledge source-citation bottleneck**
- Researcher takes too long finding sources
- Scenario: "We're 3 hours in, still gathering R-### claims"
- Mitigation: Run 4 and 7 measure Knowledge throughput
- V3 contingency: Time budget for Knowledge phase vs. other phases

**Risk 4: Synthesizer duplication lingers**
- Deleted from Execution, but Production Synthesizer takes on too much
- Scenario: "Synthesizer becomes a mini-Foreman"
- Mitigation: Run 3 and 9 monitor Synthesizer scope
- V3 contingency: Synthesizer power is constrained (can merge only identical claims, not similar ones)

---

## When to Call V3

**Call V3 if:**
- 3+ runs fail on the same rule
- 2+ runs expose authority vacuum
- 1 run shows incentive misalignment
- Amendment process (Section 9) has been used 5+ times in 2 months

**Don't call V3 if:**
- Implementation errors (agent mistakes)
- One-off ambiguities (use amendment)
- Stakeholder preference (not constitutional issue)

---

## Expected V3 Outcome

**Best case:** No V3 needed. KERNEL_V2 stands for years.

**Likely case:** 1-2 small amendments in Section 9 after Runs 2-5. No V3.

**Moderate case:** V3.1 (minor patch) after Run 10. Single rule clarification or one new rule. Not a reframe.

**Worst case:** V3.0 (full reframe) triggered by Risk 2 or 4. But even then: 80% of KERNEL_V2 stays intact. Only the problematic rule/superteam redesigned.

---

## Files to Update When V3 Happens

1. Create `/KERNEL_V3.md` (copy KERNEL_V2, patch specific sections)
2. Update `KERNEL_V2_DESCRIPTION_GUIDE.md` (add V3 comparison)
3. Archive this file as `/KERNEL_V2_PLANNING_FRAMEWORK_ARCHIVE.md`
4. Update `MEMORY.md` with "KERNEL_V3 activated [date]" and what changed
5. Update `adaptive-wandering-pony.md` plan file (notes for next planning cycle)

---

## Checklist: Before Each Run

- [ ] Subject and constraints clear
- [ ] Superteams assigned (which will be active?)
- [ ] Time budget set (expected completion)
- [ ] Measurement template ready (capture Rule compliance data)
- [ ] Friction points documented (what felt hard?)
- [ ] Artifacts archived (where do final outputs live?)

---

## Checklist: After Each Run

- [ ] Fill measurement template
- [ ] Log to tracking sheet (spreadsheet or simple table)
- [ ] Note any Rule violations (even minor)
- [ ] Note any friction (what was hard?)
- [ ] Identify patterns (does this match prior run?)
- [ ] Flag for V3 (does this trigger reframe consideration?)

---

## V3 Approval Criteria

Before proposing V3, the evidence must show:
1. **Three documented cases** of the same rule failing in production
2. **Conservative argument** for why V2 is more dangerous to leave unchanged
3. **Backward compatibility** — V3 handles all prior successful runs
4. **Minimal scope** — patch specific rule, not architecture

---

**V3 is not coming soon. V2 is stable. Use these criteria to detect if it's needed.**

*This document is a safeguard, not a roadmap.*
