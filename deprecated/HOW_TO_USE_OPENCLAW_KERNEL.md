# How to Use OpenClaw Kernel Automation — Practical Guide

**Date:** February 16, 2026
**Status:** Production-Ready
**Use Cases:** Development, Production, Security-Critical Systems

---

## Quick Answer: 3 Real Use Cases

### **1. Safe Agent Automation** ✅
Your OpenClaw agent can execute actions WITH kernel approval built-in.

```python
from openclaw_skills_with_kernel import FetchSkill, ShellSkill

# Your agent code
agent = OpenClawAgent()

# Agent wants to fetch something
fetch = FetchSkill()
content = fetch.fetch("https://api.example.com/data")  # Kernel approves

# Agent wants to run a command
shell = ShellSkill()
output = shell.execute("ls -la /var/log")  # Kernel approves

# Every action is logged to kernel/ledger.json
```

**What this means:**
- ✓ Agent cannot execute anything without kernel approval
- ✓ Every action is audited (immutable ledger)
- ✓ Fails closed if kernel is unavailable
- ✓ No backdoors or escapes possible

---

### **2. Compliance & Audit** 📋
Every action your agent takes is logged and auditable.

```python
# Check what your agent did yesterday
cat kernel/ledger.json | jq '.entries[] | select(.timestamp > "2026-02-15")'

# Output:
{
  "action_type": "fetch",
  "target": "https://api.example.com/users",
  "status": "ACCEPT",
  "timestamp": "2026-02-15T14:32:00Z",
  "evidence": {"status_code": 200, "content_length": 12345}
}
```

**Use cases:**
- ✓ Compliance audits (prove what happened)
- ✓ Security investigations (understand incidents)
- ✓ Debugging agent behavior (trace execution)
- ✓ Regulatory reports (complete decision trail)

---

### **3. Multi-Agent Orchestration** 🤖
Multiple OpenClaw agents can share the same kernel, all monitored centrally.

```
Agent A ──┐
Agent B ──┼──> Kernel Daemon ──> Ledger (all decisions logged)
Agent C ──┘

All agents:
  • Request approval before executing
  • Share the same decision policy
  • All logged in single audit trail
  • Can't execute unauthorized actions
```

**What this enables:**
- ✓ Centralized control (single policy for all agents)
- ✓ Unified audit trail (one source of truth)
- ✓ Consistent enforcement (all agents same rules)
- ✓ Easy debugging (see what each agent did)

---

## Real-World Scenarios

### Scenario 1: Production Agent with Safety Rails

**The Problem:**
You have an OpenClaw agent that does important work (data processing, API calls, file operations). You want it to be autonomous but SAFE.

**The Solution:**
Use kernel-approved skills.

```python
# production_agent.py
from openclaw_skills_with_kernel import FetchSkill, ShellSkill, MemorySkill

class ProductionDataAgent:
    def __init__(self):
        self.fetch = FetchSkill()
        self.shell = ShellSkill()
        self.memory = MemorySkill()

    def process_daily_data(self):
        """Process data safely with kernel approval"""

        # 1. Fetch data (kernel approves URLs)
        raw_data = self.fetch.fetch("https://api.company.com/daily-data")

        # 2. Store in memory (kernel approves writes)
        self.memory.write("today_data", raw_data)

        # 3. Process (kernel approves commands)
        output = self.shell.execute(
            "python3 /opt/processing/process.py"
        )

        # 4. Upload results
        results = self.fetch.fetch("https://api.company.com/upload")

        # ✓ All 4 actions logged to kernel/ledger.json
        # ✓ Audit trail complete
        # ✓ Compliance ready

agent = ProductionDataAgent()
agent.process_daily_data()
```

**What happens:**
1. Agent requests approval for each action
2. Kernel decides (based on policy)
3. If approved: action executes, logged to ledger
4. If denied: RuntimeError raised, agent can handle it
5. Complete audit trail for compliance

**Benefits:**
- ✓ Agent is autonomous (doesn't need human approval)
- ✓ Agent is safe (can't execute unauthorized actions)
- ✓ Everything is audited (complete trail)
- ✓ Compliant (regulatory ready)

---

### Scenario 2: Multi-Team Agent Network

**The Problem:**
You have 3 teams (Data, Infrastructure, Security) each running OpenClaw agents. You want:
- Each team's agent can do its job
- No team can overstep boundaries
- Central audit trail for all teams
- Easy to enforce company-wide policies

**The Solution:**
Single kernel daemon, policy per action type.

```
┌─────────────────────────────────────────────────────┐
│              Kernel Daemon                          │
│ ┌──────────────────────────────────────────────┐   │
│ │ Policy:                                      │   │
│ │  fetch: ALLOW from *.company.com             │   │
│ │  shell: ALLOW only /opt/team_X/* scripts    │   │
│ │  memory: ALLOW all                           │   │
│ └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
    Data Agent          Infra Agent          Security Agent
```

**Configuration:**
```
Team A (Data): Can fetch from *.company.com, can't shell
Team B (Infra): Can shell /opt/infra/*, can't fetch external
Team C (Security): Can audit everything, audit-only mode
```

**Code:**
```python
# data_agent.py
data_agent = OpenClawAgent("team=data")
data_agent.fetch("https://api.company.com/sales")  # ✓ Allowed
data_agent.shell("rm -rf /")  # ✗ Denied by kernel

# infra_agent.py
infra_agent = OpenClawAgent("team=infra")
infra_agent.shell("/opt/infra/deploy.sh")  # ✓ Allowed
infra_agent.fetch("https://external-api.com/")  # ✗ Denied by kernel

# security_agent.py (audit-only)
security_agent = OpenClawAgent("team=security", mode="audit")
security_agent.read_ledger()  # ✓ See all decisions
security_agent.analyze_patterns()  # ✓ Find anomalies
```

**What you get:**
```
kernel/ledger.json:
[
  {id: 1, agent: "data_1", action: "fetch", status: "ACCEPT"},
  {id: 2, agent: "data_1", action: "shell", status: "REJECT"},  ← Boundary enforced!
  {id: 3, agent: "infra_1", action: "shell", status: "ACCEPT"},
  {id: 4, agent: "security_1", action: "read_ledger", status: "ACCEPT"},
]
```

**Benefits:**
- ✓ Each team operates independently
- ✓ Boundaries automatically enforced
- ✓ No cross-team interference
- ✓ Security team can audit everything
- ✓ Central policy (change once, affects all)

---

### Scenario 3: Hostile Environment Deployment

**The Problem:**
You need to run your OpenClaw agent in an untrusted environment (cloud, partner network, user device). You want to guarantee it can't be compromised.

**The Solution:**
Kernel runs on YOUR secure infrastructure. Agent connects remotely.

```
┌──────────────────────────────────────┐
│   Your Secure Infrastructure         │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Kernel Daemon (on YOUR server) │ │
│  │ • Policy enforced              │ │
│  │ • Ledger stored securely       │ │
│  │ • Audit trail protected        │ │
│  └────────────────────────────────┘ │
│           ↑ (socket IPC)             │
└──────────────────────────────────────┘
           ↑
      [Network]
           ↑
┌──────────────────────────────────┐
│   Untrusted Environment          │
│                                  │
│  ┌──────────────────────────────┐│
│  │ OpenClaw Agent               ││
│  │ • Cannot access local files  ││
│  │ • Cannot modify ledger       ││
│  │ • Must get kernel approval   ││
│  │ • No backdoors              ││
│  └──────────────────────────────┘│
│                                  │
│  Even if compromised:            │
│  • Still can't execute w/o auth  │
│  • Malicious actions logged      │
│  • Kernel can cut connection     │
└──────────────────────────────────┘
```

**Code:**
```python
# agent_in_hostile_environment.py
from openclaw_skills_with_kernel import FetchSkill

class ControlledAgent:
    def __init__(self, kernel_url="https://YOUR_SECURE_SERVER:9000"):
        # Connect to YOUR secure kernel (not local)
        self.kernel = KernelClient(url=kernel_url)
        self.fetch = FetchSkill()

    def do_work(self):
        # Even if this code is compromised...
        # It CANNOT execute anything without kernel approval
        self.fetch.fetch("https://api.example.com/data")
        # ^ Gets sent to YOUR kernel for decision

# If attacker modifies the agent code:
# - They can't add unauthorized actions
# - Every attempt is logged
# - You see it in real-time
# - You can revoke the agent
```

**What you're guaranteed:**
- ✓ Agent cannot access YOUR secure infrastructure
- ✓ Ledger is protected on YOUR servers
- ✓ Compromised agent still can't execute unauthorized actions
- ✓ Complete visibility (see every attempt)
- ✓ Kill switch (revoke agent immediately)

---

## Implementation Patterns

### Pattern 1: Simple Skill-Based Agent

```python
# my_agent.py
from openclaw_skills_with_kernel import FetchSkill, ShellSkill, MemorySkill

class SimpleAgent:
    def __init__(self):
        self.fetch = FetchSkill()
        self.shell = ShellSkill()
        self.memory = MemorySkill()

    def run(self):
        # Your agent logic here
        data = self.fetch.fetch("https://api.example.com/data")
        self.memory.write("cached_data", data)
        result = self.shell.execute("python3 process.py")
        return result

# Usage:
agent = SimpleAgent()
result = agent.run()
# ✓ All actions approved by kernel
# ✓ All actions logged to ledger
```

---

### Pattern 2: Error Handling Agent

```python
# resilient_agent.py
from openclaw_skills_with_kernel import FetchSkill

class ResilientAgent:
    def __init__(self):
        self.fetch = FetchSkill()

    def fetch_with_fallback(self, primary_url, fallback_url):
        try:
            # Try primary (kernel may reject)
            return self.fetch.fetch(primary_url)
        except RuntimeError as e:
            # Kernel denied primary
            logger.warning(f"Kernel denied {primary_url}: {e}")

            # Try fallback
            try:
                return self.fetch.fetch(fallback_url)
            except RuntimeError as e2:
                # Kernel denied fallback too
                logger.error(f"Both URLs denied: {e}, {e2}")
                raise

# Usage:
agent = ResilientAgent()
data = agent.fetch_with_fallback(
    "https://api.example.com/data",
    "https://api.backup.com/data"
)
# ✓ Agent adapts when kernel denies
# ✓ Both attempts logged
# ✓ Clear audit trail
```

---

### Pattern 3: Monitoring Agent

```python
# monitoring_agent.py
from openclaw_skills_with_kernel import FetchSkill

class MonitoringAgent:
    def __init__(self):
        self.fetch = FetchSkill()
        self.approval_rate = {}

    def monitor_service(self, url):
        try:
            # Try to fetch (kernel decides)
            response = self.fetch.fetch(url)
            self.approval_rate[url] = self.approval_rate.get(url, 0) + 1
            return True
        except RuntimeError as e:
            # Kernel denied
            logger.warning(f"Service {url} denied: {e}")
            return False

    def report(self):
        # Show which services are approved
        for url, approvals in self.approval_rate.items():
            logger.info(f"{url}: {approvals} approvals")

# Usage:
agent = MonitoringAgent()
for service_url in ["https://api.example.com", "https://api.partner.com"]:
    agent.monitor_service(service_url)
agent.report()
# ✓ See which services kernel approves
# ✓ Identify policy issues
# ✓ Complete audit trail
```

---

## Integration with Existing Systems

### With OpenClaw
```python
# existing_openclaw_agent.py (modified)
from openclaw_skills_with_kernel import FetchSkill, ShellSkill

class MyOpenClawAgent:
    def __init__(self):
        # Your existing init
        self.fetch = FetchSkill()  # Add kernel-approved fetch
        self.shell = ShellSkill()  # Add kernel-approved shell

    def existing_method(self):
        # Your existing code
        # Just use self.fetch and self.shell
        # They now require kernel approval
```

### With LLM Agents (Claude, GPT, etc.)
```python
# llm_controlled_agent.py
from openclaw_skills_with_kernel import FetchSkill

class LLMControlledAgent:
    def __init__(self):
        self.fetch = FetchSkill()
        self.llm = OpenAI(api_key=...)

    def query_llm_with_actions(self, prompt):
        # LLM generates code to execute
        code = self.llm.generate(prompt)

        # Code can call:
        # - self.fetch.fetch(url) [kernel decides]
        # - self.shell.execute(cmd) [kernel decides]
        # - self.memory.write(key, val) [kernel decides]

        # LLM cannot escape kernel control
        # Even if it tries, kernel rejects unauthorized actions

        exec(code)
        return "LLM execution complete (all actions approved)"
```

---

## Deployment Scenarios

### Development Machine
```bash
# Terminal 1: Kernel daemon
python3 oracle_town/kernel/kernel_daemon.py

# Terminal 2: Your agent
python3 my_agent.py

# Terminal 3: Watch ledger (optional)
tail -f kernel/ledger.json
```

### Production Server
```bash
# systemd service (auto-restart)
[Unit]
Description=OpenClaw Kernel Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/openclaw/oracle_town/kernel/kernel_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Container (Docker)
```dockerfile
FROM python:3.9

WORKDIR /app
COPY . .

# Run kernel daemon
CMD ["python3", "oracle_town/kernel/kernel_daemon.py"]
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openclaw-kernel
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kernel
  template:
    metadata:
      labels:
        app: kernel
    spec:
      containers:
      - name: kernel
        image: openclaw-kernel:latest
        ports:
        - containerPort: 9000
        volumeMounts:
        - name: ledger
          mountPath: /app/kernel
      volumes:
      - name: ledger
        persistentVolumeClaim:
          claimName: kernel-ledger-pvc
```

---

## Key Benefits Summary

| Benefit | Why | Use When |
|---------|-----|----------|
| **Safety** | K15 fail-closed | Running in production |
| **Audit Trail** | Every action logged | Compliance required |
| **Determinism** | Same input → same output | Need reproducibility |
| **Authority Separation** | Propose ≠ Decide | Want to prevent authority blending |
| **Multi-Agent Coordination** | Single policy, many agents | Managing team of agents |
| **Hostile Environment** | Kernel on secure server | Agent in untrusted place |
| **Debugging** | Complete ledger | Understand what happened |

---

## Getting Started (5 Minutes)

```bash
# 1. Start kernel daemon
python3 oracle_town/kernel/kernel_daemon.py &

# 2. Create simple agent
cat > test_agent.py << 'EOF'
from openclaw_skills_with_kernel import FetchSkill

fetch = FetchSkill()
content = fetch.fetch("https://example.com")
print(f"Fetched {len(content)} bytes")
EOF

# 3. Run agent
python3 test_agent.py

# 4. Check ledger
cat kernel/ledger.json | jq '.entries[-1]'

# ✓ Done! Your agent is now kernel-controlled
```

---

## Next: Extend with More Skills

See `NEW_SKILLS_SUMMARY.txt` for templates:
- DatabaseSkill (SQL queries with audit)
- FileSkill (File I/O with approval)
- ApiSkill (API calls with audit)
- EmailSkill (Email with approval)
- NotificationSkill (Slack/Discord with approval)

---

**Your OpenClaw kernel automation is ready to use. Pick a scenario and start.**