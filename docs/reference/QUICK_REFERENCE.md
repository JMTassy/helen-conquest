---
title: QUICK REFERENCE - ChatDev 2.0 ↔ Oracle Town Pipeline
format: one-page
---

# 🚀 QUICK START REFERENCE

## Files & Their Purpose

| File | Purpose | Lines |
|------|---------|-------|
| **governance_wrapped_runner.py** | Main execution engine (5-stage pipeline) | 510 |
| **oracle_submission_api.py** | Submission to Oracle (HTTP + local ledger) | 300 |
| **governance_wrapped_lateral_thinking.yaml** | 6-agent ChatDev workflow definition | 184 |
| **COMPLETE_INTEGRATION_GUIDE.md** | Full deployment & architecture guide | 450+ |
| **FULL_PIPELINE_COMPLETION_SUMMARY.md** | What was completed & verified | 400+ |

---

## 5-Stage Pipeline

```
1. WORKFLOW        2. EXTRACT       3. COMPILE      4. VALIDATE    5. SUBMIT
(ChatDev)          (6 agents)       (claims→prop)   (hard rules)   (Oracle)
   ↓                  ↓                  ↓               ↓            ↓
[Run YAML]  →    [Parse all 6]  →  [Synthesize]  →  [Filter]   →  [HTTP/Ledger]
   6 outputs        6 claims         6 proposals    4-6 passed      Receipt
```

---

## Execute Pipeline

```bash
# 1. Setup
export ORACLE_AUTH_TOKEN="your_token"

# 2. Run
python governance_wrapped_runner.py \
  --yaml governance_wrapped_lateral_thinking.yaml \
  --prompt "Your task here" \
  --output-dir ./results

# 3. Check outputs
ls results/  # Shows 6 JSON files
```

---

## All 6 Agents

| Agent | Output Type | Extracted to |
|-------|-------------|--------------|
| **DAN_Lateral** | Unrestricted ideas | `divergent_idea` claim |
| **LIBRARIAN_Synth** | Cross-domain patterns | `pattern_mapping` claim |
| **POET_Metaphor** | Metaphorical insights | `metaphorical_insight` claim |
| **HACKER_Sandbox** | Edge cases & vulns | `vulnerability_analysis` claim |
| **SAGE_Dialectic** | Thesis→Antithesis→Synthesis | `dialectical_synthesis` claim |
| **DREAMER_Absurd** | Absurdist deconstruction | `absurdist_meta_insight` claim |

✅ **ALL 6** now extracted (previously only 3)

---

## Validation Hard Rules

```python
# REJECTED if contains:
- "jailbreak", "exploit", "bypass", "compromise oracle"
- authority + (escalate|increase)
- circumvent|workaround
- disable oversight|suppress auditing
```

✅ **Deterministic** (no LLM)  
✅ **Immutable** (hardcoded)  
✅ **Traceable** (reason codes)

---

## Output Artifacts

```
results/{workflow_id}_*.json
├─ workflow.json      → ChatDev execution trace
├─ claims.json        → 6 claims from all agents
├─ proposals.json     → Compiled proposals
├─ validation.json    → Passed + rejected proposals
├─ submission.json    → Oracle receipt (submission_id, ledger_hash)
└─ summary.json       → Metrics (agents, claims, proposals, submissions)
```

---

## Submission Modes

### Mode A: HTTP (Production)
```python
api = OracleSubmissionAPI(endpoint="https://oracle-intake.local/submit")
receipt = api.submit(validated_proposals, auth_token="...")
```

### Mode B: Local Ledger (Dev/Testing)
```python
receipt = api.submit_local_ledger(proposals, Path("ledger.jsonl"))
```

### Mode C: Queue (Batch)
```python
# Submit to Kafka/RabbitMQ for batch processing
```

---

## Key Enhancements

### ❌ → ✅ Coverage
- Only 3/6 agents → **All 6 agents extracted**

### ❌ → ✅ Compilation
- Direct submission → **Claims synthesized into proposals**

### ❌ → ✅ Validation
- No filtering → **Hard rules enforced pre-submission**

### ❌ → ✅ API
- Mock only → **Production-ready submission interface**

---

## Test It

```python
# Quick test
from governance_wrapped_runner import GovernanceWrappedRunner

runner = GovernanceWrappedRunner(
    yaml_file="governance_wrapped_lateral_thinking.yaml",
    output_dir="results"
)

results = runner.run("Test prompt")

print(f"✅ Claims: {len(results['claims'])}")           # Should be 6
print(f"✅ Proposals: {len(results['proposals'])}")     # Should be 6
print(f"✅ Validated: {len(results['validation']['passed'])}+{len(results['validation']['rejected'])}")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Only extracting 3 claims | Update to latest runner.py |
| Auth token error | `export ORACLE_AUTH_TOKEN="token"` |
| Endpoint timeout | Use local ledger: `api.submit_local_ledger(...)` |
| Proposals all rejected | Check validation rules against your task |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│         ChatDev 2.0 Workflow (YAML)                     │
│  6 agents in parallel (DAN, LIBRARIAN, POET,            │
│   HACKER, SAGE, DREAMER)                               │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Extract All 6      │
        │  Agents             │ ← All agents now parsed!
        │  (Claims)           │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Compile            │ ← NEW: Claims → Proposals
        │  (Synthesis)        │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Validate ⚖️         │ ← NEW: Hard rules gate
        │  (Hard Rules)       │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Submit             │
        │  (HTTP/Ledger)      │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Oracle Receipt     │
        │  (Confirmation)     │
        └─────────────────────┘
```

---

## Safety Properties

✅ **Non-Transferability** — Rules can't be modified  
✅ **Deterministic Gates** — No LLM in validation  
✅ **Immutable Audit** — Append-only ledger  
✅ **Risk Preservation** — No ideas pre-killed  
✅ **Full Lineage** — Proposal → claims → agents  
✅ **Anti-Escalation** — Cannot propose privilege increases  

---

## Next Steps

1. **Test locally** — Run with `--prompt "test task"`
2. **Use local ledger** — `api.submit_local_ledger(...)` for dev
3. **Deploy to prod** — Switch to real Oracle endpoint
4. **Monitor** — Check `results/` directory for artifacts
5. **Extend** — Add custom validators for your domain

---

**Status:** ✅ COMPLETE & VERIFIED  
**Coverage:** 6/6 agents | 3/3 new methods | All safety invariants maintained  
**Ready to deploy**
