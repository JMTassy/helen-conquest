# 🚀 ORACLE TOWN Quickstart Guide

Get your first multi-agent governance verdict in 5 minutes.

---

## ✅ Prerequisites

- Python 3.8+ installed
- Basic familiarity with command line

---

## 📦 Step 1: Setup (30 seconds)

```bash
# Navigate to project root
cd "JMT CONSULTING - Releve 24"

# Add oracle-town to Python path (for this session)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verify setup
ls oracle-town/
```

Expected output:
```
README.md  __init__.py  agents/  cli.py  core/  districts/  schemas/
```

---

## 🧪 Step 2: Test Individual Components (2 minutes)

### Test Claim Compiler

```bash
cd oracle-town/core
python3 claim_compiler.py
```

Expected output:
```
============================================================
COMPILED CLAIM
============================================================
Claim ID: CLM_XXXXXXXX
Type: CAMPAIGN
Text: Launch a new tourism campaign...
...
```

### Test GDPR Street (4 agents)

```bash
cd ../districts/legal
python3 gdpr_street.py
```

Expected output:
```
======================================================================
GDPR STREET REPORT: GDPR Compliance Street
======================================================================
--- TURN 1: Privacy Analyst ---
...
```

### Test Full Orchestrator

```bash
cd ../../core
python3 orchestrator.py
```

Expected output:
```
======================================================================
ORACLE TOWN PROCESSING PIPELINE
======================================================================
[1/4] Compiling claim...
✓ Claim compiled: CLM_XXXXXXXX
...
```

---

## 🎯 Step 3: Use the CLI (1 minute)

### Single Claim

```bash
# From project root
python3 oracle-town/cli.py "Launch a marketing campaign collecting user emails and location data for personalized ads"
```

### Interactive Mode

```bash
python3 oracle-town/cli.py --interactive
```

Then enter:
```
📝 Enter your claim:
> Launch tourism campaign with GPS tracking and email collection

📂 Domain [marketing/product/policy/event]:
> marketing
```

---

## 📊 Step 4: Understand the Output

### Example Verdict: NO_SHIP

```
❌ FINAL VERDICT: NO_SHIP
Claim ID: CLM_ABC12345

Rationale:
1 blocking obligations must be resolved before SHIP.

Blocking Reasons:
  1. GDPR consent mechanism: Implement explicit consent for location data

======================================================================
REMEDIATION ROADMAP (1 steps)
======================================================================

[Step 1] Implement GDPR consent mechanism: Implement explicit consent for location data
  │ Effort: LOW
  │ Timeline: 1 week
  │ Responsible: Legal & Compliance District
  │ Evidence: consent_flow_diagram, legal_sign_off
  └─ Success: Legal team signs off on GDPR consent mechanism...
```

This means:
- ❌ Claim is **blocked** from execution
- 📋 **1 obligation** must be resolved
- 🛠️ **Remediation roadmap** shows how to fix it
- ⏱️ Estimated **1 week** to resolve

### Example Verdict: SHIP

```
✅ FINAL VERDICT: SHIP

Rationale:
All constitutional checks passed. QI-INT score: 0.850.
All invariants satisfied. No blocking obligations. Verdict: SHIP.

✅ APPROVED - Claim may proceed to execution
```

This means:
- ✅ Claim is **approved** for execution
- 📊 Score: **0.850** (above 0.75 threshold)
- ✓ All checks passed

---

## 🏗️ Step 5: Customize (Optional)

### Modify Agent Prompts

Edit `oracle-town/districts/legal/gdpr_street.py`:

```python
class GDPRPrivacyAnalyst(StreetAgent):
    def __init__(self):
        system_prompt = """
        You are a GDPR Privacy Analyst.

        [Customize this prompt for your use case]

        OUTPUT FORMAT:
        ## CONTRIBUTION
        ...
        """
```

### Add Your Own Street

```bash
# Create new street file
touch oracle-town/districts/legal/contract_street.py
```

```python
from oracle_town.agents import StreetAgent

class ContractReviewerAgent(StreetAgent):
    def __init__(self):
        system_prompt = """You are a Contract Reviewer..."""
        super().__init__(
            agent_id="contract_reviewer_001",
            role="Contract Reviewer",
            system_prompt=system_prompt,
        )
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'oracle_town'"

**Solution:** Set PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Or run from project root:
```bash
cd "JMT CONSULTING - Releve 24"
python3 -m oracle_town.cli "Your claim here"
```

### "Permission denied" on cli.py

**Solution:** Make it executable:
```bash
chmod +x oracle-town/cli.py
```

### Tests run but agents return mock responses

**Expected!** MVP uses mock LLM. To use real LLMs:

1. Install dependencies:
```bash
pip install openai anthropic
```

2. Set API keys:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

3. Update `oracle-town/agents/street_agent.py`:
```python
class MockLLM:
    async def complete(self, system: str, user: str) -> str:
        # Replace with real OpenAI call
        import openai
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        return response.choices[0].message.content
```

---

## 📚 Next Steps

### Learn More
- **[README.md](README.md)**: Complete system overview
- **[ORACLE_TOWN_IMPLEMENTATION.md](../ORACLE_TOWN_IMPLEMENTATION.md)**: Technical deep-dive (600+ lines)
- **[CLAUDE.md](../CLAUDE.md)**: Development guide

### Expand System
- Add more streets to Legal district
- Implement Technical & Security district
- Add Business & Operations district
- Create web UI visualization

### Production Deployment
- Integrate real LLM APIs (OpenAI, Anthropic)
- Add FastAPI server
- Implement session persistence
- Add agent memory & reflection

---

## 🎉 You're Ready!

You now have a working **hierarchical multi-agent governance system** that can:

✅ Transform natural language → structured claims
✅ Analyze through 4-agent streets (ChatDev protocol)
✅ Aggregate via buildings & districts
✅ Calculate QI-INT scores
✅ Produce binary SHIP/NO_SHIP verdicts
✅ Generate remediation roadmaps

**Start governing!** 🏛️

```bash
python3 oracle-town/cli.py --interactive
```
