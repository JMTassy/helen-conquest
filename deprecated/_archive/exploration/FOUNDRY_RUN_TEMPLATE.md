# Foundry Town Run Template

**Use this template** to scaffold a new Foundry Town project run.

Copy this entire section, replace `[BRACKETS]`, and you have a complete run structure.

---

## RUN MANIFEST

**File:** `runs/[PROJECT_NAME]/MANIFEST.md`

```markdown
# [PROJECT_NAME] — Foundry Town Run

**Subject:** [One sentence: What are we exploring?]

**Audience:** [Who is this for? (executives, engineers, team, etc.)]

**Format:** [Output type: memo, doc, guide, proposal, code, other]

**Constraints:**
- Duration: [Time window: 45m, 90m, 2h, etc.]
- Scope: [What's in? What's out?]
- Tone: [Formal, casual, technical, narrative, etc.]

---

## Status & Timeline

| Phase | Start | End | Status | Notes |
|-------|-------|-----|--------|-------|
| Phase 0: Init | [TIME] | [TIME] | ✅ | Run created |
| Phase 1: Exploration | [TIME] | [TIME] | ⏳ | Divergent: facts, structure, assumptions |
| Phase 2: Tension | [TIME] | [TIME] | ⏳ | Mandatory: red-team all claims |
| Phase 3: Drafting | [TIME] | [TIME] | ⏳ | Convergent: prose from claims |
| Phase 4: Editorial | [TIME] | [TIME] | ⏳ | Collapse: merge, cut, finalize |
| Phase 5: Termination | [TIME] | [TIME] | ⏳ | Deliver or abort (explicit) |

---

## Claim Summary

- **Pending:** [N] (awaiting curation)
- **Accepted:** [N] (flows to drafting)
- **Rejected:** [N] (audit trail)
- **Merged:** [N] (synthesis)

---

## Key Decisions

[Log major editorial decisions here as you make them]

- **[DATE]:** [Decision & rationale]
- **[DATE]:** [Decision & rationale]

---

## Artifacts

- **v0_fragments.md:** Raw notes from Exploration phase
- **v1_draft.md:** Converged draft from Drafting phase
- **v2_editorial.md:** Final artifact (Editorial Collapse)

---

## Next Steps

[Document what unlocks after this run completes]

- [ ] [Action Item 1]
- [ ] [Action Item 2]

---

**Created:** [TIMESTAMP]
**Last Updated:** [TIMESTAMP]
**Run Lead:** [YOUR NAME]
```

---

## CLAIMS STRUCTURE

**File:** `runs/[PROJECT_NAME]/claims/pending.md`

```markdown
# Pending Claims

[Claims awaiting Foreman curation. See accepted.md, rejected.md, merged.md for curated items.]

---

CLAIM: R-001
type: evidence
statement: "[The claim in 1-2 sentences]"
source: "[Reference: file, URL, agent name]"
confidence: [low | medium | high]
author: [Researcher | Skeptic | Writer | Structurer | etc.]
status: pending
timestamp: [ISO 8601, e.g., 2026-02-13T10:15:00Z]

---

CLAIM: T-001
type: structure
statement: "[Suggested outline or section]"
source: "[Structurer's reasoning]"
confidence: [low | medium | high]
author: Structurer
status: pending
timestamp: [ISO 8601]

---

[Continue for each claim submitted during work]
```

---

## ACCEPTED CLAIMS

**File:** `runs/[PROJECT_NAME]/claims/accepted.md`

```markdown
# Accepted Claims

[Foreman-curated claims that flow to Drafting phase.]

---

CLAIM: R-001
type: evidence
statement: "[ACCEPTED: This flows to draft prose]"
source: "[Reference]"
confidence: high
author: Researcher
status: accepted
timestamp: [ISO 8601]
accepted_by: Foreman
acceptance_reason: "[Why Foreman accepted this]"

---

[Accepted claims only. Rejected items go to rejected.md.]
```

---

## REJECTED CLAIMS

**File:** `runs/[PROJECT_NAME]/claims/rejected.md`

```markdown
# Rejected Claims

[Audit trail: claims Foreman declined. Keep for historical record.]

---

CLAIM: C-042
type: critique
statement: "[Original statement]"
source: "[Reference]"
confidence: medium
author: Skeptic
status: rejected
timestamp: [ISO 8601]
rejected_by: Foreman
rejection_reason: "[Why Foreman rejected this: off-scope, redundant, weak evidence, etc.]"

---

[All rejections logged. No exceptions. Transparency.]
```

---

## MERGED CLAIMS

**File:** `runs/[PROJECT_NAME]/claims/merged.md`

```markdown
# Merged Claims

[Claims combined by Synthesizer. Shows lineage: which claims merged into which.]

---

CLAIM: M-001
type: synthesis
statement: "[Combined statement from R-001 + R-003]"
merged_from: [R-001, R-003]
confidence: high
author: Synthesizer
status: merged
timestamp: [ISO 8601]
merge_reason: "[Why these were combined: overlap, complementary, avoid redundancy]"

---

[Shows how claims were consolidated.]
```

---

## PHASE TRANSITIONS LOG

**File:** `runs/[PROJECT_NAME]/logs/phase_transitions.md`

```markdown
# Phase Transitions Timeline

[Hard record: when did each phase change, why, what was completed.]

---

## Phase 0 → Phase 1 (Exploration)

**Timestamp:** [ISO 8601]
**Trigger:** Run initialized
**Status:** ✅ Complete
**Output:** runs/[PROJECT_NAME]/ structure created

---

## Phase 1 → Phase 2 (Tension)

**Timestamp:** [ISO 8601]
**Trigger:** Sufficient facts gathered, outline sketched
**Status:** ⏳ In Progress
**Accepted Claims:** [N] (these are now under red-team review)
**Pending Claims:** [N] (on hold until Tension phase complete)

---

## Phase 2 → Phase 3 (Drafting)

**Timestamp:** [ISO 8601]
**Trigger:** Contradictions resolved, contested items marked
**Status:** ⏳ In Progress
**Action:** Writer begins drafting from accepted claims
**Awaiting:** v1_draft.md completion

---

## Phase 3 → Phase 4 (Editorial Collapse)

**Timestamp:** [ISO 8601]
**Trigger:** All accepted claims drafted; gaps marked
**Status:** ⏳ In Progress
**Input:** v1_draft.md (4,200 words)
**Target:** v2_editorial.md (2,500 words, 40% reduction)

---

## Phase 4 → Phase 5 (Termination)

**Timestamp:** [ISO 8601]
**Trigger:** Editorial collapse complete; artifact coherent
**Status:** ⏳ Awaiting decision
**Options:** Deliver (✅) or Abort (❌)
**Decision:** [TO BE MADE]

---

[One entry per phase transition. Hard timestamps. No vagueness.]
```

---

## SOURCES & REFERENCES

**File:** `runs/[PROJECT_NAME]/sources/references.md`

```markdown
# Sources & References

[Organized by type. All evidence claims link here.]

---

## Primary Sources

- **[Title]** — [URL or file path]
  - Evidence: [What this source provides]
  - Claims citing: [R-001, R-003, R-007]

---

## Secondary Sources

- **[Article/Paper/Document]** — [Reference]
  - Summary: [One sentence]
  - Claims citing: [R-002]

---

## Internal References

- **[CLAUDE.md]** — [File path]
  - Evidence: Constitutional rules, K-gates, governance model
  - Claims citing: [R-005, T-001]

---

## Precedents & Comparables

- **[Similar project/framework]** — [Reference]
  - How it applies: [1-2 sentences]
  - Claims citing: [R-004]

---

[Keep this organized. Each claim should have a traceable source.]
```

---

## DRAFTS

### v0 — Raw Fragments

**File:** `runs/[PROJECT_NAME]/drafts/v0_fragments.md`

```markdown
# Raw Fragments (Phase 1: Exploration)

[Unorganized notes from Exploration phase. Not prose. Not structured. Raw ideas.]

---

## Quick Thoughts on [Topic]

- [Idea 1]
- [Idea 2]
- [Idea 3 — but wait, this contradicts Idea 1]

---

## Outline Sketch (Structurer's Draft)

1. Context: [Why now?]
2. Problem: [What's broken?]
3. Solution: [What should we do?]
4. Timeline: [When?]

---

## Questions Still Open

- Is assumption X true?
- Does precedent Y apply?
- What if Z changes?

---

[This is scratch work. Keep it raw. Refine later.]
```

### v1 — Convergent Draft

**File:** `runs/[PROJECT_NAME]/drafts/v1_draft.md`

```markdown
# Draft v1: Convergent

[Prose from accepted claims. Gaps marked explicitly as `[DRAFT: ...]`.]

---

## Introduction

[Opening para: context + why this matters]

---

## Section 1: [Name]

[Prose from accepted claims T-001, R-002, R-005]

[Connecting sentences between claims. No invention. Gaps marked.]

[DRAFT: Expand with concrete example here? (R-009 would help)]

---

## Section 2: [Name]

[Prose from claims R-003, R-004]

[Transition: "This leads to the second point: ..."]

[DRAFT: Statistics missing; cite Researcher's source]

---

## Conclusion

[Summary of accepted claims. No new ideas.]

---

## Explicit Gaps

- [Gap 1: Missing evidence on X]
- [Gap 2: Contradictory claims on Y — awaiting Editor decision]
- [Gap 3: Timeline is vague; needs specificity]

---

[This is a complete draft, but has gaps. Ready for Editorial Collapse.]
```

### v2 — Editorial Final

**File:** `runs/[PROJECT_NAME]/drafts/v2_editorial.md`

```markdown
# FINAL ARTIFACT: [PROJECT_NAME]

**Subject:** [Restate clearly]

---

## Key Message

[1-2 sentence summary]

---

## Main Content

[Section 1 — no gaps, coherent, 40% shorter than v1]

[Section 2 — similarly compressed]

[Section 3 — only highest-value content]

---

## Recommendations

[Specific, actionable, tied to evidence]

---

## Next Steps

[What unlocks after this?]

---

**Status:** ✅ FINAL (ready for distribution)
**Word Count:** [X] (target: 2,500 — 40% reduction from v1)
**Reduction:** [N]% achieved
**Decision Log:** See EDITORIAL_LOG.md
```

---

## EDITORIAL DECISION LOG

**File:** `runs/[PROJECT_NAME]/logs/EDITORIAL_LOG.md`

```markdown
# Editorial Collapse Decisions

[Record every unilateral editorial cut and contradiction resolution.]

---

## Cuts Made

### Cut #1: Historical Background Section (Pages 1-3)

**What was removed:** Full history of [topic] from 1990 to present

**Why:** Context, not argument. Executive audience needs present-day reasoning.

**Alternative rejected:** Move to appendix (out of scope for memo format)

**Word count:** 800 words removed

**Confidence:** High (historical context is not required for decision-making)

---

### Cut #2: Competing Framework Discussion (Page 5)

**What was removed:** Paragraph comparing [Framework A] vs. [Framework B]

**Why:** Both compete with our recommended model. Including them weakens our case.

**Alternative considered:** Footnote (decided: too distracting)

**Word count:** 350 words removed

---

## Contradictions Resolved

### Contradiction #1: Governance Authority Model (Claims R-005 vs. R-008)

**R-005:** "Authority flows top-down (CEO → Director → Team)"

**R-008:** "Authority flows peer-based (teams decide collectively)"

**Resolution:** Model A (top-down) chosen

**Rationale:** Audience (executives) requires clarity on hierarchy. Peer-based model is aspirational but not applicable in current org structure.

**Editorial decision:** Keep R-005; merge R-008 into footnote (alternative considered for future)

---

### Contradiction #2: Timeline Feasibility

**R-003:** "Implementation possible in Q2 (8 weeks)"

**C-041:** "Challenge: Resource constraints suggest 12+ weeks"

**Resolution:** 10-week timeline with phased rollout

**Rationale:** Compromise between ambition and realism. Addresses skeptic's concern while maintaining aggressive schedule.

**Editorial decision:** Create new claim combining both constraints (M-010)

---

## Tone & Voice Decisions

**Target tone:** Formal, authoritative, executive-ready

**Changes made:**
- [ ] Removed casual language (e.g., "super important" → "critical")
- [ ] Unified tense (past/present/future mixed in v1 → all future in v2)
- [ ] Added transitional headers for clarity
- [ ] Replaced jargon with plain language (or added glossary)

---

## Structure Reordering

**Original (v1):** Problem → Context → Solution → Timeline

**Final (v2):** Context → Problem → Solution → Timeline

**Rationale:** Executives need context first to understand the problem. Order matches their decision-making pattern.

---

## Summary

- **Starting word count (v1):** 4,200
- **Ending word count (v2):** 2,520
- **Reduction:** 40% (1,680 words removed)
- **Decision method:** Unilateral editorial authority (no voting)
- **Contradictions resolved:** 2
- **Tone enforced:** ✅ Consistent
- **Ready for delivery:** ✅ Yes

---

[Sign off as Editor when complete]

**Editor:** [Name]
**Timestamp:** [ISO 8601]
**Status:** ✅ FINAL
```

---

## HOW TO USE THIS TEMPLATE

1. **Copy the MANIFEST section** → Create `runs/[PROJECT_NAME]/MANIFEST.md`
2. **Create claims files** → `claims/pending.md`, `accepted.md`, rejected.md`, `merged.md`
3. **Create logs** → `logs/phase_transitions.md`, `logs/EDITORIAL_LOG.md` (add to later)
4. **Create drafts** → `drafts/v0_fragments.md`, `v1_draft.md`, `v2_editorial.md` (populate as you work)
5. **Create sources** → `sources/references.md` (as you gather evidence)

---

## Quick Commands to Set Up

```bash
# Create the run folder
mkdir -p runs/[PROJECT_NAME]/{claims,drafts,logs,sources}

# Create empty files with headers
touch runs/[PROJECT_NAME]/MANIFEST.md
touch runs/[PROJECT_NAME]/claims/{pending,accepted,rejected,merged}.md
touch runs/[PROJECT_NAME]/drafts/{v0_fragments,v1_draft,v2_editorial}.md
touch runs/[PROJECT_NAME]/logs/{phase_transitions,EDITORIAL_LOG}.md
touch runs/[PROJECT_NAME]/sources/references.md

# Fill in MANIFEST.md manually
# Then use /claim, /phase-next, /editorial-collapse to populate other files
```

---

**Or use the skill:**

```bash
/foundry-new "Your subject" --audience X --format Y --duration Zm
```

This generates all structure automatically.

---

**Status:** Template ready for use
**Last Updated:** 2026-02-13
**Next:** Create your first run!
