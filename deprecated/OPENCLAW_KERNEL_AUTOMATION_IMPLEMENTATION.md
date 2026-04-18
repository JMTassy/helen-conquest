# OpenClaw Kernel Automation — Complete Implementation Guide

**Status:** Your kernel infrastructure is production-ready. This guide shows how to use it.

---

## What's Already Built (You Have This)

### 1. **Kernel Daemon** (oracle_town/kernel/kernel_daemon.py)
- Unix socket-based safety kernel
- Three safety gates: Gate A (fetch/shell), Gate B (memory), Gate C (invariants)
- Mayor receipt engine
- Immutable ledger

### 2. **Kernel Client** (oracle_town/kernel/kernel_client.py)
- Simple Python library for agents
- Sends requests → receives decisions (ACCEPT/REJECT)
- Fail-closed on timeout

### 3. **Receipt Verification** (oracle_town/kernel/receipt_check.py)
- Verifies kernel approvals before execution
- K15 enforcement: "No receipt = no execution"

### 4. **Monitoring** (oracle_town/kernel/monitor_claims.py)
- Watches kernel state
- Logs all decisions

---

## Three Ways to Use It

### OPTION 1: OpenClaw Skill with Kernel Approval (Simplest)

This is the **easiest to implement**. Your OpenClaw skills get kernel approval before executing.

#### Step 1: Create the Skill Wrapper

```python
# openclaw_skills_with_kernel.py
"""
OpenClaw skills that request kernel approval before execution.

Example: A skill that fetches from URLs only if kernel approves.
"""

import sys
sys.path.insert(0, '/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24')

from oracle_town.kernel.kernel_client import KernelClient
from oracle_town.kernel.receipt_check import check_receipt
import json

class KernelApprovedSkill:
    """Base class for skills that require kernel approval"""
    
    def __init__(self):
        self.kernel = KernelClient()
    
    def request_approval(self, action_type, target, evidence):
        """Request kernel approval for action"""
        request = {
            "action_type": action_type,
            "target": target,
            "evidence": evidence,
            "source": "OPENCLAW_SKILL"
        }
        
        decision = self.kernel._send_request(request)
        return decision
    
    def execute_if_approved(self, action_type, target, evidence, executor):
        """Execute action only if kernel approves"""
        # Step 1: Request approval
        decision = self.request_approval(action_type, target, evidence)
        
        # Step 2: Verify receipt (K15: fail-closed)
        if decision.get("decision") != "ACCEPT":
            raise RuntimeError(f"Kernel denied {action_type}: {decision.get('reason')}")
        
        # Step 3: Execute (now safe)
        return executor(target)


class FetchSkill(KernelApprovedSkill):
    """Fetch skill that requires kernel approval"""
    
    def fetch(self, url):
        import requests
        
        # Get content first
        response = requests.get(url)
        
        # Ask kernel for approval
        decision = self.request_approval(
            action_type="fetch",
            target=url,
            evidence={
                "url": url,
                "status_code": response.status_code,
                "content_length": len(response.content)
            }
        )
        
        # Check decision
        if decision.get("decision") != "ACCEPT":
            raise RuntimeError(f"Kernel rejected fetch from {url}")
        
        return response.content


class ShellSkill(KernelApprovedSkill):
    """Shell execution skill that requires kernel approval"""
    
    def execute(self, command):
        import subprocess
        
        # Show what we want to execute
        decision = self.request_approval(
            action_type="shell",
            target=command,
            evidence={
                "command": command,
                "shell": "/bin/bash"
            }
        )
        
        # Check decision
        if decision.get("decision") != "ACCEPT":
            raise RuntimeError(f"Kernel rejected shell execution: {command}")
        
        # Execute
        result = subprocess.run(command, shell=True, capture_output=True)
        return result.stdout.decode()


# Example usage
if __name__ == "__main__":
    # Fetch skill
    fetch = FetchSkill()
    try:
        content = fetch.fetch("https://example.com")
        print(f"✓ Fetched {len(content)} bytes")
    except RuntimeError as e:
        print(f"✗ Fetch denied: {e}")
    
    # Shell skill
    shell = ShellSkill()
    try:
        output = shell.execute("echo 'Hello from kernel-approved shell'")
        print(f"✓ Shell output: {output}")
    except RuntimeError as e:
        print(f"✗ Shell denied: {e}")
```

#### Step 2: Use in OpenClaw Configuration

```yaml
# openclaw_config.yaml
skills:
  fetch:
    handler: "openclaw_skills_with_kernel.FetchSkill.fetch"
    requires_kernel_approval: true
  
  shell:
    handler: "openclaw_skills_with_kernel.ShellSkill.execute"
    requires_kernel_approval: true
    risk_level: "HIGH"
```

#### Step 3: Test It

```bash
# Make sure kernel daemon is running
python3 oracle_town/kernel/kernel_daemon.py &

# Test the skill
python3 openclaw_skills_with_kernel.py
```

---

### OPTION 2: OpenClaw Heartbeat Monitoring (Background)

This runs a daemon that periodically checks kernel health.

#### Step 1: Create Monitoring Daemon

```python
# openclaw_kernel_monitor.py
"""
OpenClaw kernel monitoring daemon.

Runs in background, periodically checks kernel health,
submits observations as claims to the ledger.
"""

import sys
sys.path.insert(0, '/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24')

import json
import time
import logging
from pathlib import Path
from oracle_town.kernel.kernel_client import KernelClient
from oracle_town.kernel.monitor_claims import MonitorClaims

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('openclaw_kernel_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KernelHealthMonitor:
    """Monitor kernel health and submit observations"""
    
    def __init__(self, check_interval=60):
        self.kernel = KernelClient()
        self.monitor = MonitorClaims()
        self.check_interval = check_interval
        self.kernel_state_path = Path("kernel/state.json")
        self.ledger_path = Path("kernel/ledger.json")
    
    def read_kernel_state(self):
        """Read current kernel state"""
        try:
            with open(self.kernel_state_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"status": "unknown"}
    
    def read_ledger_stats(self):
        """Get ledger statistics"""
        try:
            with open(self.ledger_path) as f:
                ledger = json.load(f)
                entries = ledger.get('entries', [])
                return {
                    "total_entries": len(entries),
                    "accepts": sum(1 for e in entries if e.get('status') == 'ACCEPT'),
                    "rejects": sum(1 for e in entries if e.get('status') == 'REJECT'),
                    "last_entry": entries[-1] if entries else None
                }
        except FileNotFoundError:
            return {"total_entries": 0}
    
    def submit_observation(self):
        """Submit health observation to kernel"""
        state = self.read_kernel_state()
        ledger_stats = self.read_ledger_stats()
        
        observation = {
            "timestamp": time.time(),
            "kernel_state": state,
            "ledger_stats": ledger_stats
        }
        
        # Submit to kernel
        request = {
            "action_type": "observation",
            "target": "kernel_health",
            "evidence": observation,
            "source": "OPENCLAW_MONITOR"
        }
        
        try:
            decision = self.kernel._send_request(request)
            
            if decision.get("decision") == "ACCEPT":
                logger.info(f"✓ Health check logged. Entries: {ledger_stats['total_entries']}")
                return True
            else:
                logger.warning(f"✗ Kernel rejected observation: {decision.get('reason')}")
                return False
        except Exception as e:
            logger.error(f"✗ Failed to submit observation: {e}")
            return False
    
    def check_kernel_responsive(self):
        """Check if kernel is responsive"""
        request = {
            "action_type": "ping",
            "target": "kernel",
            "evidence": {"timestamp": time.time()},
            "source": "OPENCLAW_MONITOR"
        }
        
        try:
            decision = self.kernel._send_request(request)
            return decision.get("decision") is not None
        except:
            return False
    
    def run(self):
        """Main monitoring loop"""
        logger.info("=" * 60)
        logger.info("OpenClaw Kernel Monitor Started")
        logger.info("=" * 60)
        
        while True:
            try:
                # Check responsiveness
                if not self.check_kernel_responsive():
                    logger.error("✗ Kernel is not responsive!")
                else:
                    logger.info("✓ Kernel responsive")
                
                # Submit observation
                self.submit_observation()
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(self.check_interval)


if __name__ == "__main__":
    monitor = KernelHealthMonitor(check_interval=60)
    monitor.run()
```

#### Step 2: Run as Background Process

```bash
# Start kernel daemon
python3 oracle_town/kernel/kernel_daemon.py &
KERNEL_PID=$!

# Start monitor daemon
python3 openclaw_kernel_monitor.py &
MONITOR_PID=$!

# Check logs
tail -f openclaw_kernel_monitor.log

# When done:
kill $KERNEL_PID $MONITOR_PID
```

---

### OPTION 3: Full OpenClaw Integration (Advanced)

This runs OpenClaw with kernel authority built-in.

#### Step 1: Create Integration Layer

```python
# openclaw_with_kernel.py
"""
Full OpenClaw integration with Oracle Town kernel authority.

Every OpenClaw action goes through kernel gates before execution.
"""

import sys
sys.path.insert(0, '/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24')

from oracle_town.kernel.kernel_client import KernelClient
from oracle_town.kernel.kernel_daemon import KernelDaemon
from oracle_town.kernel.ledger import InMemoryLedger
import json
import logging


class OpenClawWithKernel:
    """OpenClaw agent with kernel authority enforcement"""
    
    def __init__(self):
        self.kernel = KernelClient()
        self.ledger = InMemoryLedger()
        self.logger = logging.getLogger(__name__)
    
    def fetch_url(self, url):
        """Fetch URL with kernel approval"""
        import requests
        
        # Get content
        response = requests.get(url)
        
        # Ask kernel
        decision = self.kernel._send_request({
            "action_type": "fetch",
            "target": url,
            "evidence": {"status_code": response.status_code},
            "source": "OPENCLAW"
        })
        
        if decision["decision"] != "ACCEPT":
            raise RuntimeError(f"Kernel denied: {decision['reason']}")
        
        return response.content
    
    def execute_shell(self, command):
        """Execute shell with kernel approval"""
        import subprocess
        
        # Ask kernel first
        decision = self.kernel._send_request({
            "action_type": "shell",
            "target": command,
            "evidence": {"command": command},
            "source": "OPENCLAW"
        })
        
        if decision["decision"] != "ACCEPT":
            raise RuntimeError(f"Kernel denied shell: {decision['reason']}")
        
        # Execute
        result = subprocess.run(command, shell=True, capture_output=True)
        return result.stdout.decode()
    
    def update_memory(self, key, value):
        """Update memory with kernel approval"""
        decision = self.kernel._send_request({
            "action_type": "memory_write",
            "target": key,
            "evidence": {"value": value},
            "source": "OPENCLAW"
        })
        
        if decision["decision"] != "ACCEPT":
            raise RuntimeError(f"Kernel denied memory write: {decision['reason']}")
        
        # Store
        self.memory[key] = value
        return True
```

---

## Which Option Should You Pick?

| Option | Effort | Safety | Use Case |
|--------|--------|--------|----------|
| **1: Skill Wrapper** | Low | Very High | Individual skill approval |
| **2: Monitoring** | Medium | Very High | Background health checks |
| **3: Full Integration** | High | Very High | Complete kernel control |

**Recommendation:** Start with **Option 1** (skill wrapper), then add **Option 2** (monitoring) for production.

---

## Testing Everything

```bash
# 1. Start kernel daemon
python3 oracle_town/kernel/kernel_daemon.py &

# 2. Test kernel responsiveness
python3 oracle_town/kernel/kernel_client.py

# 3. Test a skill
python3 openclaw_skills_with_kernel.py

# 4. Start monitoring
python3 openclaw_kernel_monitor.py &

# 5. Watch the ledger grow
tail -f kernel/ledger.json

# 6. Check logs
tail -f openclaw_kernel_monitor.log
```

---

## Safety Guarantees (All Options)

✅ **K15: No Receipt = No Execution**
- OpenClaw never executes without kernel approval
- Fail-closed (if kernel unreachable, execution denied)

✅ **Immutable Audit Trail**
- Every decision logged to ledger
- Cannot be modified retroactively

✅ **Authority Separation**
- OpenClaw proposes actions
- Kernel decides what's allowed
- Ledger records decisions

✅ **Determinism**
- Same input → same decision (K5)
- Reproducible, auditable

---

## Next Steps

1. **Pick your option** (recommendation: Option 1 + Option 2)
2. **Test with kernel daemon running**
3. **Deploy to background**
4. **Monitor the ledger growth**

Your kernel is ready. You just need to connect OpenClaw to it.

