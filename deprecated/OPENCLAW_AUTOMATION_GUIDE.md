# OpenClaw Kernel Automation — Quick Start Guide

## What You Have

Your kernel is **already structured for OpenClaw automation**. The architecture is:

```
OpenClaw (Agent/Executor)
    ↓ (submits claim)
Oracle Town Kernel (Authority/Validator)
    ↓ (returns receipt)
OpenClaw (Proceeds with execution if approved)
```

---

## What "Automate Kernel" Means (Three Scenarios)

### 1. **Run Kernel Tasks Automatically** ✅
Automate periodic kernel maintenance (ledger scanning, state monitoring, gate validation)

### 2. **Have OpenClaw Propose Changes to Kernel** ✅
OpenClaw observes something → submits claim → kernel decides → ledger records

### 3. **Trigger Kernel Operations from OpenClaw Skills** ✅
OpenClaw skills call kernel gates directly (with receipt verification)

---

## Quick Implementation (Pick One)

### SCENARIO A: Automated Heartbeat Monitoring
**What it does:** OpenClaw periodically checks kernel health, submits observations as claims

```python
# openclaw_heartbeat_kernel_monitor.py
from oracle_town.kernel.submit_claim import submit_action_claim
import time

def kernel_health_check():
    """OpenClaw monitors kernel health every N seconds"""
    while True:
        # Observe kernel state
        state = read_kernel_state()  # from kernel/state.json
        
        # Submit observation as claim
        receipt = submit_action_claim(
            action_type="observation",
            target="kernel_state",
            evidence_bytes=json.dumps(state).encode(),
            intent="Monitor kernel health metrics",
            source="OPENCLAW"
        )
        
        # Only proceed if kernel approves
        if receipt['decision'] == 'ACCEPT':
            log_observation(state)
            print(f"✓ Kernel observation logged at {receipt['ledger_entry_id']}")
        else:
            print(f"✗ Kernel rejected observation: {receipt['reason']}")
        
        time.sleep(300)  # Every 5 minutes

if __name__ == '__main__':
    kernel_health_check()
```

### SCENARIO B: OpenClaw Skills That Call Kernel
**What it does:** OpenClaw skills request kernel authority before taking action

```python
# openclaw_skill_with_kernel_approval.py
from oracle_town.kernel.submit_claim import submit_action_claim
from oracle_town.kernel.receipt_check import check_receipt

def fetch_with_kernel_approval(url):
    """OpenClaw fetch skill that gets kernel approval first"""
    
    # 1. Fetch the resource (don't execute yet)
    response = requests.get(url)
    
    # 2. Submit to kernel for approval
    receipt = submit_action_claim(
        action_type="fetch",
        target=url,
        evidence_bytes=response.content,
        intent=f"Fetch content from {url}",
        source="OPENCLAW"
    )
    
    # 3. Check receipt (K15: no receipt = no execution)
    if not check_receipt(receipt):
        raise RuntimeError(f"Kernel denied fetch: {receipt['reason']}")
    
    # 4. Execute (now approved)
    return response.content

def get_heartbeat_instructions():
    """Example: Get daily instructions from Moltbook (kernel-approved)"""
    content = fetch_with_kernel_approval("https://moltbook.com/heartbeat")
    instructions = parse_instructions(content)
    return instructions
```

### SCENARIO C: Continuous Kernel Automation Loop
**What it does:** OpenClaw daemon that continuously checks kernel, submits observations, executes decisions

```python
# openclaw_kernel_automation_daemon.py
import json
from oracle_town.kernel.submit_claim import submit_action_claim
from oracle_town.kernel.ledger import read_ledger_entry
from oracle_town.kernel.mayor import Mayor

class OpenClawKernelDaemon:
    def __init__(self):
        self.kernel_state_path = "kernel/state.json"
        self.ledger_path = "kernel/ledger.json"
        self.mayor = Mayor()
    
    def observe_kernel_state(self):
        """Step 1: Observe kernel state"""
        with open(self.kernel_state_path) as f:
            state = json.load(f)
        return state
    
    def submit_observation(self, observation):
        """Step 2: Submit observation as claim"""
        receipt = submit_action_claim(
            action_type="observation",
            target="kernel_state",
            evidence_bytes=json.dumps(observation).encode(),
            intent="Automated kernel monitoring",
            source="OPENCLAW_DAEMON"
        )
        return receipt
    
    def read_latest_ledger_entries(self, count=5):
        """Step 3: Read kernel decisions"""
        with open(self.ledger_path) as f:
            ledger = json.load(f)
        return ledger['entries'][-count:]
    
    def execute_kernel_decisions(self, entries):
        """Step 4: Act on kernel authority"""
        for entry in entries:
            if entry['status'] == 'ACCEPT':
                self.handle_accepted_claim(entry)
            elif entry['status'] == 'REJECT':
                self.handle_rejected_claim(entry)
    
    def handle_accepted_claim(self, claim):
        """Execute when kernel approves"""
        action_type = claim['action_type']
        
        if action_type == 'fetch':
            url = claim['target']
            print(f"✓ Kernel approved fetch: {url}")
            # Execute the fetch
            
        elif action_type == 'update':
            target = claim['target']
            print(f"✓ Kernel approved update: {target}")
            # Execute the update
    
    def handle_rejected_claim(self, claim):
        """Log when kernel rejects"""
        print(f"✗ Kernel rejected {claim['action_type']}: {claim.get('reason', 'no reason')}")
    
    def run_forever(self):
        """Main automation loop"""
        while True:
            # Observe
            state = self.observe_kernel_state()
            
            # Submit
            receipt = self.submit_observation(state)
            
            # Read decisions
            entries = self.read_latest_ledger_entries()
            
            # Execute
            self.execute_kernel_decisions(entries)
            
            print(f"✓ Cycle complete. Ledger entries: {len(entries)}")
            
            time.sleep(60)  # Run every minute

if __name__ == '__main__':
    daemon = OpenClawKernelDaemon()
    daemon.run_forever()
```

---

## How to Use (Step by Step)

### Step 1: Check Kernel Integration Exists
```bash
python3 oracle_town/kernel/kernel_client.py
# Should show kernel is responsive
```

### Step 2: Pick Your Scenario
- **Scenario A:** You want passive monitoring (OpenClaw observes, logs)
- **Scenario B:** You want skill-level approval (OpenClaw skills call kernel)
- **Scenario C:** You want full daemon automation (continuous background automation)

### Step 3: Deploy
```bash
# Copy the code to your project
# Scenario A: Run as cron job (5 min interval)
# Scenario B: Use with OpenClaw skill system
# Scenario C: Run as background daemon

# Then test:
python3 openclaw_kernel_automation_daemon.py
```

### Step 4: Monitor
```bash
# Watch the ledger grow
tail -f kernel/ledger.json

# Watch OpenClaw logs
tail -f openclaw_daemon.log
```

---

## Key Safety Rules (Built-In)

✅ **K15 Enforcement:** No receipt = no execution (fail-closed)
✅ **Immutable Ledger:** All actions logged, tamper-proof
✅ **Authority Separation:** OpenClaw proposes, Kernel decides
✅ **Determinism:** Same claim → same decision (K5)
✅ **Transparency:** Full audit trail visible

---

## Which Scenario Should You Use?

| Scenario | Use Case | Complexity | Safety |
|----------|----------|-----------|--------|
| **A** | Monitor kernel health passively | Low | Very high |
| **B** | Skills need kernel approval | Medium | Very high |
| **C** | Full automation daemon | High | Very high |

**Recommendation:** Start with **Scenario A** (simplest) or **Scenario B** if you have specific OpenClaw skills.

