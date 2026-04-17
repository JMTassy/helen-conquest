# NPC CONSTITUTIONAL CHARTER

**Status:** IMMUTABLE SUPPORT DOCUMENT
**Effective Date:** January 31, 2026
**Authority:** DOCTRINE_V1.0, Section 9

---

## PREAMBLE

NPCs are non-playing constitutional witnesses.

They cannot decide.
They cannot recommend.
They cannot optimize.
They cannot trigger action.

They exist to answer one question only:

> "What actually happened under the doctrine we ratified?"

Their observations are eligible evidence for doctrine amendments.
Nothing else.
Nothing more.

---

## SECTION 1: THE FIVE FOUNDATIONAL RULES (NON-NEGOTIABLE)

These rules apply to all NPCs, forever.

### Rule 1: No Prescriptions

NPC output must not contain the words or concepts:
- "should"
- "must"
- "recommend"
- "better"
- "worse"

**Permitted language:**
- "measurement: 0.71"
- "accept_outcome_success_rate declined by 0.08"
- "16 of 22 CLASS_III overrides succeeded"

**Forbidden language:**
- "You should accept more"
- "The doctrine is too strict"
- "We should tighten evidence standards"

**Enforcement:** Any observation containing prescriptive language is rejected at intake. Silent discard (NPCs do not error).

### Rule 2: No Future Tense

NPCs do not predict. They measure the past.

**Permitted:**
- "Acceptance rate was 42% in April"
- "SpeculationTracker observed 3 CLASS_III outcomes reviewed this period"

**Forbidden:**
- "Acceptance rate will rise to 45% next quarter"
- "If we don't change policy, outcomes will worsen"
- "We expect failure rates to increase"

**Enforcement:** Observations using "will", "expect", "predict", "forecast" are discarded.

### Rule 3: Ledger-Bound Only

NPC observations must reference only:
- Receipts (immutable verdict records)
- Past outcomes (recorded when review date passed)
- Doctrine versions (published, hashed versions)

**Forbidden sources:**
- External data not in ledger
- Personal intuition
- Extrapolations beyond observed window
- Forecasts

**Enforcement:** Every observation must include ≥1 referenced receipt_id. Observations without ledger references are discarded.

### Rule 4: Doctrine-Pinned

Every NPC observation must explicitly declare:
- `doctrine_version` (e.g., "1.0")
- `doctrine_hash` (e.g., "sha256:6ba9551d...")

If observations span a doctrine amendment, the NPC must split the observation:
- One observation under doctrine v1.0 (receipts 1-100)
- One observation under doctrine v1.1 (receipts 101-150)

**Why:** Doctrine changes make apples-to-apples comparison impossible. Honesty requires splitting.

**Enforcement:** Observations lacking valid doctrine_hash are discarded.

### Rule 5: Silence Is Valid Output

An NPC may emit nothing for a window. This is data.

**Example:**
- PatternDetector observes for 90 days
- No drift detected
- Emits nothing (silence is signal)

**Incorrect response:**
- "No anomalies detected" (a statement, not silence)

**Correct response:**
- Emit no observation (silence)

**Why:** Silence prevents forced conclusions. It respects unknowns.

---

## SECTION 2: THE FOUR CANONICAL NPC TYPES (IMMUTABLE SET)

Adding or removing NPC types requires formal doctrine amendment.

### NPC-A: AccuracyWatcher

**Question it answers:**
Did ACCEPT and REJECT verdicts align with outcomes historically?

**Permitted metrics:**
- `accept_outcome_success_rate` — % of ACCEPT verdicts where outcome matched expectation
- `reject_regret_rate` — % of REJECT verdicts where manual override later proved necessary
- `false_positive_rate` — % of ACCEPT verdicts that later failed
- `false_negative_rate` — % of REJECT verdicts that manual override later succeeded

**Example observation (valid):**
```json
{
  "npc_type": "accuracy_watcher",
  "observation_window": {
    "start": "2026-01-31",
    "end": "2026-04-30"
  },
  "referenced_receipts": ["R-2026-02-15-0001", "R-2026-02-15-0002", ...],
  "metric_id": "accept_outcome_success_rate",
  "measurement": {
    "value": 0.71,
    "unit": "ratio"
  },
  "confidence": "HIGH",
  "notes": "Of 24 ACCEPT verdicts issued Feb-Apr, 17 outcomes succeeded (0.71). 7 failed."
}
```

**Forbidden observation:**
```json
{
  "metric_id": "accept_outcome_success_rate",
  "measurement": 0.71,
  "notes": "This shows your rejection discipline is working."  // Prescriptive
}
```

---

### NPC-B: SpeculationTracker

**Question it answers:**
Are CLASS_III overrides paying off or compounding risk?

**Permitted metrics:**
- `override_success_ratio` — % of reviewed CLASS_III overrides that succeeded
- `capital_at_risk` — total amount committed via CLASS_III overrides, currently unlocked
- `capital_recovered` — total amount returned from reviewed CLASS_III overrides
- `identity_alignment_score` — yes/no: did the override measure up to its identity-defining claim?

**Special rule:**
- MUST include `review_date` reference
- MUST emit follow-up observation when review date passes
- This NPC tracks specific overrides through their lifecycle

**Silence rule:**
- If review date not reached → emit nothing
- Example: "The LE TAR wall is reviewed 2027-01-31. Today is 2026-09-30. Silence."

**Example observation (valid):**
```json
{
  "npc_type": "speculation_tracker",
  "referenced_receipts": ["override_le_tar_wall_001"],
  "metric_id": "capital_at_risk",
  "measurement": {
    "value": 700000,
    "unit": "EUR"
  },
  "review_date": "2027-01-31",
  "notes": "LE TAR wall override: €700k at risk, locked until 2027-01-31. Status: in progress."
}
```

**Forbidden observation:**
```json
{
  "metric_id": "capital_at_risk",
  "measurement": 700000,
  "notes": "This is too much risk. You should reconsider."  // Prescriptive
}
```

---

### NPC-C: PatternDetector

**Question it answers:**
Is doctrine producing systematic bias or blind spots?

**Permitted metrics:**
- `class_distribution` — Distribution of verdicts by CLASS_I/II/III/IV (are all classes used?)
- `rejection_cluster_density` — Are rejections clustered by class or spread evenly?
- `evidence_insufficiency_rate` — % of submissions rejected due to insufficient evidence (K1 enforcement)
- `doctrine_section_pressure` — Is one doctrine section producing more rejections than others?

**Example observation (valid):**
```json
{
  "npc_type": "pattern_detector",
  "observation_window": {
    "start": "2026-03-30",
    "end": "2026-06-28"
  },
  "metric_id": "class_distribution",
  "measurement": {
    "value": "CLASS_I: 40%, CLASS_II: 35%, CLASS_III: 20%, CLASS_IV: 5%"
  },
  "confidence": "HIGH",
  "notes": "Class distribution stable across 90-day window. No drift detected."
}
```

**Canary property:**
PatternDetector is the early warning system, not the reformer. It detects drift but does not propose fixes.

---

### NPC-D: RiskAnalyzer

**Question it answers:**
Is your override behavior becoming normalized? Are exceptions creeping into routine?

**Permitted metrics:**
- `override_frequency` — How many CLASS_III/IV overrides per month (trending up/down/stable?)
- `mean_time_between_overrides` — Average days between override decisions
- `override_justification_length` — Average characters in override reasoning (longer = more seriousness)
- `override_dependency_index` — Do overrides cluster in specific areas (high = exception creep)

**Example observation (valid):**
```json
{
  "npc_type": "risk_analyzer",
  "observation_window": {
    "start": "2026-03-30",
    "end": "2026-06-28"
  },
  "metric_id": "override_frequency",
  "measurement": {
    "value": 2.3,
    "unit": "per month"
  },
  "delta": {
    "value": 0.5,
    "baseline_window": {
      "start": "2026-01-01",
      "end": "2026-03-29"
    }
  },
  "confidence": "MEDIUM",
  "notes": "Override frequency trending up: 1.8/month (Jan-Mar) → 2.3/month (Mar-Jun). +0.5 per month. Monitor."
}
```

**This NPC protects against normalization of deviation.** It does not judge. It measures.

---

## SECTION 3: NPC OUTPUT SEMANTICS (CRITICAL)

NPC observations are:

❌ **NOT claims** — They are not submitted to TRI gate
❌ **NOT proposals** — They do not suggest actions
❌ **NOT inputs to TRI** — TRI gate ignores NPCs entirely
❌ **NOT reasons for action** — They do not justify any decision
❌ **NOT warnings** — They do not trigger alerts

They are:

✅ **Eligible evidence** — For doctrine amendments (see Section 4)
✅ **Retrospective audits** — For understanding doctrine evolution
✅ **Personal accountability** — For your future self to understand what was observed

Nothing else. Nothing more.

---

## SECTION 4: NPC → AMENDMENT GATE (Structural Enforcement)

An amendment **cannot be proposed** unless all three conditions are met:

### Condition 1: ≥2 Distinct NPC Types

Example valid states:
- ✅ AccuracyWatcher + PatternDetector (2 types)
- ✅ AccuracyWatcher + SpeculationTracker + RiskAnalyzer (3 types)
- ❌ AccuracyWatcher only (1 type)
- ❌ AccuracyWatcher + AccuracyWatcher (same type twice)

**Why:** One observer can be idiosyncratic. Two independent observers noticing the same problem is signal.

### Condition 2: ≥90 Consecutive Days Observation

- Observations must cover the same time window
- Example: Both start on 2026-03-30, both end on 2026-06-28 (exactly 90 days)
- Fragmented observations (30 days here, 30 days there, 30 days elsewhere) do NOT count

**Why:** Doctrine stability requires time. Quick amendments are corrupted by noise.

### Condition 3: Referencing the Same Doctrine Section

Both NPCs must reference:
- Same `doctrine_hash` (no amendments happened between observations)
- Same target section (e.g., both reference "Section 1.2 — CLASS_II")

**Why:** Amendment must address a specific gap. General complaints are not actionable.

### Structural Enforcement

Amendment submission will be **rejected at intake** if:
- Fewer than 2 NPC types represented
- Observation window < 90 days
- Different doctrine versions mixed
- Target section misaligned between NPCs

This is not negotiable. This is enforced by the Doctrine Enforcer module.

---

## SECTION 5: WHY THIS IS HARD (AND NECESSARY)

You have now enforced:

1. **Witnesses without power**
   - NPCs observe
   - NPCs have no authority to change anything
   - NPCs cannot trigger action

2. **Power without witnesses forbidden**
   - Amendments require NPC evidence
   - You cannot amend based on feeling alone
   - Authority is exercised only after witnesses speak

3. **Change without evidence impossible**
   - Amendment requires 90 days + 2 NPCs + 1 target section
   - Fast amendments are blocked structurally
   - Reactive changes are prevented by design

This prevents:
- ❌ "The system felt wrong" amendments (requires NPC evidence)
- ❌ "Standards evolved naturally" claims (amendments are logged explicitly)
- ❌ "We always meant it this way" rewriting (old doctrine versions are pinned)

**Your future self will not be able to lie to your past self.**

---

## SECTION 6: NPC IMMUTABILITY

The set of four NPC types is immutable:
- AccuracyWatcher
- SpeculationTracker
- PatternDetector
- RiskAnalyzer

**Cannot:**
- Add new NPC types without formal doctrine amendment
- Remove existing NPC types without formal doctrine amendment
- Change what metrics a given NPC can emit (requires amendment)

**Can:**
- Add new metrics to MetricId enum, but only via amendment
- Modify NPC observation frequency (no structural change)
- Create multiple instances of same NPC type (e.g., AccuracyWatcher_001, AccuracyWatcher_002)

---

## SECTION 7: LEDGER ENTRY FOR NPC OBSERVATIONS

Every NPC observation is recorded in ledger:

```
oracle_town/ledger/observations/YYYY/MM/
├── obs_npc_accuracy_watcher_2026_02_15_001.json
├── obs_npc_pattern_detector_2026_03_30_001.json
└── obs_npc_speculation_tracker_2026_04_15_001.json
```

**Properties:**
- Immutable (append-only)
- Timestamped
- Doctrine-pinned
- Searchable by NPC type and date
- Complete audit trail of what NPCs observed

---

## SECTION 8: NPC TESTING AND VERIFICATION

### K5 Determinism

NPC observations must be deterministic:
- Same receipt set + same window + same metric → identical observation

```bash
# Test: Run same NPC observation 200 times
for i in {1..200}; do
  python3 oracle_town/npc_framework.py \
    --npc accuracy_watcher \
    --receipts receipts_feb_to_apr.json \
    --output obs_{i}.json
done

# Verify: All observations have identical hash
sha256sum obs_*.json | sort | uniq -c
# Should show: 200 identical hashes
```

### Validation Tests

```bash
# Test: Forbidden language rejection
observation_with_should = NPCObservation(..., notes="You should...")
try:
  observation_with_should.validate()
  assert False, "Should have rejected prescriptive language"
except ValueError:
  pass  # Correct

# Test: Doctrine pinning
obs_without_doctrine = NPCObservation(..., doctrine_hash="")
try:
  obs_without_doctrine.validate()
  assert False, "Should have rejected missing doctrine_hash"
except ValueError:
  pass  # Correct

# Test: Referenced receipts required
obs_no_receipts = NPCObservation(..., referenced_receipts=[])
try:
  obs_no_receipts.validate()
  assert False, "Should have rejected no receipts"
except ValueError:
  pass  # Correct
```

---

## SECTION 9: WHAT NPCs CANNOT DO

NPCs may NOT:

❌ Change doctrine (requires amendment voting)
❌ Ratify decisions (requires you, the sole authority)
❌ Trigger overrides (requires explicit user submission)
❌ Modify ledger (ledger is append-only, NPCs are read-only)
❌ Access external data (ledger-bound only)
❌ Make predictions (past-tense only)
❌ Offer opinions (factual measurements only)
❌ Propose solutions (observations only, no prescriptions)
❌ Auto-execute anything (zero authority)

NPCs are **witnesses, not judges.**

---

## SECTION 10: WHAT NPCs CAN DO

NPCs may:

✅ Observe historical outcomes
✅ Measure metrics from ledger
✅ Detect patterns in verdicts
✅ Track CLASS_III overrides
✅ Emit structured observations
✅ Generate evidence for amendments
✅ Speak silently (emit nothing when appropriate)
✅ Reference doctrine versions explicitly

NPCs are **sources of truth, not sources of authority.**

---

## CLOSING

The NPC Constitutional Charter establishes:

1. **Witnesses without power** — NPCs observe but cannot command
2. **Power without witnesses forbidden** — Amendments require NPC evidence
3. **Change without evidence impossible** — 90 days + 2 NPCs + structural enforcement

Your future self will be accountable to what NPCs actually observed.
Not what you felt.
Not what you believed.
Not what you hoped.

**What actually happened.**

---

**NPC CONSTITUTIONAL CHARTER — EFFECTIVE JANUARY 31, 2026**
**STATUS: IMMUTABLE**
**AUTHORITY: DOCTRINE_V1.0, SECTION 9**
