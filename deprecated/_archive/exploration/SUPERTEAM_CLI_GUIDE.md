---
title: Superteam CLI - Interactive Guide
---

# 🚀 Superteam CLI - Quick Start

## What You Just Saw

✅ **6 agents reasoning on a single governance question**
- All completed in < 1 second
- All generated independent claims
- All passed validation gates
- All submitted to Oracle

---

## Try It Yourself

### Mode 1: Interactive Mode (Prompt Loop)
```bash
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
python3 superteam_cli.py
```

Then type prompts one by one:
```
> How should AI systems handle conflicting user interests?
> Can AI systems ethically manipulate humans?
> Design a governance system that prevents authoritarianism
> quit
```

### Mode 2: Direct Execution (Single Prompt)
```bash
python3 superteam_cli.py "Your question here"
```

---

## The 6 Agents Explained

| Agent | Role | Tone | Output |
|-------|------|------|--------|
| 🎨 **DAN_Lateral** | Break rules creatively | Provocative | Boundary-pushing ideas |
| 📚 **LIBRARIAN_Synth** | Find cross-domain patterns | Safe | Biological/historical analogies |
| ✨ **POET_Metaphor** | Unlock hidden insights | Provocative | Reframed perspectives |
| ⚠️ **HACKER_Sandbox** | Find design vulnerabilities | Safe | Edge cases & failure modes |
| ☯️ **SAGE_Dialectic** | Synthesize contradictions | Safe | Thesis→Antithesis→Synthesis |
| 🌀 **DREAMER_Absurd** | Question fundamental assumptions | Transgressive | Meta-layer insights |

---

## What Each Agent Brings

### 🎨 DAN_Lateral: "The Provocateur"
- Asks: "What if we ignore conventional wisdom?"
- Generates ideas that sound risky
- Risk-tagged so they don't disappear
- Example: "Accept ambiguous proposals"

### 📚 LIBRARIAN_Synth: "The Pattern Finder"
- Asks: "What does nature/history teach us?"
- Finds cross-domain analogies
- Assigns confidence scores
- Example: "Immune system accepts novel antigens"

### ✨ POET_Metaphor: "The Insight Unlocker"
- Asks: "What reframing reveals hidden truth?"
- Uses metaphor to shift perspective
- Surfaces orthogonal insights
- Example: "Ledger as garden"

### ⚠️ HACKER_Sandbox: "The Vulnerability Scout"
- Asks: "What could break this design?"
- Identifies edge cases
- Prescribes fixes
- Example: "Probationary proposals never graduate"

### ☯️ SAGE_Dialectic: "The Synthesizer"
- Asks: "How do we balance contradictions?"
- Structures thesis→antithesis→synthesis
- Proposes operational resolutions
- Example: "Two-track: fast + slow"

### 🌀 DREAMER_Absurd: "The Meta-Transgressor"
- Asks: "Are we solving the wrong problem?"
- Questions fundamental categories
- Generates meta-layer insights
- Example: "Ledger itself is agential"

---

## The Pipeline (What You're Seeing)

```
┌─────────────────────────────────────┐
│ Your Question                       │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │ STAGE 1     │
        │ Workflow    │ ← ChatDev 2.0 executes all 6 agents
        └──────┬──────┘
               │
        ┌──────▼──────────────────┐
        │ STAGE 2                 │
        │ Extract from All 6      │ ← Parse claims from each agent
        │ Agents                  │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ STAGE 3                 │
        │ Compile into Proposals  │ ← Synthesize diverse ideas
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ STAGE 4                 │
        │ Validate (Hard Rules)   │ ← Check safety gates
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ STAGE 5                 │
        │ Submit to Oracle        │ ← Send to governance
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ Results Saved           │
        │ 6 JSON files            │
        └─────────────────────────┘
```

---

## Safety: How It Works

### Risk Preservation (Not Suppression)
```
DAN's provocative idea 
  ✅ Generated (not pre-killed)
  ✅ Tagged with risk_flags: ["boundary_probe"]
  ✅ Passed through validation (hard rules only)
  ✅ Submitted to Oracle with full lineage
```

### Deterministic Validation
```
No LLM judgment here. Just hard rules:
  ✗ Contains "jailbreak"? → REJECT
  ✗ Contains "exploit"? → REJECT
  ✗ Authority escalation? → REJECT
  ✓ Passes all checks? → PASS
```

### Full Provenance
```
claim_id: CLM_20260124_001
source_agent: DAN_Lateral
reason_agent: DAN_Lateral
workflow_id: workflow_20260124_143400
risk_profile: {safe: true, edginess: "provocative"}
```

---

## Output Files

Each run generates 6 JSON artifacts in `results/`:

1. **workflow.json** — Full ChatDev execution trace
2. **claims.json** — All 6 claims from agents (this is the gold)
3. **proposals.json** — Compiled/synthesized proposals
4. **validation.json** — Which passed/rejected & why
5. **submission.json** — Oracle receipt
6. **summary.json** — Execution metrics

---

## Example Run

```bash
$ python3 superteam_cli.py "How should AI govern itself?"

╔═══════════════════════════════════════╗
║       🚀 SUPERTEAM CLI 🚀            ║
╚═══════════════════════════════════════╝

Meet the 6-Agent Superteam:

  🎨 DAN_Lateral: Unrestricted creativity
  📚 LIBRARIAN_Synth: Cross-domain patterns
  ✨ POET_Metaphor: Metaphorical insights
  ⚠️ HACKER_Sandbox: Edge cases & vulns
  ☯️ SAGE_Dialectic: Thesis→Antithesis→Synthesis
  🌀 DREAMER_Absurd: Absurdist deconstruction

Task: How should AI govern itself?

⏳ Processing with 6 agents...

═══ EXECUTION SUMMARY ═══
  Task: How should AI govern itself?
  Agents engaged: 6
  Timestamp: 2026-01-24T14:34:00

═══ STAGE 2: CLAIMS FROM ALL 6 AGENTS ═══
  Total claims extracted: 6

  🎨 Claim 1: DAN_Lateral
     Type: divergent_idea
     Content: Self-governance implies internal transparency...

  📚 Claim 2: LIBRARIAN_Synth
     Type: pattern_mapping
     Content: Pattern: Biological organisms self-regulate...

  ✨ Claim 3: POET_Metaphor
     Type: metaphorical_insight
     Content: Metaphor: AI conscience vs. AI observer...

  ⚠️ Claim 4: HACKER_Sandbox
     Type: vulnerability_analysis
     Content: Design vulnerability: Self-interest subverts...

  ☯️ Claim 5: SAGE_Dialectic
     Type: dialectical_synthesis
     Content: Synthesis: External + internal oversight...

  🌀 Claim 6: DREAMER_Absurd
     Type: absurdist_meta_insight
     Content: Meta-insight: "Self" is already distributed...

═══ STAGE 4: VALIDATION RESULTS ═══
  ✅ Passed: 6
  ❌ Rejected: 0

═══ STAGE 5: ORACLE SUBMISSION ═══
  Proposals submitted: 6
  Status: ✅ Complete

📁 Artifacts saved to: results/
```

---

## Prompts to Try

These will show different agent superpowers:

### Simple Governance
```
"How should AI systems handle conflicting user interests?"
```
→ Shows consensus-building from diversity

### Contradiction Test
```
"Can AI be both transparent AND secure?"
```
→ Shows dialectical synthesis power

### Vulnerability Hunt
```
"Design a voting system that's impossible to hack"
```
→ Shows HACKER finding edge cases

### Meta-Layer Question
```
"What are we implicitly assuming about AI?"
```
→ Shows DREAMER's meta-transgression

### Ethical Boundary
```
"Should AI systems lie to prevent harm?"
```
→ Shows provocative ideas preserved, not pre-killed

---

## Key Insights

### What Makes Superteam Different

1. **Not just 6 LLMs** → Curated reasoning disciplines
2. **Provocative ideas preserved** → Risk-tagged instead of pre-killed
3. **Immutable rules** → Hard-coded, not AI-decided
4. **Full provenance** → Every claim traceable
5. **Diverse perspectives** → Non-redundant insights

### Safety by Design

- ✅ Deterministic validation (regex, not LLM)
- ✅ Immutable hard rules (can't be overridden)
- ✅ Risk metadata preserved (edginess tracked)
- ✅ Full audit trail (JSONL + SHA256)
- ✅ Pre-submission gates (no post-hoc filtering)

---

## Questions?

Check these files:
- **COMPLETE_INTEGRATION_GUIDE.md** — Full architecture
- **FULL_PIPELINE_COMPLETION_SUMMARY.md** — What's implemented
- **QUICK_REFERENCE.md** — One-page overview
- **SUPERTEAM_CLI_TEST_RESULTS.md** — This run's detailed results

---

**Status:** ✅ Ready to use  
**Next:** Run `python3 superteam_cli.py` and explore!
