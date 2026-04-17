# NPC → AMENDMENT INTERFACE SPECIFICATION

**Status:** STRUCTURAL ENFORCEMENT
**Effective Date:** January 31, 2026
**Version:** 1.0

---

## PREAMBLE

This document specifies the ONLY mechanism by which NPC observations become doctrine amendments.

**Core principle:**
Witnesses must speak before law changes.
Law cannot change based on authority alone.
Amendments require evidence.
Evidence comes only from NPCs.

This creates a structural separation:
- **NPCs observe** (witness layer)
- **You vote** (authority layer)
- **Doctrine evolves** (law layer)

No component can cross these layers.

---

## SECTION 1: THE AMENDMENT PROPOSAL GATE

An amendment proposal is **automatically rejected at intake** if it fails ANY of these checks:

### Check A: NPC Evidence Sufficiency

**Requirement:** ≥2 distinct NPC observations covering ≥90 consecutive days

**What this checks:**
- Are there ≥2 different NPC types represented? (e.g., AccuracyWatcher AND PatternDetector)
- Do both observations cover the exact same time window? (e.g., both 2026-03-30 to 2026-06-28)
- Is that window ≥90 days?

**Validation code pseudo-logic:**
```
npc_types_present = set()
for each npc_observation in amendment.supporting_evidence:
    npc_types_present.add(observation.npc_type)
    duration = observation.observation_window.duration_days()

    if duration < 90:
        reject("Observation window too short: {duration} < 90 days")

    if observation.doctrine_hash != pinned_doctrine_hash:
        reject("Doctrine version mismatch in NPC evidence")

if len(npc_types_present) < 2:
    reject("Amendment requires ≥2 distinct NPC types, got {len(npc_types_present)}")

if not all_windows_overlap(90+ days):
    reject("NPC observations must cover same 90+ day window")
```

**Rejection codes:**
- `AMENDMENT_REJECT_INSUFFICIENT_NPC_COUNT` — Fewer than 2 NPC types
- `AMENDMENT_REJECT_OBSERVATION_WINDOW_TOO_SHORT` — < 90 days
- `AMENDMENT_REJECT_DOCTRINE_MISMATCH` — Different doctrine versions
- `AMENDMENT_REJECT_OBSERVATION_WINDOWS_NOT_ALIGNED` — NPCs observed different periods

**Cannot be waived.** No exceptions.

---

### Check B: Amendment Specificity

**Requirement:** Amendment must target exactly ONE doctrine section

**What this checks:**
- Does the amendment reference a specific section? (e.g., "Section 1.2 — CLASS_II")
- Do all supporting NPC observations reference the same section?
- Is the proposed change clearly differentiated from current text?

**Validation code pseudo-logic:**
```
target_section = amendment.target_section
if not target_section:
    reject("Amendment must specify target_section")

for each npc_obs in amendment.supporting_evidence:
    if npc_obs.implied_section != target_section:
        reject("NPC observation {id} references different section")

# Check that proposed change is actually different
current_text = doctrine[target_section]
proposed_text = amendment.proposed_change
if current_text == proposed_text:
    reject("Proposed change is identical to current doctrine")
```

**Rejection codes:**
- `AMENDMENT_REJECT_NO_TARGET_SECTION` — Missing target section
- `AMENDMENT_REJECT_SECTION_MISMATCH` — NPC evidence targets different section
- `AMENDMENT_REJECT_NO_ACTUAL_CHANGE` — Proposed = current

---

### Check C: Conservative Risk Assessment

**Requirement:** `risk_of_inaction ≥ risk_of_change`

**What this checks:**
- Did you quantify cost of inaction?
- Did you quantify risk of amendment?
- Is inaction at least as dangerous as change?

**Validation code pseudo-logic:**
```
risk_inaction = amendment.conservatism_analysis.risk_of_inaction
risk_change = amendment.conservatism_analysis.risk_of_change

if not risk_inaction:
    reject("Conservatism analysis missing risk_of_inaction")

if not risk_change:
    reject("Conservatism analysis missing risk_of_change")

if risk_inaction < risk_change:
    reject("Amendment fails conservatism test: change (risk={risk_change}) exceeds inaction (risk={risk_inaction})")
```

**Rejection codes:**
- `AMENDMENT_REJECT_MISSING_CONSERVATISM_ANALYSIS` — No risk quantification
- `AMENDMENT_REJECT_CONSERVATISM_TEST_FAILED` — Inaction less risky than change
- `AMENDMENT_REJECT_RISK_COMPARISON_UNCLEAR` — Risks not comparable

---

## SECTION 2: VALID AMENDMENT FLOW

Assuming all three checks pass, amendment proceeds to Gate C: Ratification.

```
Amendment Proposal
    ↓
Check A: NPC Evidence (≥2 types, ≥90 days, same window)
    ├─ FAIL → AUTO REJECT (intake gate)
    └─ PASS
         ↓
Check B: Specificity (one section, clear change)
    ├─ FAIL → AUTO REJECT (intake gate)
    └─ PASS
         ↓
Check C: Conservatism (inaction ≥ risk of change)
    ├─ FAIL → AUTO REJECT (intake gate)
    └─ PASS
         ↓
Gate C: Ratification (YOUR VOTE)
    ├─ RATIFY → New doctrine version created
    ├─ CONDITIONAL_ACCEPT → Trial period begins
    └─ REJECT → 180-day lockout, no re-proposal
```

**Key property:** Three checks are automatic and deterministic. Gate C is your conscious choice.

---

## SECTION 3: NPC SILENCE AND AMENDMENT BLOCKING

An amendment proposal can be **blocked by NPC silence**.

**Scenario:**
You want to propose amendment A-2026-06-001 (tighten CLASS_II evidence).
You have:
- AccuracyWatcher observation (March 30 - June 28)
- PatternDetector observation (March 30 - June 28)
- Your conservatism analysis

But during that same 90-day window:
- RiskAnalyzer emitted nothing (silence)
- SpeculationTracker emitted nothing (silence)

**Question:** Is silence a problem?

**Answer:** No. Silence is valid. Amendment proceeds.

**Different scenario:**
You want to propose amendment A-2026-06-001 (tighten CLASS_II evidence).
But AccuracyWatcher explicitly contradicts it:

```json
{
  "npc_type": "accuracy_watcher",
  "observation": "CLASS_II evidence quality is appropriate. ACCEPT success rate remains stable at 71%.",
  "confidence": "HIGH"
}
```

**Question:** Can you ignore this NPC observation?

**Answer:** No. If you want to propose amendment contradicting this NPC, you must:
1. **Explain the contradiction** in amendment rationale
2. **Show why your conservatism analysis overrides NPC finding**
3. **Accept responsibility for ignoring NPC evidence**

This is recorded in ledger. Your future self can see you dismissed valid NPC evidence.

---

## SECTION 4: MULTIPLE AMENDMENTS IN SEQUENCE

Amendments create cascading constraints:

### Freeze Period (Post-Ratification)

After an amendment is RATIFIED:
- **30-day freeze:** No new amendments can be proposed
- **Reason:** New doctrine needs time to stabilize
- **Enforced by:** Intake gate checks amendment_timestamp against last_ratification_timestamp

### Override Cost Multiplier

After an amendment is RATIFIED:
- **60-day period:** All CLASS_III/IV overrides count as 2× normal weight in risk calculations
- **Reason:** Discourages circumventing new doctrine via overrides
- **Enforced by:** RiskAnalyzer flags heavy override use post-amendment

### NPC Threshold Tightening

After an amendment is RATIFIED:
- **120 days:** NPC observation thresholds for next amendment temporarily increase
  - Confidence must be HIGH (not MEDIUM)
  - ≥3 NPC types required (not ≥2)
  - Evidence window ≥120 days (not ≥90 days)
- **Reason:** Prevents amendment ping-pong and reactivity
- **Enforced by:** Intake gate checks for post-amendment period

**Timeline:**
```
Amendment A Ratified (Day 0)
    ├─ Day 0-30: Freeze (no new amendment proposals)
    ├─ Day 0-60: Override multiplier (CLASS_III counts as 2×)
    ├─ Day 0-120: Higher thresholds for next amendment (≥3 NPCs, ≥120 days, HIGH confidence)
    └─ Day 120+: Normal thresholds resume
```

---

## SECTION 5: EVIDENCE QUALITY STANDARDS

For amendment to pass intake, NPC evidence must meet quality standards.

### AccuracyWatcher Evidence Quality

**Valid:**
- "17 of 24 ACCEPT verdicts succeeded" (concrete count)
- "Success rate: 0.71" (measured ratio)
- "Failed outcomes: [list of decision IDs]" (verifiable cases)

**Invalid:**
- "Success rate appears good" (vague)
- "Most ACCEPTs worked out" (unmeasured)
- "We should expect 70%+ success" (prescriptive)

### PatternDetector Evidence Quality

**Valid:**
- "CLASS_II rejection rate: 40% (March) → 48% (June)" (concrete trend)
- "Evidence distribution: 60% strong, 30% moderate, 10% weak" (quantified)
- "Rejection clustering by class: CLASS_II concentrated 60%, others 15% each" (specific)

**Invalid:**
- "Rejection rates are increasing" (no numbers)
- "Evidence quality seems to be declining" (opinion)
- "We should be more selective" (prescriptive)

### SpeculationTracker Evidence Quality

**Valid:**
- "LE TAR wall: €700k at risk, review date 2027-01-31, in progress" (fact)
- "3 of 5 reviewed overrides succeeded (60%)" (measured)
- "Review dates: [explicit list with outcomes]" (verifiable)

**Invalid:**
- "Overrides are paying off" (vague)
- "The wall investment looks good" (opinion)

### RiskAnalyzer Evidence Quality

**Valid:**
- "Override frequency: 2.1/month (Jan-Mar) → 2.7/month (Apr-Jun)" (measured)
- "Justification length: avg 150 chars → avg 95 chars" (tracked metric)
- "Override dependency: 60% in Q2 concentrated in [specific domain]" (quantified)

**Invalid:**
- "Overrides are becoming too casual" (opinion)
- "We're relying too much on exceptions" (vague)

---

## SECTION 6: AMENDMENT LEDGER ENTRY

Every amendment creates immutable ledger entries:

```
oracle_town/ledger/amendments/2026/06/A-2026-06-001_ratified.json
```

**Contents:**
```json
{
  "amendment_id": "A-2026-06-001",
  "title": "Tighten CLASS_II Evidence Threshold",
  "doctrine_version_from": "1.0",
  "doctrine_version_to": "1.1",
  "target_sections": ["Section 1.2"],
  "timestamp_proposed": "2026-06-30T09:00:00Z",
  "gate_a_check": {
    "status": "PASS",
    "npc_types_present": ["accuracy_watcher", "pattern_detector"],
    "observation_window": {
      "start": "2026-03-30",
      "end": "2026-06-28"
    },
    "duration_days": 90
  },
  "gate_b_check": {
    "status": "PASS",
    "target_section": "Section 1.2",
    "proposed_change_valid": true
  },
  "gate_c_check": {
    "status": "PASS",
    "risk_of_inaction": "HIGH (€200k/month in failed CLASS_II)",
    "risk_of_change": "MEDIUM (modest rejection rate increase)",
    "conservatism_result": "INACTION_MORE_DANGEROUS"
  },
  "gate_c_ratification": {
    "status": "RATIFY",
    "timestamp": "2026-06-30T09:15:00Z",
    "ratification_statement": "..."
  },
  "doctrine_v1_0_hash": "sha256:6ba9551d6a17551a04a719b6f1539b9bae772c72fbb86053d3470607fd68a709",
  "doctrine_v1_1_hash": "sha256:[computed]",
  "freeze_period_until": "2026-07-30",
  "override_multiplier_until": "2026-08-29",
  "threshold_tightening_until": "2026-10-28"
}
```

**Properties:**
- Immutable (once recorded, never modified)
- Complete audit trail (all gates, all votes, all dates)
- Hashable (SHA-256 verification possible)
- Searchable (by date, by NPC type, by doctrine version)

---

## SECTION 7: REJECTED AMENDMENTS AND HISTORICAL RECORD

When an amendment is rejected (at intake or at Gate C), it is still recorded:

```
oracle_town/ledger/amendments/2026/06/A-2026-06-002_rejected.json
```

**Contents:**
```json
{
  "amendment_id": "A-2026-06-002",
  "title": "Loosen Acceptance Rate Target to 50%",
  "timestamp_proposed": "2026-06-15T10:00:00Z",
  "gate_a_check": {
    "status": "FAIL",
    "reason": "AMENDMENT_REJECT_INSUFFICIENT_NPC_COUNT",
    "details": "Amendment requires ≥2 distinct NPC types. Only AccuracyWatcher provided evidence."
  },
  "rejected_at_gate": "A"
}
```

**Alternative rejection (at Gate C):**
```json
{
  "amendment_id": "A-2026-06-003",
  "title": "Override CLASS_III Burden",
  "gate_a_check": { "status": "PASS" },
  "gate_b_check": { "status": "PASS" },
  "gate_c_check": { "status": "PASS" },
  "gate_c_ratification": {
    "status": "REJECT",
    "timestamp": "2026-06-30T14:30:00Z",
    "rejection_reason": "Evidence supports amendment, but risk analysis shows change is equally risky as inaction. Prefer stability. Can re-propose after 2026-12-30."
  },
  "cannot_resubmit_until": "2026-12-30T14:30:00Z"
}
```

**Key property:** Rejected amendments are fully recorded. Your future self can see what you considered and why you rejected it.

---

## SECTION 8: NPC-AMENDMENT DETERMINISM (K5)

Amendment intake checks must be deterministic:

**Same amendment inputs → Identical intake decision (ACCEPT or REJECT)**

```bash
# Test: Run amendment intake 10 times
for i in {1..10}; do
  python3 oracle_town/amendment_intake.py \
    --amendment amendment_A_2026_06_001.json \
    --output intake_result_{i}.json
done

# Verify: All results are identical
diff intake_result_1.json intake_result_2.json
# Should show: no differences

sha256sum intake_result_*.json | sort | uniq -c
# Should show: 10 identical hashes
```

**If non-deterministic → System is broken (K5 invariant violated)**

---

## SECTION 9: WHY THIS INTERFACE MATTERS

The NPC-Amendment interface enforces:

1. **Evidence before power**
   - Amendments require NPC observations
   - You cannot change doctrine without witnesses

2. **Time before change**
   - 90-day observation window is mandatory
   - Fast amendments are blocked structurally

3. **Honesty about trade-offs**
   - Conservatism test requires quantifying risks
   - You must show why change is necessary

4. **Accountability for reversals**
   - If amendment contradicts NPC evidence, it's recorded
   - Your future self can see you dismissed valid observation

This makes doctrine evolution transparent and prevents:
- ❌ Reactive amendments (require 90 days)
- ❌ Emotional amendments (require NPC evidence)
- ❌ Hidden amendments (full ledger record)
- ❌ Unauthorized amendments (intake gates are deterministic)

---

## CLOSING

The NPC-Amendment Interface completes the governance structure:

- **NPCs watch** (observation layer)
- **Intake gates validate** (enforcement layer)
- **You vote** (authority layer)
- **Doctrine evolves** (law layer)

Each layer is distinct. No component can cross layers.
This is the structure that prevents corruption.

---

**NPC-AMENDMENT INTERFACE SPECIFICATION — EFFECTIVE JANUARY 31, 2026**
**STATUS: IMMUTABLE**
**AUTHORITY: DOCTRINE_V1.0, SECTIONS 9-10**
