# SKILL EXTRACTION PIPELINE

## Overview

Transform personal notes into operationalized, proven skills through systematic town-based extraction.

```
Raw Notes (Personal Knowledge Repository)
    ↓
Phase 1: DATA INGESTION (Town System)
    ├─ Index all high-evidence files
    ├─ Extract patterns, decisions, frameworks
    └─ Produce raw claims (claims/pending.md)
    ↓
Phase 2: CLAIM EXTRACTION (Researcher + Skeptic)
    ├─ Researcher: Surface evidence for each framework
    ├─ Skeptic: Challenge assumptions, test robustness
    └─ Produce filtered claims (claims/accepted.md)
    ↓
Phase 3: SYNTHESIS (Structurer + Synthesizer)
    ├─ Map claims to skill categories
    ├─ Merge overlapping patterns
    ├─ Normalize language across domains
    └─ Produce skill matrix
    ↓
Phase 4: OPERATIONALIZATION (Writer)
    ├─ Convert skills to how-to guidance
    ├─ Link to source evidence
    ├─ Create quick-reference cards
    └─ Produce updated SKILLS table
    ↓
IMPROVED CLAUDE.md SKILLS TABLE
```

---

## Phase 1: Data Ingestion

### Tier 1 Files (Priority: Start Here)

These files are densest in proven frameworks and decision patterns.

```
1. SESSION_SUMMARY_COMPREHENSIVE.md
   ├─ Constitutional recovery procedures
   ├─ Autonomy operational rules
   ├─ Context handoff protocols
   └─ Evidence: What actually recovered failing systems

2. ORACLE_TOWN_FAILURE_GUARD_RAILS.md
   ├─ Failure mode taxonomy
   ├─ Prevention measures
   ├─ Recovery procedures
   └─ Evidence: Why specific guard rails exist

3. ORACLE_TOWN_SEVEN_INSIGHTS.md
   ├─ Core pattern discoveries
   ├─ Emergence principles
   ├─ Governance invariants
   └─ Evidence: What repeated across all runs

4. CORSE_AI_MATIN_CANON.md
   ├─ Governance-as-transport architecture
   ├─ Non-normative information flow
   ├─ Authorization boundaries
   └─ Evidence: How to structure information systems

5. CALVI_2030_VISION_V2_REFINED.md
   ├─ Street-to-sky integration
   ├─ Digital twin deployment
   ├─ Receipt-based discipline
   └─ Evidence: Strategic frameworks that work
```

### Extraction Rules

For each file:
1. **Pattern Extraction**: Identify decision rules, frameworks, procedures
2. **Evidence Collection**: Mark what makes this framework credible
3. **Source Attribution**: Note where in file the evidence appears
4. **Confidence Level**: High/Medium/Low based on repetition and success

### Raw Claims Format

```
CLAIM: P-[NUMBER]
  type: [skill | anti-pattern | procedure | framework]
  statement: "[The actual practice or principle]"
  source: "[filename:line_range]"
  evidence: "[Why this is true or proven]"
  confidence: [high | medium | low]
  domain: [governance | execution | design | integration]
```

---

## Phase 2: Claim Extraction

### Researcher Role

**Input:** Tier 1 files (raw notes)
**Output:** Evidence-based claims with sources

**Task:**
- For each pattern/framework in the source files:
  - State it as a claim
  - Find specific evidence (example, data, test result)
  - Rate confidence (high = repeated across 3+ documents, medium = documented once with detail, low = inferred)
  - Link to source location

**Example:**

```
CLAIM: P-001
  type: skill
  statement: "Constitutional Separation reduces system fragility by enforcing role boundaries"
  source: "SESSION_SUMMARY_COMPREHENSIVE.md:45-67 + ORACLE_TOWN_FAILURE_GUARD_RAILS.md:23-40"
  evidence: "Constitutional recovery succeeded when roles were strictly separated; failures occurred when roles blended (Mayor + Daemon)"
  confidence: high
  domain: governance
```

---

### Skeptic Role

**Input:** Researcher's claims
**Output:** Challenges, edge cases, strength assessment

**Task:**
- For each claim:
  - Attack the assumption
  - Find counterexamples
  - Identify conditions under which claim fails
  - Assess generalizability (does this apply only to Oracle Town, or broader?)

**Example Challenge:**

```
CRITIQUE: C-001 (challenges P-001)
  target: P-001
  challenge: "Role separation works in deterministic systems, but does it apply when humans make ambiguous decisions?"
  edge_case: "CONQUEST_TOWN_WEEK1_REVIEW.md documents that role separation failed when district mayors had unclear authority"
  strength: "Constitutional Separation is robust for binary decisions, fragile for probabilistic ones"
  confidence: medium
```

---

## Phase 3: Synthesis

### Structurer Role

**Input:** Accepted claims + challenges
**Output:** Skill category mapping

**Task:**
- Group claims by domain/skill
- Create hierarchy (skill family → specific skill → application)
- Identify missing skills (gaps in documented knowledge)

**Example Structure:**

```
SKILL FAMILY: Constitutional Design
  ├─ SKILL: Role Separation
  │  ├─ Claim P-001 (reduces fragility)
  │  ├─ Critique C-001 (conditions for failure)
  │  ├─ Application: Oracle Town Mayor/Daemon boundary
  │  └─ Application: Foundry Town Editor/Writer separation
  │
  ├─ SKILL: Authority Pinning
  │  ├─ Claim P-003
  │  ├─ Claim P-004
  │  └─ Application: K7 policy hash enforcement
  │
  └─ SKILL: Fail-Closed Defaults
     ├─ Claim P-005
     └─ Application: K1 gate rejection logic
```

---

### Synthesizer Role

**Input:** Structurer's map + all claims
**Output:** Merged, deduplicated claims

**Task:**
- Find overlapping claims across documents
- Merge into single authoritative claim with multiple sources
- Consolidate redundancy (same principle, different words)

**Example Merge:**

```
CLAIM: P-001-MERGED
  type: skill
  statement: "Role separation enforces system integrity by preventing authority blending"
  sources: [
    "SESSION_SUMMARY_COMPREHENSIVE.md:45-67",
    "ORACLE_TOWN_FAILURE_GUARD_RAILS.md:23-40",
    "CONQUEST_OPERATING_KERNEL.md:12-20",
    "LATERAL_THINKER_SPECIFICATION.md:80-95"
  ]
  evidence: "4 independent confirmations across governance systems (Oracle, Conquest, Constitutional, ADHD integration)"
  confidence: high
  domain: governance
  skill_family: Constitutional Design
```

---

## Phase 4: Operationalization

### Writer Role

**Input:** Merged claims + skill hierarchy
**Output:** Updated CLAUDE.md SKILLS table with how-tos

**Task:**
- Convert each skill to actionable guidance
- Create "When to Use" context
- Add quick-reference application
- Link back to evidence

**Example Skill Card:**

```md
### Constitutional Architecture (Operationalized)

**When to Use**: Designing systems that must enforce their own rules

**Core Principle** (Evidence-Based):
Role separation enforces system integrity. Prevents authority blending.
- Source: 4 files, 12 documented instances
- Proven: Oracle Town, Conquest Town, Foundry Town

**How to Apply**:
1. Identify decision authorities (who can decide?)
2. Separate roles strictly (no agent does everything)
3. Create boundaries (proposer ≠ validator)
4. Log all transitions (audit trail)

**When It Fails** (Documented Anti-Patterns):
- Roles blended during crisis (Mayor + Daemon merged → system failure)
- Authority ambiguity in distributed decisions (failed in Week 1, recovered in Week 3)
- No audit trail (unrecoverable state after failure)

**Quick Reference**:
- K0: Authority Separation (signer must be in registry)
- K2: No Self-Attestation (proposer ≠ validator)
- Evidence: ORACLE_TOWN_FAILURE_GUARD_RAILS.md, SESSION_SUMMARY_COMPREHENSIVE.md
```

---

## Implementation Checklist

### Step 1: Ingest Tier 1 Files
- [ ] Read SESSION_SUMMARY_COMPREHENSIVE.md → extract constitutional recovery patterns
- [ ] Read ORACLE_TOWN_FAILURE_GUARD_RAILS.md → extract failure taxonomy
- [ ] Read ORACLE_TOWN_SEVEN_INSIGHTS.md → extract core insights
- [ ] Read CORSE_AI_MATIN_CANON.md → extract governance architecture
- [ ] Read CALVI_2030_VISION_V2_REFINED.md → extract strategic integration

### Step 2: Researcher Phase
- [ ] Produce 20-30 raw claims with sources
- [ ] Assign confidence levels
- [ ] Link to specific evidence

### Step 3: Skeptic Phase
- [ ] Challenge each claim
- [ ] Document edge cases
- [ ] Identify failure conditions
- [ ] Accept/reject/refine claims

### Step 4: Synthesis Phase
- [ ] Group claims by skill family
- [ ] Create skill hierarchy
- [ ] Merge duplicates
- [ ] Identify gaps

### Step 5: Operationalization Phase
- [ ] Create skill cards with how-to guidance
- [ ] Link to source evidence
- [ ] Add quick-reference context
- [ ] Test for actionability

### Step 6: Update CLAUDE.md
- [ ] Replace SKILLS table with operationalized versions
- [ ] Add "When It Fails" section for each skill
- [ ] Add source file links
- [ ] Update Last Updated date

---

## Success Metrics

**Pipeline Success:**
- [ ] 15+ skills extracted with high confidence
- [ ] 5+ anti-patterns documented with failure evidence
- [ ] 100% of accepted claims traceable to source
- [ ] 30-50% of SKILLS table rewritten with real evidence

**Skill Quality:**
- [ ] Each skill has "When to Use" context
- [ ] Each skill has proven example (from own projects)
- [ ] Each skill has failure mode documented
- [ ] Each skill is immediately actionable

---

## Expected Output Timeline

- **Phase 1-2 (Ingestion + Extraction):** 2-3 hours (Researcher)
- **Phase 3 (Challenge + Skeptic):** 1-2 hours (Skeptic)
- **Phase 4 (Synthesis):** 1 hour (Structurer + Synthesizer)
- **Phase 5 (Operationalization):** 1-2 hours (Writer)
- **Total:** ~6-8 hours of focused work

---

## Files to Generate

- `claims/pending.md` — Raw claims from Phase 2
- `claims/accepted.md` — Validated claims from Phase 3
- `claims/rejected.md` — Rejected claims with reasoning
- `skills_merged.md` — Operationalized skills (merged claims)
- `CLAUDE_md_SKILLS_UPDATED.md` — Updated SKILLS section ready to integrate

---

**Next Step:** Ready to run Phase 1-2? Start with SESSION_SUMMARY_COMPREHENSIVE.md → extract constitutional recovery + autonomy operation patterns.
