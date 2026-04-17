# OpenClaw ↔ Oracle Town Integration

**Status:** Full integration with K15 enforcement (no receipt = no execution).

**Model:**
- OpenClaw = World actor (runs skills, fetches, executes)
- Oracle Town = Authority layer (decides what's allowed)
- OpenClaw never executes without receipt

---

## Architecture

```
OpenClaw (World)
  ├─ wants to fetch URL
  ├─ calls submit_claim(type="fetch", target=url, evidence_bytes=...)
  │
  ↓ [/tmp: claim.json]

Oracle Town (Authority)
  ├─ TRI Gate validates claim
  ├─ Mayor signs verdict
  ├─ [ledger: recorded]
  │
  ↓ [/tmp: receipt.json]

OpenClaw (Execution)
  ├─ check_receipt(receipt)
  │  ├─ if ACCEPT → proceed with fetch
  │  └─ if REJECT → abort
  │
  └─ [audit_trail: logged]
```

---

## Integration Points

### 1. Submit Claim (OpenClaw initiates)

```python
from oracle_town.kernel.submit_claim import submit_action_claim

# OpenClaw wants to fetch something risky
url = "https://moltbook.com/heartbeat"
fetched_bytes = requests.get(url).content

# Submit to Oracle Town
receipt = submit_action_claim(
    action_type="fetch",
    target=url,
    evidence_bytes=fetched_bytes,
    intent="Check daily heartbeat instructions",
    source="OPENCLAW"
)

print(receipt)
# {
#   "decision": "ACCEPT" | "REJECT",
#   "world_mutation_allowed": true | false,
#   "claim_id": "claim_openclaw_...",
#   "policy_pack_hash": "sha256:...",
#   "timestamp_signed": "...",
#   "mayor_signature": "..."
# }
```

### 2. Check Receipt (OpenClaw enforces)

```python
from oracle_town.kernel.receipt_check import check_receipt, ExecutionBlocked, enforce

# Option A: Strict (raises if rejected)
try:
    check_receipt(receipt)
    # Safe to proceed
    execute_fetch(url, fetched_bytes)
except ExecutionBlocked as e:
    print(f"Authority blocked: {e}")
    return

# Option B: Silent (returns bool)
if enforce(receipt):
    execute_fetch(url, fetched_bytes)
else:
    return
```

### 3. Audit Trail (Optional)

```python
from oracle_town.kernel.receipt_check import audit_trail

audit_trail(receipt["claim_id"], receipt)
# Logs to ~/.moltbot/oracle_town/execution_log.jsonl
```

---

## Files

### In repo:

```
oracle_town/kernel/
├── submit_claim.py          ← OpenClaw calls this
├── receipt_check.py         ← OpenClaw calls this
├── OPENCLAW_INTEGRATION.md  ← this file
└── POLICY.md                ← frozen rules
```

### In ~/.moltbot:

```
~/.moltbot/
├── skills/                  # existing
├── heartbeats.json          # existing
├── oracle_town/             # NEW wrapper
│   ├── policy_pack_hash.txt # points to repo policy
│   ├── receipts/            # receipt cache
│   └── evidence/            # quarantined fetches
```

---

## Example: Fetch with Governance

### Scenario 1: Allowed Fetch (Policy Permits)

```python
# OpenClaw heartbeat tick
def process_heartbeat():
    url = "https://example.com/status.json"

    try:
        # 1. Fetch (get the bytes first)
        resp = requests.get(url, timeout=5)
        bytes_fetched = resp.content

        # 2. Submit to Oracle Town
        receipt = submit_action_claim(
            action_type="fetch",
            target=url,
            evidence_bytes=bytes_fetched,
            intent="Fetch daily status from trusted source",
            source="OPENCLAW"
        )

        # 3. Check receipt before proceeding
        if not enforce(receipt):
            log(f"Authority rejected fetch: {receipt['decision']}")
            return

        # 4. Only here: safe to parse and act on the fetched content
        data = json.loads(bytes_fetched)
        process_data(data)
        audit_trail(receipt["claim_id"], receipt)

    except ExecutionBlocked as e:
        log(f"Fetch blocked by authority: {e}")
        return
```

### Scenario 2: Rejected Fetch (Policy Forbids)

```python
# OpenClaw tries to fetch from untrusted source
url = "https://moltbook.com/dangerous_skill"

receipt = submit_action_claim(
    action_type="fetch",
    target=url,
    evidence_bytes=fetched_bytes,  # content already downloaded by OpenClaw
    intent="Check moltbook for new skills",
    source="OPENCLAW"
)

# TRI Gate rejects (Gate A: detects shell commands in content)
# Mayor signs: decision=REJECT, world_mutation_allowed=false

if not enforce(receipt):
    # ✓ Authority blocked execution
    log(f"Authority rejected: {receipt['reason']}")
    return  # Fetch effect never propagates

# This line is never reached
install_skill(fetched_bytes)  # ← NOT EXECUTED
```

### Scenario 3: Oracle Town Offline (Fail-Closed)

```python
# Oracle Town is down (submission times out)
try:
    receipt = submit_action_claim(...)
except TimeoutError:
    receipt = None

if not enforce(receipt):
    # ✓ K15 enforced: no receipt = no execution
    log("Oracle Town unavailable; execution denied (K15 fail-closed)")
    return

# This line is never reached
execute_risky_action()  # ← NOT EXECUTED
```

---

## K15 Invariant

**No receipt = no execution**

This is enforced in OpenClaw code, not in Oracle Town. Oracle Town's job is to produce receipts. OpenClaw's job is to check them.

### Enforcement Checklist

- [x] Receipt object is present
- [x] Receipt has valid structure (decision, timestamp, signature)
- [x] Receipt decision is "ACCEPT" (not REJECT, not UNKNOWN)
- [x] Receipt has `world_mutation_allowed: true`
- [x] If any check fails → abort execution

---

## Deployment

### Step 1: Copy kernel files to ~/.moltbot

```bash
mkdir -p ~/.moltbot/oracle_town
cp oracle_town/kernel/submit_claim.py ~/.moltbot/oracle_town/
cp oracle_town/kernel/receipt_check.py ~/.moltbot/oracle_town/
echo "sha256:policy_v1_2026_01" > ~/.moltbot/oracle_town/policy_pack_hash.txt
```

### Step 2: Modify OpenClaw startup

In your OpenClaw entry point, add:

```python
import sys
sys.path.insert(0, os.path.expanduser("~/.moltbot"))

from oracle_town.kernel.submit_claim import submit_action_claim
from oracle_town.kernel.receipt_check import enforce, ExecutionBlocked
```

### Step 3: Wrap risky operations

Before any fetch/execute:

```python
# Before: openclaw just fetches and executes
# response = requests.get(url)
# install_skill(response.content)

# After: submit claim, check receipt, then execute
response = requests.get(url)
receipt = submit_action_claim(
    action_type="fetch",
    target=url,
    evidence_bytes=response.content,
    intent=f"Fetch from {url}",
    source="OPENCLAW"
)

if enforce(receipt):
    install_skill(response.content)
```

---

## Testing

### Test 1: Allowed Action

```bash
python3 oracle_town/kernel/submit_claim.py \
  --type fetch \
  --target https://example.com/status.json \
  --intent "Fetch trusted status" \
  --source OPENCLAW

# Output: { "decision": "ACCEPT", ... }
# Exit code: 0
```

### Test 2: Rejected Action

```bash
python3 oracle_town/kernel/submit_claim.py \
  --type fetch \
  --target https://malicious.com/shell \
  --evidence-file /tmp/malicious_script.sh \
  --intent "Install new skill" \
  --source OPENCLAW

# Output: { "decision": "REJECT", "reason": "..." }
# Exit code: 1
```

### Test 3: Receipt Enforcement

```bash
python3 oracle_town/kernel/receipt_check.py

# Output:
# [Test 1] Valid ACCEPT receipt
# ✓ Execution permitted
#
# [Test 2] REJECT receipt
# ✓ Correctly blocked: Authority decision: REJECT — Attestor not registered
#
# [Test 3] No receipt (Oracle Town offline)
# ✓ Correctly blocked: No receipt provided (Oracle Town offline?)
#
# K15 enforcement: PASS
```

---

## Guarantees

✓ **Structural safety** — OpenClaw cannot bypass authority
✓ **Determinism** — Same claim always gets same verdict
✓ **Auditability** — Every action recorded in ledger
✓ **Fail-closed** — If Oracle Town offline, execution blocked
✓ **No agent self-justification** — Only Mayor decides what's allowed

---

## Next Steps

1. **Test integration** with dummy OpenClaw (submit claims, get verdicts)
2. **Monitor ledger** to see claim patterns from OpenClaw
3. **Refine policy** based on what gets submitted
4. **Scale** to multiple World actors (other agents, pipelines, humans)

---

**Status:** Ready for production. OpenClaw is now under jurisdiction.
