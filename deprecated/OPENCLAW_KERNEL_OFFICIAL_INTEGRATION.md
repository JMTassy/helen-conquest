# OpenClaw Official Integration — Oracle Town Kernel

**Date:** February 16, 2026
**Status:** Ready for Integration
**Compatibility:** OpenClaw Node 22+

---

## What This Is

This guide shows how to integrate the Oracle Town Kernel with **official OpenClaw** (the real system at openclaw.ai).

Our kernel is:
- ✅ A safety layer for OpenClaw agents
- ✅ A governance system for multi-agent coordination
- ✅ An audit trail for compliance
- ✅ A fail-closed execution framework

---

## Official OpenClaw Architecture

```
┌─────────────────────────────────────────┐
│  OpenClaw CLI (Node 22+)                │
│  • openclaw doctor (diagnostics)        │
│  • openclaw status (gateway status)     │
│  • openclaw dashboard (web UI)          │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  OpenClaw Gateway                       │
│  • Agent orchestration                  │
│  • Skill coordination                   │
│  • Message routing                      │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  OpenClaw Agents                        │
│  • Execute skills                       │
│  • Manage state                         │
│  • Process tasks                        │
└─────────────────────────────────────────┘
```

---

## Our Kernel Layer (Addition)

```
┌─────────────────────────────────────────┐
│  OpenClaw Agents (Official)             │
└─────────────────────────────────────────┘
         ↓
    [NEW: Oracle Town Kernel]
    ├─ Request approval for actions
    ├─ Enforce governance policies
    └─ Log all decisions to ledger
         ↓
┌─────────────────────────────────────────┐
│  Action Execution (safe)                │
│  • fetch (approved URLs only)           │
│  • shell (approved commands only)       │
│  • memory (approved writes only)        │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Immutable Ledger (kernel/ledger.json)  │
│  • Every decision logged                │
│  • Timestamp + evidence                 │
│  • Compliance-ready audit trail         │
└─────────────────────────────────────────┘
```

---

## Installation

### Step 1: Install Official OpenClaw

Follow the official installation at https://docs.openclaw.ai/install

**macOS/Linux/WSL2:**
```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

**Verify installation:**
```bash
openclaw doctor
openclaw status
```

### Step 2: Install Oracle Town Kernel

The kernel is already in your repository at:
```
oracle_town/kernel/kernel_daemon.py
```

No additional installation needed. Just run:
```bash
python3 oracle_town/kernel/kernel_daemon.py &
```

---

## Integration Pattern

### With OpenClaw Skills

Official OpenClaw skills can be wrapped with kernel approval:

```python
# With official OpenClaw
from openclaw.skills import fetch, shell

# Wrap with kernel approval
from openclaw_skills_with_kernel import FetchSkill, ShellSkill

class KernelApprovedOpenClawAgent:
    def __init__(self):
        # Use kernel-approved skills
        self.fetch = FetchSkill()
        self.shell = ShellSkill()

    def execute_task(self):
        # Official OpenClaw task, but with kernel governance
        data = self.fetch.fetch("https://api.example.com/data")
        result = self.shell.execute("python3 process.py")
        return result
```

### With OpenClaw Gateway

OpenClaw Gateway orchestrates agents. Our kernel sits in the execution layer:

```
OpenClaw Gateway
    ├─ Task: "Fetch data and process"
    │
    ├─ Route to Agent
    │   └─ Agent.fetch()    ──→ Kernel approval ──→ Fetch
    │   └─ Agent.shell()    ──→ Kernel approval ──→ Shell
    │
    └─ Log results to ledger
```

**No changes needed to OpenClaw Gateway.** The kernel sits transparently in the agent layer.

---

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# Terminal 1: Official OpenClaw
openclaw dashboard

# Terminal 2: Kernel daemon
python3 oracle_town/kernel/kernel_daemon.py &

# Terminal 3: Your agent (uses kernel skills)
python3 my_agent.py
```

### Scenario 2: Production with OpenClaw Gateway

```bash
# Start OpenClaw officially
openclaw start

# Start kernel daemon (separate terminal)
python3 oracle_town/kernel/kernel_daemon.py &

# Agents registered with OpenClaw Gateway use kernel skills
# All actions logged to kernel/ledger.json
```

### Scenario 3: Docker + OpenClaw

```dockerfile
FROM node:22

# Install OpenClaw
RUN curl -fsSL https://openclaw.ai/install.sh | bash

# Copy kernel
COPY oracle_town /app/oracle_town
WORKDIR /app

# Start both
CMD ["sh", "-c", "openclaw start & python3 oracle_town/kernel/kernel_daemon.py"]
```

---

## Configuration

### Kernel Policy (oracle_town/kernel/policy.json)

Define what OpenClaw agents can do:

```json
{
  "policies": {
    "openclaw_agent_default": {
      "fetch": {
        "allow_domains": [
          "api.example.com",
          "*.company.com"
        ],
        "deny_external": true
      },
      "shell": {
        "allow_paths": [
          "/opt/openclaw/scripts/*"
        ],
        "deny_dangerous": true
      },
      "memory": {
        "allow_all": true
      }
    }
  }
}
```

### Kernel Environment

```bash
# Set kernel home (where ledger is stored)
export OPENCLAW_KERNEL_HOME=/var/openclaw/kernel

# Set kernel listen port
export OPENCLAW_KERNEL_PORT=9000

# Start kernel
python3 oracle_town/kernel/kernel_daemon.py
```

---

## Integration with Official OpenClaw Features

### OpenClaw Dashboard Integration

The OpenClaw dashboard shows agent activity. Our kernel ledger adds governance layer:

```
OpenClaw Dashboard (agents, tasks, status)
         ↓
Oracle Town Kernel (governance, approvals, ledger)
         ↓
kernel/ledger.json (audit trail)
```

You can:
- See what OpenClaw agents tried to do (dashboard)
- See what kernel approved/denied (ledger)
- Track compliance (audit trail)

### OpenClaw Skills Integration

Official OpenClaw skills + kernel approval:

```python
# Official OpenClaw skill
from openclaw.skills import database_query

# Wrapped with kernel
from openclaw_skills_with_kernel import DatabaseSkill

database_skill = DatabaseSkill()  # Requires kernel approval
result = database_skill.query("SELECT * FROM users")  # Kernel decides
```

### OpenClaw Multi-Agent Coordination

OpenClaw Gateway routes tasks to agents. Kernel ensures governance:

```
Task (OpenClaw Gateway)
    ├─ Agent 1: fetch.fetch(url)      ──→ Kernel: OK for team_data
    ├─ Agent 2: shell.execute(cmd)    ──→ Kernel: DENIED for team_data
    └─ Agent 3: memory.write(data)    ──→ Kernel: OK for team_data
```

---

## Monitoring

### OpenClaw Status

```bash
openclaw status
# Shows: gateway running, agents connected, tasks processed
```

### Kernel Status

```bash
# Check kernel is running
curl -s http://localhost:9000/health

# Check ledger
cat kernel/ledger.json | jq '.entries[] | {action_type, status}'

# Check approvals by agent
cat kernel/ledger.json | jq '.entries[] | {agent: .source, status}' | sort | uniq -c
```

### Unified Monitoring

```bash
# OpenClaw agent output
openclaw dashboard

# Kernel approvals
watch -n 2 "cat kernel/ledger.json | jq '.entries[-1]'"

# Both in split terminal
```

---

## Compliance & Audit Trail

### OpenClaw provides:
- Task history (what agents were asked to do)
- Agent logs (what agents tried)
- Gateway routing (how tasks were coordinated)

### Kernel adds:
- Approval decisions (what kernel allowed/denied)
- Evidence (what was requested, by whom)
- Immutable ledger (compliance-ready audit trail)
- Complete governance (who did what, when, why)

### Together:
**Complete visibility into agent execution with governance enforcement**

---

## Troubleshooting

### "Agent can't reach kernel"
```bash
# Check kernel is running
ps aux | grep kernel_daemon

# Check port
netstat -an | grep 9000

# Restart kernel
python3 oracle_town/kernel/kernel_daemon.py &
```

### "Kernel rejecting all actions"
```bash
# Check policy
cat oracle_town/kernel/policy.json

# Check ledger for rejection reason
cat kernel/ledger.json | jq '.entries[-1] | {status, reason}'

# Update policy or agent configuration
```

### "OpenClaw and Kernel out of sync"
```bash
# Restart both (order doesn't matter)
openclaw stop
python3 oracle_town/kernel/kernel_daemon.py &
openclaw start
```

---

## Next Steps

### For Development:
1. Install official OpenClaw (https://docs.openclaw.ai/install)
2. Start OpenClaw dashboard (`openclaw dashboard`)
3. Start kernel daemon (`python3 oracle_town/kernel/kernel_daemon.py &`)
4. Create agent using kernel skills
5. Watch both dashboard and ledger

### For Production:
1. Deploy OpenClaw officially (using their infrastructure)
2. Run kernel daemon on same/nearby machine
3. Configure kernel policy for your agents
4. Monitor both OpenClaw dashboard and kernel ledger
5. Archive ledger periodically

### For Compliance:
1. OpenClaw logs: agent activity and task routing
2. Kernel ledger: approval decisions and governance
3. Together: complete audit trail for regulators

---

## Example: Complete Workflow

```bash
# Step 1: Install and start OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw start

# Step 2: Start kernel daemon
python3 oracle_town/kernel/kernel_daemon.py &

# Step 3: Create agent (uses kernel skills)
cat > openclaw_agent.py << 'EOF'
from openclaw_skills_with_kernel import FetchSkill, ShellSkill

class MyOpenClawAgent:
    def __init__(self):
        self.fetch = FetchSkill()
        self.shell = ShellSkill()

    def process_data(self):
        # Fetch data (kernel approves)
        data = self.fetch.fetch("https://api.company.com/data")

        # Process (kernel approves)
        result = self.shell.execute("python3 /opt/process.py")

        return result

# Register with OpenClaw
agent = MyOpenClawAgent()
EOF

# Step 4: Monitor
# Terminal A: OpenClaw dashboard
openclaw dashboard

# Terminal B: Kernel ledger
watch -n 1 "cat kernel/ledger.json | jq '.entries[-3:]'"

# Terminal C: Agent execution
python3 openclaw_agent.py
```

---

## Compatibility

| Component | Version | Status |
|-----------|---------|--------|
| **OpenClaw** | Node 22+ | ✅ Compatible |
| **Oracle Town Kernel** | 1.0 | ✅ Ready |
| **Python** | 3.8+ | ✅ Required |
| **Docker** | Any | ✅ Supported |
| **Kubernetes** | Any | ✅ Supported |

---

## Summary

**The Oracle Town Kernel is a governance layer for official OpenClaw agents.**

It adds:
- ✅ Approval required for all actions
- ✅ Complete audit trail
- ✅ Policy enforcement
- ✅ Fail-closed execution
- ✅ Compliance support

**No changes to OpenClaw needed.** The kernel sits transparently in the agent execution layer.

---

## Resources

- **Official OpenClaw:** https://docs.openclaw.ai
- **Kernel Skills:** `openclaw_skills_with_kernel.py`
- **Kernel Daemon:** `oracle_town/kernel/kernel_daemon.py`
- **Integration Guide:** `HOW_TO_USE_OPENCLAW_KERNEL.md`
- **Quick Start:** `QUICK_START_BY_USE_CASE.txt`

---

**Ready to integrate with official OpenClaw? Start with:**

```bash
# 1. Install OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash

# 2. Start kernel
python3 oracle_town/kernel/kernel_daemon.py &

# 3. Create agent with kernel skills
# Done!
```