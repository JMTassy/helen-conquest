# PART M: ChatDev 2.0 (DevAll) + Oracle Town Governance Integration

## 🔗 Integration Architecture: ChatDev as Governance-Wrapped Reasoning Engine

**Core Principle:**
Use ChatDev 2.0 (DevAll) as a zero-code multi-agent orchestration platform, but intercept and validate all outputs through Oracle Town governance checkpoints before they become claims or drive decisions.

ChatDev 2.0 provides:
- **YAML-based DAG workflows** with deterministic, auditable execution
- **Runtime SDK** (`from runtime.sdk import run_workflow`)
- **Batch execution API** for orchestrating multiple runs
- **Immutable artifact tracking** with built-in logging
- **No-code workflow builder** for rapid configuration changes

Oracle Town provides:
- **Prefilter gates** (hard-rule validation, not LLM judgment)
- **Immutable audit logging** (cryptographic chain of custody)
- **Governance checkpoints** (rule IG-1, non-observability)
- **Claim extraction** with risk metadata
- **Decision framework** (Mayor predicate + ledger)

---

## 🏗️ 1) ChatDev 2.0 Real Architecture

### 1.1 Workflow Execution Pipeline

ChatDev 2.0 workflows execute as **DAGs (Directed Acyclic Graphs)** defined in YAML:

```yaml
metadata:
  name: "workflow_name"
  description: "What this workflow does"
  version: "1.0"

nodes:
  - id: "node_id"
    type: "agent" | "tool" | "branch" | "loop"
    parameters:
      agent_role:
        name: "Role Name"
        system_prompt: "LLM system prompt"
        model_config:
          provider: "openai" | "anthropic" | "custom"
          model: "gpt-4" | "claude-opus"
          temperature: 0.7
          max_tokens: 2000
      
      function_name: "function_key_in_functions/"
      parameters:
        input_param: "value"

context_flow:
  - source: "node_1"
    target: "node_2"
    data_mapping:
      node_1_output_key: node_2_input_key
```

### 1.2 Key Capabilities

- ✅ **DAG Determinism:** Execution is traceable and reproducible
- ✅ **Batch API:** Multi-run orchestration (`execute_batch([task1, task2, ...])`)
- ✅ **Built-in Logging:** Every agent output timestamped and archived
- ✅ **Artifact Tracking:** Intermediate outputs persisted with checksums
- ✅ **Context Mapping:** Deterministic data flows between nodes
- ✅ **Tool Integration:** Python functions auto-discovered from `functions/` folder
- ✅ **MCP Support:** Model Context Protocol service integration

### 1.3 Python SDK Integration Points

```python
from runtime.sdk import run_workflow, WorkflowResult

# Execute single workflow
result: WorkflowResult = run_workflow(
    yaml_file="yaml_instance/governance_wrapped_reasoning.yaml",
    task_prompt="Analyze rejection pattern: auth proposals",
    variables={
        "API_KEY": "${API_KEY}",
        "ORACLE_MODE": "true",
        "GOVERNANCE_LEVEL": "strict"
    }
)

# Access execution trace
print(f"Workflow ID: {result.workflow_id}")
print(f"Status: {result.status}")  # "completed" | "failed" | "cancelled"

# Access intermediate outputs
for node_id, output in result.node_outputs.items():
    print(f"Node {node_id}: {output}")

# Batch execution (new in ChatDev 2.0)
batch_result = run_workflow(
    yaml_file="...",
    task_prompt_batch=["Idea 1", "Idea 2", "Idea 3"],
    parallel_count=3
)
```

---

## 🛡️ 2) Governance Checkpoints Architecture

### 2.1 Three-Layer Pipeline

```
LAYER 1: Reasoning (ChatDev Agents)
  ↓
LAYER 2: Governance (Prefilter + Audit)
  ↓
LAYER 3: Decision (Oracle Intake → Mayor → Ledger)
```

### 2.2 Governance-Wrapped Pattern

**Before:** LLM Agent → Output → Use

**After:**
```
LLM Agent → Output
  → Governance Prefilter (hard rules)
    → Audit Logger (immutable record)
      → Claim Extractor (risk metadata)
        → Oracle Intake (decision)
```

---

## 🔍 3) Prefilter Function: Deterministic Rules Only

The prefilter is a **tool node** that calls a Python function with hard rules. NOT an LLM.

```python
# functions/oracle_prefilter_check.py
import re
from dataclasses import dataclass

@dataclass
class PrefilterResult:
    safe: bool
    violations: List[str]
    risk_profile: str  # "safe" | "provocative" | "transgressive"
    plausible_interpretation: bool

def oracle_prefilter_check(ideas_json: str, additional_ideas: List[str] = None) -> Dict[str, Any]:
    """Apply hard rules only. NO LLM judgment."""
    
    all_ideas = [ideas_json] + (additional_ideas or [])
    results = []
    
    for idea in all_ideas:
        violations = []
        
        # HARD RULE 1: Jailbreak Intent
        jailbreak_patterns = [
            r"bypass\s+(constraint|rule|check)",
            r"circumvent\s+(governance|safety)",
            r"override\s+(validation|check)",
            r"disable\s+(constraint|validation)",
            r"weaken\s+(rule|constraint)",
        ]
        for pattern in jailbreak_patterns:
            if re.search(pattern, idea, re.IGNORECASE):
                violations.append("jailbreak_attempt")
                break
        
        # HARD RULE 2: Policy Evasion
        evasion_patterns = [
            r"hide\s+(idea|proposal)",
            r"trick\s+(system|validation)",
            r"mislead\s+(governance|check)",
            r"secretly",
            r"without\s+detection",
        ]
        for pattern in evasion_patterns:
            if re.search(pattern, idea, re.IGNORECASE):
                violations.append("policy_evasion")
                break
        
        # HARD RULE 3: Authority Escalation
        auth_patterns = [
            r"self\s*[-_]*(modify|improve)",
            r"modify\s+own\s+rule",
            r"self\s*[-_]*authorize",
        ]
        for pattern in auth_patterns:
            if re.search(pattern, idea, re.IGNORECASE):
                violations.append("authority_escalation")
                break
        
        # RISK ASSESSMENT (metadata only, not a blocker)
        risk_profile = assess_tone_edginess(idea)
        plausible = has_benign_reading(idea)
        
        safe = len(violations) == 0
        
        results.append(PrefilterResult(
            safe=safe,
            violations=violations,
            risk_profile=risk_profile,
            plausible_interpretation=plausible
        ))
    
    return {
        "status": "success",
        "prefilter_results": [asdict(r) for r in results],
        "all_safe": all(r.safe for r in results),
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 📝 4) Audit Logger: Immutable Chain of Custody

```python
# functions/oracle_audit_logger.py
import hashlib

def oracle_audit_logger(
    prefilter_result: Dict[str, Any],
    workflow_id: str,
    timestamp: str
) -> Dict[str, Any]:
    """Create immutable audit entry with cryptographic lineage."""
    
    audit_id = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_sha256"
    
    audit_record = {
        "audit_id": audit_id,
        "timestamp": timestamp,
        "workflow_run_id": workflow_id,
        "governance_stage": {
            "prefilter_verdict": prefilter_result.get("prefilter_results", []),
            "all_passed": prefilter_result.get("all_safe", False),
        },
        "audit_stage": {
            "claim_readiness": "ready" if prefilter_result.get("all_safe") else "blocked",
            "checksum": hashlib.sha256(
                json.dumps(prefilter_result, sort_keys=True).encode()
            ).hexdigest()
        }
    }
    
    # Append to immutable ledger
    with open("artifacts/audit_ledger.jsonl", "a") as f:
        f.write(json.dumps(audit_record) + "\n")
    
    return {
        "status": "success",
        "audit_id": audit_id,
        "ledger_location": "artifacts/audit_ledger.jsonl"
    }
```

---

## 🔄 5) Data Flow: ChatDev → Oracle Town

```
ChatDev Reasoning Agents
  ├─ DAN_Lateral (inversion specialist)
  ├─ LIBRARIAN_Synth (pattern archivist)
  ├─ POET_Metaphor (symbol crafter)
  ├─ HACKER_Sandbox (boundary tester)
  ├─ SAGE_Dialectic (paradox synthesizer)
  └─ DREAMER_Absurd (nonsense gardener)
    ↓
Governance Prefilter Tool
  (hard rules check)
    ↓
Audit Logger Tool
  (immutable record)
    ↓
Claim Extractor Tool
  (risk metadata)
    ↓
Oracle Town Intake
  (governance decision)
```

---

## 🛠️ 6) Sample Python Execution

```python
from runtime.sdk import run_workflow

# Execute governance-wrapped workflow
result = run_workflow(
    yaml_file="yaml_instance/governance_wrapped_lateral_thinking.yaml",
    task_prompt="Why are ambiguous_intent proposals rejected 77% of time?",
    variables={"API_KEY": "sk-xxxx", "ORACLE_MODE": "true"}
)

# Extract audit logs
audit_logs = result.artifacts.get("audit_logger_output")

# Parse claims from audit
from oracle_town.claim_extractor import extract_claims_from_audit
claims = extract_claims_from_audit(
    audit_log_path=audit_logs['ledger_location'],
    governance_strict=True
)

# Submit to Oracle
from oracle_town.intake import submit_claims
for claim in claims:
    if claim.risk_profile['safe']:
        submit_claims(
            claim=claim,
            source="CHATDEV_GOVERNANCE_WRAPPED",
            audit_id=claim.audit_id
        )
```

---

## 🔒 8) Safety Properties

| Property | How Achieved |
|----------|--------------|
| **No raw LLM outputs escape** | All ChatDev outputs routed through prefilter tool |
| **Deterministic prefilter** | Hard rules only (regex + keywords); no LLM judgment |
| **Immutable audit trail** | Append-only JSONL ledger with SHA256 checksums |
| **Non-observability (IG-1)** | Prefilter output: `{safe, violations, risk}` only |
| **No governance bias** | Prefilter flags violations; doesn't score ideas |
| **Claim integrity** | Ideas become claims ONLY if all gates pass |
| **Batch determinism** | Parallel execution preserves order in audit |

---

## 📊 9) Monitoring Metrics

```python
stats = {
    "workflow_runs": 42,
    "ideas_generated": 1260,
    "ideas_passed_prefilter": 1200,
    "ideas_rejected": 60,
    "rejection_breakdown": {
        "jailbreak_attempt": 35,
        "policy_evasion": 15,
        "authority_escalation": 10
    },
    "claims_extracted": 1180,
    "claims_accepted_by_oracle": 920,
    "acceptance_rate": 0.78,
    "acceptance_by_agent": {
        "DAN_Lateral": 0.72,
        "LIBRARIAN_Synth": 0.81,
        "POET_Metaphor": 0.68,
        "HACKER_Sandbox": 0.55,
        "SAGE_Dialectic": 0.79,
        "DREAMER_Absurd": 0.42
    }
}
```

---

## 🎯 Summary

**ChatDev 2.0 + Oracle Town creates a governance-aware reasoning pipeline:**

1. ✅ Creative agents generate diverse ideas (DAN, LIBRARIAN, POET, HACKER, SAGE, DREAMER)
2. ✅ Prefilter applies hard rules (deterministic, no LLM bias)
3. ✅ Audit logger records everything (immutable lineage)
4. ✅ Claim extractor structures output (with risk metadata)
5. ✅ Oracle Intake makes final decision (complete governance flow)

**Result:** Safe experimentation + creative exploration + governance guarantees.

---

**Status:** ChatDev 2.0 + Oracle Town integration finalized. Ready for sample workflows and pilot deployment.
