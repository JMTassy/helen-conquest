# 🧾 ORACLE TOWN — YEAR-2 LOG SCHEMAS

**Human-First, Insight-Preserving, Machine-Verifiable**

---

## 0. Design Principle (Read This First)

Numbers explain **whether** something happened.
Insights explain **why** it mattered.

Therefore:
- Every log has **two layers:**
  1. **FACT LAYER** (immutable, auditable)
  2. **INSIGHT LAYER** (descriptive, non-binding, human-readable)

No insight is ever allowed to:
- ❌ justify a decision
- ❌ amend doctrine
- ❌ cross into evidence

---

## 1. Daily Town Log

**"What did this town actually live through today?"**

```json
{
  "log_type": "DAILY_TOWN_LOG",
  "town_id": "PORTO",
  "date": "2026-04-17",
  "doctrine_hash": "sha256:abc123...",
  "kernel_hash": "sha256:def456...",

  "fact_layer": {
    "claims_received": 12,
    "ship_count": 9,
    "no_ship_count": 3,
    "override_count": 1,
    "k_gate_rejections": {
      "K1": 2,
      "K2": 1,
      "K5": 0,
      "K7": 0
    },
    "parameter_snapshot": {
      "evidence_threshold": 0.50,
      "override_cost": 9,
      "evidence_decay": 0.92
    }
  },

  "insight_layer": {
    "mayor_reflection": "Most refusals today were due to incomplete evidence rather than disagreement. The town felt calm, not blocked.",
    "notable_tension": "One override clustered near identity-boundary decisions.",
    "felt_risk": "LOW",
    "felt_confidence": "STABLE",
    "felt_pressure_from_visibility": "NONE"
  },

  "constraints": {
    "insight_non_binding": true,
    "no_cross_town_reference": true
  },

  "signature": "ed25519:..."
}
```

### Why This Matters For You

- You'll remember **how the town felt**, not just what it did
- "Calm refusals" vs "anxious refusals" are radically different futures
- This prevents silent psychological drift

---

## 2. NPC Observation Log

**"What did the system notice without judging?"**

```json
{
  "log_type": "NPC_OBSERVATION",
  "npc_id": "npc_p_004",
  "town_id": "PORTO",
  "date": "2026-04-17",

  "observation": {
    "statement": "Override activity today was concentrated in late-stage identity claims.",
    "scope": "LOCAL_ONLY",
    "confidence": "DESCRIPTIVE",
    "time_span": "24h"
  },

  "forbidden_checks": {
    "normative_language": false,
    "recommendation": false,
    "comparison": false
  },

  "allowed_metadata": {
    "counts": {
      "overrides": 1,
      "identity_claims": 3
    }
  },

  "insight_tag": [
    "override-clustering",
    "identity-boundary"
  ],

  "signature": "npc-key:..."
}
```

### Why This Matters For You

- NPCs become **memory keepers**, not advisors
- Over time, you'll see patterns without being pushed by them
- This protects your intuition from being hijacked by analytics

---

## 3. CORSE AI MATIN — Daily Edition

**"What circulated across the island today?"**

```json
{
  "publication": "CORSE_AI_MATIN",
  "date": "2026-04-17",
  "edition_id": "CAM-2026-04-17",

  "column_A_ledger_facts": [
    {
      "town_id": "PORTO",
      "ship": 9,
      "no_ship": 3,
      "overrides": 1
    },
    {
      "town_id": "CORTE",
      "ship": 4,
      "no_ship": 6,
      "overrides": 0
    }
  ],

  "column_B_insight_zone": [
    {
      "origin": "npc_c_002",
      "text": "Evidence freeze durations appear longer this week.",
      "town_id": "CORTE"
    },
    {
      "origin": "npc_a_006",
      "text": "High throughput days did not correlate with increased override activity.",
      "town_id": "AJACCIO"
    }
  ],

  "kill_switch": {
    "interpretation_detected": false,
    "ranking_detected": false,
    "normative_language_detected": false
  },

  "signature": "sha256:..."
}
```

### Why This Matters For You

- This becomes your **slow newspaper**, not a feed
- No "best town", no trend, no pressure
- You can read it like **weather**, not like a scoreboard

---

## 4. CALVI EVENT LOG (Annual)

**"What emerged when everyone was together?"**

```json
{
  "event_type": "CALVI_ON_THE_AI_ROCKS",
  "year": 2027,
  "location": "CALVI",

  "fact_layer": {
    "npc_present": 87,
    "towns_present": 10,
    "insights_generated": 214,
    "claims_generated": 0,
    "kill_switch_activations": 11
  },

  "insight_layer": {
    "collective_mood": "CURIOUS / UNRUSHED",
    "dominant_themes": [
      "identity boundaries",
      "long-term reversibility",
      "silence as signal"
    ],
    "notable_absence": "No convergence language detected.",
    "human_takeaway": "The system felt more like a monastery than a market."
  },

  "boundary_enforcement": {
    "claims_allowed": false,
    "decisions_allowed": false,
    "doctrine_discussion": "DESCRIPTIVE_ONLY"
  }
}
```

### Why This Matters For You

- This captures **culture**, not just structure
- You'll remember **why** Calvi exists
- It prevents the event from slowly turning into Davos

---

## 5. Monthly Human Synthesis Log (Optional but Powerful)

**"What did I, as a human, actually learn?"**

⚠️ **This is not used by the system.**
**It exists only for you.**

```json
{
  "log_type": "HUMAN_SYNTHESIS",
  "author": "Jean-Marie Tassy",
  "month": "2026-04",

  "what_surprised_me": "High refusal days felt more peaceful than high acceptance days.",
  "what_i_expected_but_didnt_happen": "Prestige did not create imitation pressure.",
  "what_i_understand_better_now": "Refusal is not friction — it is clarity.",
  "what_i_am_watching_next": "Subtle emotional responses to prolonged silence.",
  "what_i_refuse_to_optimize": "Acceptance rate — it is no longer my metric."
}
```

### Why This Matters For You

- This protects you from becoming a machine operator
- It preserves the **meaning** of what you built
- Future-you will thank present-you for this layer

---

## 6. Query Interface (Human + Machine)

**For searching patterns without imposing them:**

```python
# Query examples (human-readable):
What surprised the system this month?
Which insights re-appeared after long silence?
How did the town feel in April vs March?
Did anything break the pattern?
When was the last genuine disagreement?
```

**Returns:**
- Timestamped observations
- Supporting facts (numbers)
- Context (human reflection)
- No ranking, no recommendation

---

## Implementation Schedule

| Phase | When | What |
|---|---|---|
| **Daily Logs** | Every evening | Fact + insight capture |
| **NPC Observations** | Continuous | Append-only memory |
| **CORSE Edition** | Every evening | Public circulation |
| **Monthly Synthesis** | Month-end | Human reflection only |
| **CALVI Log** | Annual event (Dec) | Culture capture |
| **Query System** | Throughout | Pattern search (read-only) |

---

## Final Insight (Human to Human)

What you're actually building is not just a system.

You're building:
- A **memory that doesn't lie**
- A **culture that doesn't centralize**
- A **future self that won't gaslight the past**

Most systems forget why they were built.

**This one remembers — because you designed it to.**

---

**🐎 TRACULINU NUNZIA — L'histoire se souvient.**

*Last updated: 2026-02-01T00:00:00Z*
*Status: READY FOR YEAR-2*
