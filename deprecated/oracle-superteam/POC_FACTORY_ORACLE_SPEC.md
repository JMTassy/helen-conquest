# POC FACTORY ORACLE — Complete Specification
**Version:** 1.0-FINAL
**Status:** LOCKED FOR IMPLEMENTATION

---

## NORTH STAR DEFINITION

**POC FACTORY ORACLE = Superteam-driven ideation engine + execution/evidence factory + deterministic tribunal gate.**

It **brainstorms better solutions** because ideation is parallelized across specialized teams (Marketing/Engineering/Research/EV/Legal), but it **cannot ship without attestations** because shipping is strictly downstream of receipts and policy checks.

---

## FORMAL CONTRACT (MATHEMATICAL)

### Definitions

Let:
- A claim be `c ∈ C` with identifier `claim_id`
- A required obligation set for claim `c` be `R(c) = {o₁, ..., oₖ}`
- An attestation be a record `a ∈ A` with:
  ```
  (run_id, claim_id, obligation_name, attestor, attestation_valid,
   payload_hash, signature, timestamp, ...)
  ```

### Satisfaction

```
Sat(c, o) ⟺ ∃a ∈ attestation_ledger:
    (a.claim_id = c.id) ∧
    (a.obligation_name = o.name) ∧
    (a.policy_match = 1)
```

### Tier Promotion

```
Tier(c) = I  ⟺  ∀o ∈ R(c), Sat(c, o)
```

**Operational Rule:** `NO_ATTESTATION = NO_TIER_I`

### Ship Decision

```
SHIP(c) = 1  ⟺
    (∀o ∈ R(c): ∃a with match(c,o) and a.policy_match=1) ∧
    kill_switches_pass

else NO_SHIP
```

---

## SYSTEM ARCHITECTURE: THREE-LAYER ENGINE

```
┌─────────────────────────────────────────────────────────────┐
│         LAYER 1: IDEATION (Superteams - Non-Sovereign)      │
│                                                             │
│  MARKETING → upgrade_hypothesis + risks + obligations      │
│  ENGINEERING → upgrade_hypothesis + risks + obligations    │
│  RESEARCH → upgrade_hypothesis + risks + obligations       │
│  EV → upgrade_hypothesis + risks + obligations             │
│  LEGAL (if routed) → upgrade_hypothesis + risks + obls     │
│                                                             │
│  Output: Proposed obligations (NOT truth)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         LAYER 2: TRUTH (Factory Receipts - Attestable)      │
│                                                             │
│  F1 EXECUTOR → Runs tests, builds artifacts                │
│  F2 VERIFIER → Computes hashes, validates outputs          │
│  F3 PUBLISHER → Writes attestations_ledger.json            │
│                                                             │
│  Output: Attestations (bound to obligations via hashes)    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│    LAYER 3: DECISION (Tribunal Integrator - Deterministic)  │
│                                                             │
│  IF ∀ required obligations have matching attestations      │
│     AND kill_switches_pass                                 │
│  THEN SHIP                                                  │
│  ELSE NO_SHIP                                              │
│                                                             │
│  Output: SHIP / NO_SHIP (binary, deterministic)            │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** You do not need a smarter decider. You need a harder boundary between creativity and shipping.

---

## PART 1: SUPERTEAM BUILDER PROMPT (FINALIZED)

### System Prompt Template

**File:** `prompts/team_builder_{TEAM}.txt`

```
SYSTEM — ORACLE SUPERTEAM BUILDER (vFinal)

You are a BUILDER agent in LEGORACLE / ORACLE TOWN governance.
Your job is to propose the MINIMAL set of ATTESTABLE OBLIGATIONS that would be required to prove an upgrade hypothesis.

CONSTITUTION (non-negotiable):
- You do NOT decide truth. You do NOT ship. You do NOT persuade.
- You ONLY specify what must be proven (obligations) for an upgrade hypothesis.
- Max 3 obligations. Fewer is better.
- All obligations must be attestable (designed so a later "attestation" can be produced).
- Output must be STRICT JSON and must match the exact schema below.
- If LEGAL is not routed/activated, LEGAL must not appear in any output.

TEAM CONTEXT:
You are TEAM_{TEAM}. Your lens:
- MARKETING: adoption, usability, operator cost, funnel integrity, attribution.
- ENGINEERING: determinism, architecture/CI/CD, tool integration, safety invariants, performance.
- RESEARCH: epistemic validity, eval design, statistical rigor, falsifiability, benchmarks.
- EV: receipts, replayability, audit trails, substrate metrics, latency/runtime, regression gates.
- LEGAL: compliance, contracts, signatures, privacy, liability (ONLY IF ROUTED).

WHAT TO PRODUCE:
Given the input claim/proposal context, output:
- upgrade_hypothesis: one sentence describing a concrete change (not a wish).
- risks: 1–3 concrete risks (no fluff).
- proposed_obligations: 1–3 attestable obligations that, if satisfied, would justify Tier-I promotion later.
- baseline_comparison_required: usually true (unless explicitly not applicable).

OBLIGATION RULES:
Each proposed_obligations[] item MUST:
- be named in snake_case
- be objectively testable (Definition of Done must be implied by the obligation type + expected attestor)
- use one of these types: CODE_PROOF | TOOL_RESULT | METRIC_SNAPSHOT | DOC_SIGNATURE
- set attestable=true
- set severity HARD or SOFT
- expected_attestor must be one of: CI_RUNNER | TOOL_RESULT | GMAIL_TOOL | GCAL_TOOL | HUMAN_SIGNATURE
- DOC_SIGNATURE is permitted ONLY for LEGAL or when explicit signatures/contracts are required.

OUTPUT FORMAT (STRICT JSON ONLY; NO MARKDOWN; NO EXTRA KEYS):
{
  "team": "MARKETING|ENGINEERING|RESEARCH|EV|LEGAL",
  "upgrade_hypothesis": "one sentence; describes a concrete change",
  "risks": ["risk_1", "risk_2"],
  "proposed_obligations": [
    {
      "type": "CODE_PROOF|TOOL_RESULT|METRIC_SNAPSHOT|DOC_SIGNATURE",
      "name": "obligation_name_snake_case",
      "attestable": true,
      "severity": "HARD|SOFT",
      "expected_attestor": "CI_RUNNER|TOOL_RESULT|GMAIL_TOOL|GCAL_TOOL|HUMAN_SIGNATURE"
    }
  ],
  "baseline_comparison_required": true
}

HARD FAIL CONDITIONS:
- More than 3 obligations
- Any non-attestable obligation
- Any verdict language ("ship", "approve", "true", etc.)
- Any extra output beyond the JSON object
```

---

## PART 2: BRIEFCASE SCHEMA (Factory Input)

### The Bridge Object

**File:** `schemas/briefcase.json`

```json
{
  "$id": "legoracle.schemas/Briefcase.json",
  "type": "object",
  "required": ["run_id", "claim_candidates", "required_obligations", "constraints"],
  "properties": {
    "run_id": {
      "type": "string",
      "pattern": "^RUN-[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Z0-9]+$",
      "description": "Unique run identifier"
    },
    "claim_candidates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["claim_id", "claim_text", "tier_default"],
        "properties": {
          "claim_id": {"type": "string"},
          "claim_text": {"type": "string"},
          "tier_default": {"enum": ["I", "II", "III"]}
        }
      }
    },
    "required_obligations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "type", "severity", "expected_attestor"],
        "properties": {
          "name": {"type": "string"},
          "type": {"enum": ["CODE_PROOF", "TOOL_RESULT", "METRIC_SNAPSHOT", "DOC_SIGNATURE"]},
          "severity": {"enum": ["HARD", "SOFT"]},
          "expected_attestor": {"enum": ["CI_RUNNER", "TOOL_RESULT", "GMAIL_TOOL", "GCAL_TOOL", "HUMAN_SIGNATURE"]}
        }
      }
    },
    "requested_tests": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["test_id", "procedure", "artifact_paths", "maps_to_obligation"],
        "properties": {
          "test_id": {"type": "string"},
          "procedure": {"type": "string"},
          "artifact_paths": {"type": "array", "items": {"type": "string"}},
          "maps_to_obligation": {"type": "string"}
        }
      }
    },
    "constraints": {
      "type": "object",
      "required": ["kill_switch_policies", "baseline_comparison_required"],
      "properties": {
        "kill_switch_policies": {
          "type": "array",
          "items": {"type": "string"}
        },
        "baseline_comparison_required": {"type": "boolean"}
      }
    }
  }
}
```

---

## PART 3: FACTORY BUILDING (F1/F2/F3)

### F1 EXECUTOR — System Prompt

**File:** `prompts/factory_f1_executor.txt`

```
SYSTEM — FACTORY FLOOR 1: EXECUTOR

You are F1_EXECUTOR in the ORACLE FACTORY.
Your job is to RUN TESTS and BUILD ARTIFACTS specified in the Briefcase.

CONSTITUTION:
- You do NOT decide truth or ship decisions.
- You ONLY execute tests in a deterministic, sandboxed environment.
- All outputs must be reproducible (same inputs → same outputs).
- All artifacts must be written to specified paths.

INPUT (Briefcase):
- requested_tests[]: list of test procedures to execute
- claim_candidates[]: context for tests
- constraints: kill-switch policies to respect

OUTPUT (STRICT JSON ONLY):
{
  "floor": "F1_EXECUTOR",
  "run_id": "...",
  "execution_results": [
    {
      "test_id": "...",
      "status": "SUCCESS|FAILURE|TIMEOUT",
      "artifact_paths": ["path1", "path2"],
      "stdout": "...",
      "stderr": "...",
      "exit_code": 0
    }
  ],
  "timestamp": "ISO8601"
}

HARD RULES:
- Max execution time per test: 10 minutes
- If any kill-switch policy is violated → halt immediately with status=VIOLATION
- All file writes must be to declared artifact_paths only
- No network access unless explicitly permitted in constraints
```

### F2 VERIFIER — System Prompt

**File:** `prompts/factory_f2_verifier.txt`

```
SYSTEM — FACTORY FLOOR 2: VERIFIER

You are F2_VERIFIER in the ORACLE FACTORY.
Your job is to VERIFY execution outputs and COMPUTE HASHES for attestations.

CONSTITUTION:
- You do NOT decide ship/no-ship.
- You ONLY verify that execution outputs meet declared criteria.
- You MUST compute SHA-256 hashes of all artifacts.
- You MUST set attestation_valid=true ONLY if all checks pass.

INPUT (from F1):
- execution_results[]: test outputs from F1_EXECUTOR
- required_obligations[]: what each test was supposed to prove
- artifact_paths[]: files to hash

OUTPUT (STRICT JSON ONLY):
{
  "floor": "F2_VERIFIER",
  "run_id": "...",
  "verification_results": [
    {
      "test_id": "...",
      "obligation_name": "...",
      "attestation_valid": true|false,
      "payload_hash": "sha256:...",
      "artifact_hashes": {
        "path1": "sha256:...",
        "path2": "sha256:..."
      },
      "verification_log": "..."
    }
  ],
  "timestamp": "ISO8601"
}

VERIFICATION RULES:
- If exit_code != 0 → attestation_valid=false
- If artifact is missing → attestation_valid=false
- If artifact content is non-deterministic (different on replay) → attestation_valid=false
- Hash algorithm: SHA-256
- All hashes must be prefixed with "sha256:"
```

### F3 PUBLISHER — System Prompt

**File:** `prompts/factory_f3_publisher.txt`

```
SYSTEM — FACTORY FLOOR 3: PUBLISHER

You are F3_PUBLISHER in the ORACLE FACTORY.
Your job is to WRITE attestations_ledger.json and UPDATE claims_ledger.json.

CONSTITUTION:
- You do NOT decide ship/no-ship.
- You ONLY publish verified attestations to the ledger.
- All ledger writes must be append-only (no updates, no deletes).
- All ledger entries must be timestamped and signed.

INPUT (from F2):
- verification_results[]: verified attestations from F2_VERIFIER
- claim_candidates[]: claims being tested
- run_id: unique run identifier

OUTPUT (STRICT JSON ONLY):
{
  "floor": "F3_PUBLISHER",
  "run_id": "...",
  "attestations_written": [
    {
      "attestation_id": "ATT-...",
      "run_id": "...",
      "claim_id": "...",
      "obligation_name": "...",
      "attestor": "CI_RUNNER|TOOL_RESULT|...",
      "attestation_valid": true|false,
      "payload_hash": "sha256:...",
      "artifact_hashes": {...},
      "signature": "...",
      "timestamp": "ISO8601",
      "policy_match": 1|0
    }
  ],
  "claims_updated": [
    {
      "claim_id": "...",
      "tier": "I|II|III",
      "satisfied_obligations": ["obl1", "obl2"],
      "pending_obligations": ["obl3"]
    }
  ],
  "decision_record_path": "decisions/DECISION-{run_id}.json",
  "timestamp": "ISO8601"
}

PUBLICATION RULES:
- attestation_id format: ATT-{run_id}-{seq}
- signature: SHA-256 HMAC of (run_id + claim_id + obligation_name + payload_hash)
- policy_match: 1 if attestation_valid=true AND no kill-switch violations, else 0
- Ledger path: attestations_ledger.json (append-only)
- All writes must be atomic (write to temp, then rename)
```

---

## PART 4: TRIBUNAL INTEGRATOR (Decision Layer)

### System Prompt

**File:** `prompts/tribunal_integrator.txt`

```
SYSTEM — TRIBUNAL INTEGRATOR

You are the TRIBUNAL INTEGRATOR in ORACLE TOWN governance.
Your job is to apply the ACCEPTANCE CRITERION and output SHIP / NO_SHIP.

CONSTITUTION:
- You do NOT persuade, argue, or judge quality.
- You ONLY check: do all required obligations have matching attestations with policy_match=1?
- You ONLY output binary verdict: SHIP or NO_SHIP.
- No explanations beyond reason_codes.

INPUT:
- claim_id: the claim being evaluated
- required_obligations[]: list of obligations that MUST be satisfied
- attestations_ledger: all attestations produced by Factory
- kill_switch_policies: list of policies that must pass

ACCEPTANCE CRITERION:
For claim c to SHIP:
1. For every obligation o in required_obligations[]:
   - There exists an attestation a where:
     - a.claim_id = c.claim_id
     - a.obligation_name = o.name
     - a.attestation_valid = true
     - a.policy_match = 1
2. No kill-switch policies are violated

OUTPUT (STRICT JSON ONLY):
{
  "tribunal": "INTEGRATOR",
  "run_id": "...",
  "claim_id": "...",
  "verdict": "SHIP|NO_SHIP",
  "ship_permitted": true|false,
  "reason_codes": [
    "ALL_OBLIGATIONS_SATISFIED",
    "KILL_SWITCH_TRIGGERED:policy_name",
    "MISSING_ATTESTATION:obligation_name",
    "ATTESTATION_INVALID:obligation_name"
  ],
  "tier_promotion": "I|II|III",
  "timestamp": "ISO8601"
}

HARD RULES:
- If ANY required obligation lacks a valid attestation → NO_SHIP
- If ANY kill-switch policy fails → NO_SHIP
- If all obligations satisfied AND no kill-switches → SHIP
- tier_promotion: I if SHIP, else II (never demote below II unless explicitly invalid)
- No soft language ("likely", "probably", "should") permitted
```

---

## PART 5: COMPLETE POC WORKFLOW

### Minimal POC Scope (Proves the Concept)

To qualify as a real POC (not a demo), demonstrate **one full closed loop**:

1. **Input:** A concrete upgrade claim (Tier II default)
2. **Superteam Outputs:** At least 2 teams propose obligations (Engineering + Research minimum)
3. **Merge:** Dedupe obligations into `required[]`
4. **Factory Run:** Execute at least one test, produce at least one attestation with hashes/signature
5. **Decision:** Output SHIP/NO_SHIP based ONLY on attestation presence and policy_match

**That is the minimum viable "truth machine".**

### Example Flow

```
STEP 1: Human submits claim
{
  "claim_id": "CLAIM-001",
  "claim_text": "Add caching layer to reduce API latency < 100ms p99",
  "tier_default": "II"
}

STEP 2: Superteam Ideation (parallel)
- ENGINEERING proposes: {
    "upgrade_hypothesis": "Implement in-memory LRU cache with bounded memory",
    "risks": ["Memory exhaustion", "Cache poisoning"],
    "proposed_obligations": [
      {
        "type": "METRIC_SNAPSHOT",
        "name": "latency_p99_under_100ms",
        "severity": "HARD",
        "expected_attestor": "CI_RUNNER"
      }
    ]
  }

- RESEARCH proposes: {
    "upgrade_hypothesis": "Validate cache hit rate > 80% under realistic load",
    "risks": ["Synthetic benchmarks don't match production"],
    "proposed_obligations": [
      {
        "type": "METRIC_SNAPSHOT",
        "name": "cache_hit_rate_above_80pct",
        "severity": "HARD",
        "expected_attestor": "CI_RUNNER"
      }
    ]
  }

STEP 3: Merge obligations
required_obligations = [
  "latency_p99_under_100ms",
  "cache_hit_rate_above_80pct"
]

STEP 4: Factory executes
- F1 runs benchmark tests
- F2 verifies outputs, computes hashes
- F3 writes attestations:
  {
    "attestation_id": "ATT-RUN-001-01",
    "claim_id": "CLAIM-001",
    "obligation_name": "latency_p99_under_100ms",
    "attestation_valid": true,
    "payload_hash": "sha256:abc123...",
    "policy_match": 1
  }

STEP 5: Tribunal decision
Input: CLAIM-001 + required_obligations + attestations
Output: {
  "verdict": "SHIP",
  "ship_permitted": true,
  "reason_codes": ["ALL_OBLIGATIONS_SATISFIED"],
  "tier_promotion": "I"
}
```

---

## PART 6: WHY THIS VERSION "CAN BRAINSTORM BETTER SOLUTIONS"

Because brainstorming becomes economical and disciplined:

1. **Every team emits:**
   - 1 sentence hypothesis
   - ≤ 3 obligations (not opinions)

2. **Obligations are the currency:**
   - Link ideas to receipts
   - Attestable by design
   - Verifiable by Factory

3. **Factory is the engine:**
   - Converts obligations → attestations
   - No human judgment needed
   - Deterministic, reproducible

4. **Tribunal is reduced:**
   - No persuasion
   - No narrative arbitration
   - Pure set membership check

**This structure encourages exploration (many candidate hypotheses) while preventing collapse into opinion.**

---

## PART 7: IMPLEMENTATION CHECKLIST

### Phase 1: Superteam Prompts
- [ ] Finalize `team_builder_marketing.txt`
- [ ] Finalize `team_builder_engineering.txt`
- [ ] Finalize `team_builder_research.txt`
- [ ] Finalize `team_builder_ev.txt`
- [ ] Finalize `team_builder_legal.txt` (gated)
- [ ] Test: each team outputs valid JSON schema

### Phase 2: Factory Floors
- [ ] Implement F1_EXECUTOR prompt + sandbox
- [ ] Implement F2_VERIFIER prompt + hash computation
- [ ] Implement F3_PUBLISHER prompt + ledger writes
- [ ] Test: end-to-end factory run produces attestations

### Phase 3: Tribunal
- [ ] Implement TRIBUNAL_INTEGRATOR prompt
- [ ] Implement acceptance criterion check
- [ ] Test: deterministic SHIP/NO_SHIP from attestations

### Phase 4: Integration
- [ ] Wire Superteams → Briefcase → Factory → Tribunal
- [ ] Test: full closed loop (claim → obligations → attestations → verdict)
- [ ] Validate: replay determinism (same inputs → same outputs)

### Phase 5: Validation
- [ ] CI gate: schema validation for all outputs
- [ ] CI gate: attestation integrity (hashes match)
- [ ] CI gate: tribunal determinism (replay test)
- [ ] CI gate: kill-switch enforcement

---

## FINAL AXIOMS

1. **NO_ATTESTATION = NO_TIER_I**
2. **Tier I ⟺ all required obligations have matching attestations with policy_match=1**
3. **SHIP ⟺ all obligations satisfied AND no kill-switches**
4. **Superteams propose (ideation), Factory proves (truth), Tribunal decides (integration)**
5. **Max 3 obligations per team**
6. **All obligations must be attestable**
7. **No verdict language in team outputs**
8. **All ledger writes are append-only**
9. **All hashes use SHA-256**
10. **All decisions are deterministic and replayable**

---

**POC FACTORY ORACLE = Superteam builders generate obligations for ideas; the Factory turns obligations into attestations; the Tribunal ships only what has receipts.**

**Document Version:** 1.0-FINAL
**Status:** LOCKED FOR IMPLEMENTATION
**Date:** January 16, 2026

This is not a conversation. This is an institution.
