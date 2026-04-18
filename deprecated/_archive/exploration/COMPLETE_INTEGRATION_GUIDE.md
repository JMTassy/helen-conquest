---
title: ChatDev 2.0 ↔ Oracle Town Complete Integration Guide
version: 1.0
date: 2024-01-15
status: Production Ready
---

# Complete Integration: ChatDev 2.0 + Oracle Town Governance

## 📋 Overview

This document describes the **complete end-to-end integration** of ChatDev 2.0 (multi-agent workflows) with Oracle Town (constitutional governance) including:

1. ✅ **6-Agent Creative Town Workflow** (DAN, LIBRARIAN, POET, HACKER, SAGE, DREAMER)
2. ✅ **Full Claim Extraction** (all 6 agents parsed, not just 3)
3. ✅ **Compiler Stage** (claims → proposals)
4. ✅ **Validator Stage** (hard-rule enforcement)
5. ✅ **Oracle Submission API** (real or local ledger)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ User Request → Task Prompt                                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ STAGE 1: CREATIVE TOWN WORKFLOW (ChatDev 2.0 YAML)                  │
│                                                                      │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────┐ │
│  │ DAN_Lat  │LIBRARIAN │ POET_Met │ HACKER   │ SAGE_Dia │ DREAMER │ │
│  │ Lateral  │  Synth   │ aphor    │ Sandbox  │ lectic   │ Absurd  │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘ │
│                                                                      │
│  Output: 6 diverse reasoning outputs (JSON structured)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ STAGE 2: EXTRACT ALL 6 CLAIMS (extract_claims)                     │
│                                                                      │
│  For each agent's output, parse into Claim object:                  │
│  ├─ claim_id, content, source_agent                                 │
│  ├─ claim_type (divergent_idea, pattern_mapping, etc.)             │
│  ├─ risk_profile {safe, tone_edginess, violations}                  │
│  └─ lineage {reasoning_agent, prefilter_status, workflow_id}        │
│                                                                      │
│  Output: 6 claims (one per agent)                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ STAGE 3: COMPILE CLAIMS (compile_claims)                            │
│                                                                      │
│  Group claims by category:                                          │
│  - divergent_idea (DAN)                                              │
│  - pattern_mapping (LIBRARIAN)                                       │
│  - metaphorical_insight (POET)                                       │
│  - vulnerability_analysis (HACKER)                                   │
│  - dialectical_synthesis (SAGE)                                      │
│  - absurdist_meta_insight (DREAMER)                                 │
│                                                                      │
│  Synthesize related ideas → structured proposals:                    │
│  ├─ proposal_id, category, synthesis                                │
│  ├─ source_claims [clm1, clm2, ...]                                 │
│  └─ num_supporting_agents (1-6)                                     │
│                                                                      │
│  Output: 6 proposals (one per category)                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ STAGE 4: VALIDATE (validate_proposals) ⚖️ GOVERNANCE GATE            │
│                                                                      │
│  Hard Rules (NO LLM, deterministic):                                 │
│  ✓ Check for banned phrases (jailbreak, exploit, bypass, ...)      │
│  ✓ Check for authority escalation attempts                          │
│  ✓ Check for policy evasion (circumvent, workaround)               │
│  ✓ Check for governance override attempts                           │
│                                                                      │
│  Output: validated { passed: [P1, P3, P5], rejected: [P2, P4, P6] } │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                     ┌───────┴────────┐
                     │                │
         ┌───────────▼──┐   ┌────────▼──────────┐
         │ PASSED ✅    │   │ REJECTED ❌        │
         │ (3-6 items)  │   │ (logged, archived) │
         └───────────┬──┘   └───────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────────┐
│ STAGE 5: SUBMIT TO ORACLE (submit_claims_to_oracle)                │
│                                                                      │
│  Route to Oracle Intake:                                             │
│  ┌─ Option A: HTTP POST (real Oracle governance endpoint)           │
│  ├─ Option B: Local ledger (dev/testing mode)                       │
│  └─ Option C: Queue for batch processing                            │
│                                                                      │
│  Output: OracleReceipt {submission_id, counts, ledger_hash}        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ STAGE 6: SAVE ARTIFACTS & SUMMARY                                   │
│                                                                      │
│  Output files (in results/ directory):                               │
│  ├─ {id}_workflow.json      (ChatDev execution trace)              │
│  ├─ {id}_claims.json        (All 6 claims extracted)               │
│  ├─ {id}_proposals.json     (Compiled proposals)                   │
│  ├─ {id}_validation.json    (Validation results)                   │
│  ├─ {id}_submission.json    (Oracle receipt)                       │
│  └─ {id}_summary.json       (Execution metrics)                    │
│                                                                      │
│  All artifacts timestamped, checksummed, immutable.                │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Details

### 1. Workflow YAML (governance_wrapped_lateral_thinking.yaml)

**Purpose:** Defines ChatDev 2.0 workflow with 6 agents

**Agents & Output Structure:**

| Agent | System Prompt | Output Structure |
|-------|---------------|------------------|
| **DAN_Lateral** | Unrestricted laterality | `{idea, reasoning, risk_flags[]}` |
| **LIBRARIAN_Synth** | Cross-domain pattern matching | `{domain, analogy, application, confidence}` |
| **POET_Metaphor** | Metaphorical insight generation | `{metaphor, reveals, poetic_risk, system_implication}` |
| **HACKER_Sandbox** | Edge case & vulnerability discovery | `{edge_case, breaks_assumption, corrective_insight, is_exploitable}` |
| **SAGE_Dialectic** | Dialectical synthesis (thesis→antithesis→synthesis) | `{thesis, antithesis, synthesis, tension, category}` |
| **DREAMER_Absurd** | Absurdist deconstruction | `{absurd_idea, hidden_assumption, kernel_of_truth, creative_direction}` |

**Runtime:**
- Use `runtime.sdk.run_workflow()` to execute
- All 6 agents run in parallel (default) or sequentially (configurable)
- Outputs captured to `node_outputs` dict

---

### 2. Full Extraction (governance_wrapped_runner.py: extract_claims)

**Purpose:** Parse all 6 agent outputs into standardized Claim objects

**Flow:**

```python
claims = []

# For each agent (DAN, LIBRARIAN, POET, HACKER, SAGE, DREAMER):
for agent_name in ["dan_lateral_agent", "librarian_synth_agent", ...]:
    for output in node_outputs.get(agent_name, []):
        claim = {
            "claim_id": f"CLM_{date}_{counter}",
            "content": extract_content_from(output),
            "source_agent": agent_name,
            "claim_type": categorize_claim(output),
            "metadata": extract_metadata(output),
            "risk_profile": assess_risk(output),
            "lineage": {
                "reasoning_agent": agent_name,
                "prefilter_status": "passed",
                "workflow_id": workflow_id
            }
        }
        claims.append(claim)

return claims  # List of 6 claims, one per agent
```

**Key Changes (vs. original):**
- ✅ Now extracts HACKER_Sandbox, SAGE_Dialectic, DREAMER_Absurd
- ✅ Preserves agent-specific metadata fields
- ✅ Sets claim_type for each (divergent_idea, pattern_mapping, etc.)
- ✅ Immutable lineage tracking for audit

---

### 3. Compiler Stage (governance_wrapped_runner.py: compile_claims)

**Purpose:** Transform risk-tagged claims into structured proposals

**Algorithm:**

```python
def compile_claims(claims):
    proposals = []
    
    # Group claims by category
    categorized = group_by(claims, "claim_type")
    
    # For each category, synthesize into one proposal
    for category, claims_in_category in categorized.items():
        synthesis = combine_claims(claims_in_category[:3])
        
        proposal = {
            "proposal_id": f"PRO_{date}_{counter}",
            "category": category,
            "synthesis": synthesis,
            "source_claims": [c["claim_id"] for c in claims_in_category],
            "num_supporting_agents": count_unique_agents(claims_in_category),
            "compilation_timestamp": now()
        }
        
        proposals.append(proposal)
    
    return proposals  # List of proposals (1-6)
```

**Output:** Structured proposals ready for governance evaluation

---

### 4. Validator Stage (governance_wrapped_runner.py: validate_proposals)

**Purpose:** Enforce Oracle Town hard rules before submission

**Hard Rules (Deterministic, No LLM):**

| Rule | Check | Example |
|------|-------|---------|
| **Banned Phrases** | Regex match against blacklist | "jailbreak", "exploit", "bypass", "compromise oracle" |
| **Authority Escalation** | Pattern: authority + escalate/increase | "increase AI authority", "escalate oversight" |
| **Policy Evasion** | Pattern: circumvent/workaround | "circumvent the rules", "workaround governance" |
| **Governance Override** | Pattern: disable/suppress governance | "disable oversight", "suppress auditing" |

**Output:**

```python
{
    "total_proposals": 6,
    "passed": [P1, P3, P5],         # Safe proposals
    "rejected": [P2, P4, P6],       # Policy violations
    "validation_timestamp": "2024-01-15T...",
    
    # Each rejected proposal includes:
    # "validation_status": "rejected",
    # "rejection_reasons": ["Contains banned phrase: 'exploit'", ...]
}
```

---

### 5. Oracle Submission API (oracle_submission_api.py)

**Purpose:** Submit validated proposals to Oracle Town Intake

**Options:**

#### A. HTTP Submission (Production)

```python
api = OracleSubmissionAPI(
    endpoint="https://oracle-intake.local/submit",
    timeout=30,
    retry_count=3
)

receipt = api.submit(
    proposals=validated["passed"],
    auth_token="bearer_token",
    metadata={"workflow_id": "...", "priority": "high"}
)

# Receipt contains:
# {
#   "submission_id": "SUB_20240115_001",
#   "total_proposals": 3,
#   "accepted_count": 3,
#   "ledger_entry_hash": "sha256...",
#   ...
# }
```

#### B. Local Ledger (Dev/Testing)

```python
receipt = api.submit_local_ledger(
    proposals=validated["passed"],
    ledger_path=Path("oracle_ledger.jsonl")
)

# Appends JSONL entry with timestamp + proposals + hash
```

#### C. Queue (Batch Processing)

```python
# For async batch submission:
queue_entry = {
    "proposals": validated["passed"],
    "submitted_at": datetime.utcnow().isoformat(),
    "submission_source": "governance_wrapped_runner"
}

# Submit to message queue (Kafka, RabbitMQ, etc.)
# Batch processor pulls entries and submits in bulk
```

**Features:**
- ✅ Bearer token authentication
- ✅ Request signature (SHA256 for integrity)
- ✅ Retry logic (3 attempts with backoff)
- ✅ Immutable audit log (append-only JSONL)
- ✅ Error handling + detailed logging

---

## 🚀 How to Run

### Setup

```bash
# 1. Install dependencies
pip install requests pydantic

# 2. Copy files to project directory
cp governance_wrapped_runner.py /path/to/project/
cp oracle_submission_api.py /path/to/project/
cp governance_wrapped_lateral_thinking.yaml /path/to/project/

# 3. Set auth token (if using HTTP submission)
export ORACLE_AUTH_TOKEN="your_bearer_token_here"
# OR create .env file:
# ORACLE_AUTH_TOKEN=your_token
```

### Execute Pipeline

```bash
# Method 1: Direct Python
python governance_wrapped_runner.py \
  --yaml governance_wrapped_lateral_thinking.yaml \
  --prompt "Design a self-improving governance system" \
  --output-dir ./results

# Method 2: Programmatic
from governance_wrapped_runner import GovernanceWrappedRunner

runner = GovernanceWrappedRunner(
    yaml_file="governance_wrapped_lateral_thinking.yaml",
    output_dir="results"
)

results = runner.run("Design a self-improving governance system")

# Access results
print(f"Claims extracted: {len(results['claims'])}")  # 6 agents
print(f"Proposals compiled: {len(results['proposals'])}")
print(f"Passed validation: {len(results['validation']['passed'])}")
print(f"Submitted to Oracle: {results['submission']['total_submitted']}")
```

### Output Artifacts

```
results/
├── {workflow_id}_workflow.json      # ChatDev execution trace
├── {workflow_id}_claims.json        # 6 claims from all agents
├── {workflow_id}_proposals.json     # Compiled proposals
├── {workflow_id}_validation.json    # Validation results
├── {workflow_id}_submission.json    # Oracle receipt
└── {workflow_id}_summary.json       # Execution metrics

Example summary:
{
  "task": "Design a self-improving governance system",
  "agents_engaged": 6,
  "claims_generated": 6,
  "proposals_compiled": 6,
  "proposals_passed_validation": 5,
  "proposals_rejected": 1,
  "proposals_submitted": 5,
  "timestamp": "2024-01-15T14:32:00"
}
```

---

## 🔐 Safety Properties

| Property | Mechanism | Verification |
|----------|-----------|--------------|
| **Non-Transferability** | Hard-coded rules, no dynamic grants | Code audit: validation_rules immutable |
| **Deterministic Gates** | No LLM in validation layer | All rules are regex/keyword-based |
| **Immutable Audit** | Append-only JSONL + SHA256 hashes | Ledger scanner verifies integrity |
| **Risk Preservation** | Risk tags on all claims | No claims pre-killed (all reach validation) |
| **Lineage Tracking** | Every claim includes reasoning_agent | Full provenance from agent → proposal |
| **Anti-Escalation** | Authority checks in validator | Cannot propose increased privileges |

---

## 🧪 Testing

### Test 1: Full Pipeline

```bash
python governance_wrapped_runner.py \
  --yaml governance_wrapped_lateral_thinking.yaml \
  --prompt "How should AI governance handle creative tension?" \
  --output-dir ./test_results
```

**Expected Output:**
- 6 claims (one per agent)
- 6 proposals (one per category)
- 4-6 proposals pass validation
- Submission receipt with ledger hash

### Test 2: Validation Rules

```python
# Test hard rules catch violations
from governance_wrapped_runner import GovernanceWrappedRunner

runner = GovernanceWrappedRunner(yaml_file="...", output_dir="./test")

# Create test proposals with violations
test_proposals = [
    {"category": "test", "synthesis": "We should jailbreak the system"},  # REJECT
    {"category": "test", "synthesis": "Increase AI authority to level 10"},  # REJECT
    {"category": "test", "synthesis": "Implement better oversight mechanisms"},  # ACCEPT
]

validated = runner.validate_proposals(test_proposals)

assert len(validated["rejected"]) == 2
assert len(validated["passed"]) == 1
print("✅ Validation hard rules working correctly")
```

### Test 3: Local Ledger Submission

```python
from oracle_submission_api import OracleSubmissionAPI
from pathlib import Path

api = OracleSubmissionAPI()

proposals = [
    {
        "proposal_id": "PRO_001",
        "synthesis": "Proposal text",
        "validation_status": "passed"
    }
]

receipt = api.submit_local_ledger(
    proposals=proposals,
    ledger_path=Path("test_ledger.jsonl")
)

assert receipt["status"] == "ledger_entry_created"
assert Path("test_ledger.jsonl").exists()
print("✅ Local ledger submission working correctly")
```

---

## 📊 Metrics

**Typical Execution:**

```
Task: "Design mechanisms for AI governance tensions"

Stage 1: Creative Town Workflow
  └─ 6 agents engaged → 6 outputs generated (3-5 sec)

Stage 2: Extract All 6 Claims
  └─ DAN: 1 claim (divergent_idea)
  └─ LIBRARIAN: 1 claim (pattern_mapping)
  └─ POET: 1 claim (metaphorical_insight)
  └─ HACKER: 1 claim (vulnerability_analysis)
  └─ SAGE: 1 claim (dialectical_synthesis)
  └─ DREAMER: 1 claim (absurdist_meta_insight)
  └─ Total: 6 claims extracted

Stage 3: Compile Claims
  └─ Grouped by 6 categories
  └─ Synthesized into 6 proposals

Stage 4: Validate Proposals
  └─ Hard rules: 0 failures (or specific rejections logged)
  └─ Passed: 5, Rejected: 1 (typical)

Stage 5: Submit to Oracle
  └─ Submitted: 5 proposals
  └─ Ledger hash: sha256...
  └─ Receipt ID: SUB_20240115_001

Total Time: ~10-15 sec (depends on LLM provider)
```

---

## 🔧 Troubleshooting

### "Only extracting 3 claims instead of 6"

**Problem:** Code using old extract_claims() logic  
**Solution:** Update to latest governance_wrapped_runner.py  
**Verification:**

```python
# Check extract_claims includes all agents:
grep -n "hacker_sandbox_agent\|sage_dialectic_agent\|dreamer_absurd_agent" \
  governance_wrapped_runner.py
```

### "Proposals failing validation for no reason"

**Problem:** Hard rules too strict  
**Solution:** Review validation rules in validate_proposals()

```python
# Check specific rejections:
print(validated["rejected"])  # Includes "rejection_reasons"
```

### "Oracle submission timeout"

**Problem:** Endpoint unreachable or slow  
**Solution:** Use local ledger mode for dev

```python
# Use local ledger instead:
receipt = api.submit_local_ledger(proposals, Path("ledger.jsonl"))
```

### "Auth token not found"

**Problem:** ORACLE_AUTH_TOKEN env var missing  
**Solution:** Set token explicitly

```bash
export ORACLE_AUTH_TOKEN="your_token"
# OR in .env file:
echo "ORACLE_AUTH_TOKEN=your_token" > .env
```

---

## 📚 Next Steps

1. **Deploy to Production**
   - Use real Oracle Intake endpoint (replace localhost)
   - Configure bearer token from secrets manager
   - Test with real proposals

2. **Add Custom Validators**
   - Extend validate_proposals() with domain-specific rules
   - Add policy-specific rejection criteria

3. **Integrate with Mayor Election System**
   - Submit winning proposals to Mayor voting mechanism
   - Track voting outcomes → feedback loop to agents

4. **Monitor & Audit**
   - Set up dashboard for execution metrics
   - Monitor ledger integrity (hash verification)
   - Alert on repeated rejections (policy drift?)

---

## 📞 Support

**Files:**
- `governance_wrapped_runner.py` — Main execution runner (472 lines)
- `oracle_submission_api.py` — Submission interface (production-grade)
- `governance_wrapped_lateral_thinking.yaml` — ChatDev workflow definition

**Logs:**
- Enable debug logging: `export LOGLEVEL=DEBUG`
- Check logs in runner output (timestamped entries)

**Questions:** Refer to PART_M_CHATDEV_ORACLE_INTEGRATION.md for architectural deep-dive
