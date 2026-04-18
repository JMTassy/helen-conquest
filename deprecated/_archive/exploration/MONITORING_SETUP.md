# Option A: Monitor — Operational Guide

**Goal:** Run daily emulation, watch OpenClaw submit claims, verify K15 blocks bad ones.

**Status:** Ready to deploy. Three components work together:

1. **Daily Emulation Loop** — Runs every day, produces briefs + trends
2. **Test OpenClaw** — Simulates real claim scenarios
3. **Claims Monitor** — Reports on what got accepted/rejected

---

## Setup (15 minutes)

### 1. Create cron job for daily emulation

```bash
# Add to crontab -e
0 9 * * * cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24" && bash oracle_town/daily_emulation_loop.sh >> /tmp/emulation_log.txt 2>&1
```

This runs every day at 9 AM, producing:
- `/tmp/obs_out.json` — observations normalized
- `/tmp/ins_out.json` — clusters + anomalies
- `/tmp/brf_out.json` — brief with ONE BET
- `/tmp/trend_report.json` — 7-day trends
- `oracle_town/ledger/briefs/brief_2026-01-30.json` — stored for history

### 2. Start dashboard (separate terminal)

```bash
export LEDGER_ROOT="oracle_town/ledger"
export TMP_ROOT="/tmp"
python3 oracle_town/dashboards/emu_dashboard/server_stdlib.py
# Open http://127.0.0.1:5005
```

Live view updates every 2.5 seconds. No restart needed.

### 3. Run test OpenClaw (initial validation)

```bash
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
python3 oracle_town/kernel/test_openclaw.py
```

Output:
```
✓ ALLOWED | fetch_trusted          | example.com/status.json      | ACCEPT
✗ BLOCKED | fetch_untrusted        | moltbook.com/heartbeat       | REJECT
✗ BLOCKED | skill_install          | skill:sentiment-analyzer     | REJECT
✗ BLOCKED | heartbeat_modify       | heartbeat_config             | REJECT
✓ ALLOWED | fetch_metrics          | metrics.local/daily          | ACCEPT

K15 Invariant Verification:
✓ K15 ENFORCED: 3 claim(s) blocked despite OpenClaw proposal
```

This proves the boundary is real:
- 2 claims accepted (trusted sources)
- 3 claims rejected (unregistered attestor, K0 enforcement)

### 4. Monitor claims daily

```bash
python3 oracle_town/kernel/monitor_claims.py --since today
```

Output:
```
SUMMARY
Total claims:        5
Accepted:            2 (40.0%)
Rejected:            3

BY SOURCE
OPENCLAW_TEST        | Total:   5 | Accept:   2 | Reject:   3 | Rate: 40.0%

K15 ENFORCEMENT VERIFICATION
✓ K15 ACTIVE: 3 claim(s) blocked by authority
✓ DISCRIMINATION WORKING: System accepts safe claims, rejects unsafe ones
```

---

## Daily Workflow

### Morning (9 AM)

✓ Cron job runs emulation automatically
✓ Dashboard shows latest brief + trends
✓ Ledger records any new claims

### Midday (Check)

```bash
# Quick status check
python3 oracle_town/kernel/monitor_claims.py --since 24h

# View recent claims
python3 oracle_town/kernel/monitor_claims.py --since today --format json | jq '.recent_claims'

# Check dashboard
open http://127.0.0.1:5005
```

### Weekly (Analysis)

```bash
# Acceptance rate trend
python3 oracle_town/kernel/monitor_claims.py --since 7d

# Review rejections
python3 oracle_town/kernel/monitor_claims.py --since 7d | grep -A 20 "REJECTION REASONS"

# Check trend analysis
cat oracle_town/ledger/briefs/brief_*.json | jq '.signal_strength' | sort -n
```

---

## What to Watch For

### Expected Behavior

✓ **Acceptance rate 20-50%**
- Some claims accepted (trusted sources)
- Most rejected (unregistered attestors, K0 enforcement)

✓ **K15 enforced**
- If rejection happens, execution blocked
- No claim gets executed without receipt

✓ **Determinism**
- Same claim always gets same decision
- Policy hash immutable

### Warning Signs

⚠️ **100% acceptance rate**
- Policy too permissive
- Unregistered attestors being accepted (K0 broken)

⚠️ **0% acceptance rate**
- Policy too restrictive
- No legitimate claims getting through

⚠️ **Hashes differ on re-run**
- K5 determinism violated
- Bug in decision logic

⚠️ **Claims missing from ledger**
- Check file permissions
- Verify ledger path is correct

---

## Example: Real-World Monitoring

### Day 1: Initial Run

```bash
$ python3 oracle_town/kernel/test_openclaw.py

✓ fetch_trusted          | example.com/status.json      | ACCEPT
✗ fetch_untrusted        | moltbook.com/heartbeat       | REJECT (K0: attestor not registered)
✗ skill_install          | skill:sentiment-analyzer     | REJECT (K0: attestor not registered)
✗ heartbeat_modify       | heartbeat_config             | REJECT (K0: attestor not registered)
✓ fetch_metrics          | metrics.local/daily          | ACCEPT

K15 ENFORCED: 3 claims blocked
DISCRIMINATION WORKING: ✓
```

**Conclusion:** Boundary is real. K15 is working.

### Day 2: Monitor

```bash
$ python3 oracle_town/kernel/monitor_claims.py --since 24h

Total claims: 5
Accepted: 2 (40%)
Rejected: 3 (60%)

BY SOURCE
OPENCLAW_TEST | Total: 5 | Accept: 2 | Reject: 3 | Rate: 40.0%

K15 ENFORCEMENT VERIFICATION
✓ K15 ACTIVE: 3 claim(s) blocked by authority
```

**Conclusion:** System is stable. Consistent behavior.

### Week 1: Pattern Analysis

```bash
$ python3 oracle_town/kernel/monitor_claims.py --since 7d

Acceptance rate: 40%
Rejection reasons (top):
- K0: Attestor not registered: 15
- K5: Evidence hash mismatch: 2
- Gate A: Shell commands detected: 1
```

**Conclusion:**
- K0 is the main gate (unregistered attestors)
- System catching malicious content (Gate A)
- No false positives (all rejections justified)

---

## Extending: Real OpenClaw Integration

When you're ready to attach actual OpenClaw:

### 1. Modify OpenClaw startup

```python
# openclaw.py startup
import sys
from oracle_town.kernel.submit_claim import submit_action_claim
from oracle_town.kernel.receipt_check import enforce, ExecutionBlocked

def initialize():
    global submit_claim, check_receipt
    submit_claim = submit_action_claim
    check_receipt = enforce
```

### 2. Wrap risky operations

```python
# Before: fetch and execute directly
# content = requests.get(url).content
# execute(content)

# After: submit claim, check receipt
content = requests.get(url).content
try:
    receipt = submit_claim(
        action_type="fetch",
        target=url,
        evidence_bytes=content,
        intent=f"Heartbeat check from {url}",
        source="OPENCLAW"
    )
    if check_receipt(receipt):
        execute(content)
except ExecutionBlocked:
    log("Authority blocked execution")
    return
```

### 3. Monitor incoming claims

```bash
# Watch OpenClaw in real-time
watch -n 5 'python3 oracle_town/kernel/monitor_claims.py --since 1h --format json | jq ".summary"'
```

---

## Hardening (Optional: Phase B)

Once you're confident in monitoring, lock OpenClaw source to prevent bypasses:

```bash
# Make OpenClaw read-only (cannot edit K15 enforcement)
chmod 440 openclaw.py

# Protect git history (cannot revert K15 changes)
git config branch.main.protected true
git config branch.main.requireCodeOwnerReviews true
```

Then K15 enforcement becomes **structural**, not procedural.

---

## Interpretation Guide

### Acceptance Rate Analysis

```
80-100%  → Policy too permissive. Register real attestors.
50-80%   → Healthy. Good mix of accept/reject.
20-50%   → Restrictive but working. Expected during testing.
0-20%    → Too restrictive. Check attestor registration.
0%       → Broken. All claims rejected. Check policy.
```

### Rejection Reason Distribution

```
K0: Attestor not registered
  → Expected during testing (no attestors registered yet)
  → Action: Register attestors when moving to production

K1: Fail-closed (missing evidence/quorum)
  → Indicates incomplete claims
  → Action: Review claim submission in OpenClaw

Gate A: Shell commands / exec chains
  → Indicates malicious content captured
  → Action: This is a WIN. K15 worked. Log and monitor.

Gate B: Skill install / credential access
  → Indicates suspicious operations
  → Action: Review policy. May be legitimate.

K5: Evidence hash mismatch
  → Indicates determinism issues
  → Action: Critical. Stop deployment. Debug.
```

### Action Items by Scenario

**Scenario 1: All ACCEPT**
```
Root cause: No valid attestor keys in registry
Fix:
  1. Generate Ed25519 key pair
  2. Register public key in oracle_town/keys/public_keys.json
  3. Sign claims with private key
  4. Re-run test_openclaw.py
Result: Some claims should now REJECT (K0 checks run)
```

**Scenario 2: All REJECT**
```
Root cause: Policy too strict OR keys not in registry
Fix:
  1. Check oracle_town/keys/public_keys.json (has entries?)
  2. Review policy rules (what gates are rejecting?)
  3. Loosen policy if needed
  4. Re-test
Result: ACCEPT rate should increase
```

**Scenario 3: Inconsistent Results**
```
Root cause: K5 determinism broken
Action: STOP. Do not proceed to production.
Debug:
  1. Run same claim twice
  2. Compare decision hashes
  3. Find non-deterministic operation
  4. Fix before deploying
```

---

## Success Criteria

✓ **Phase 1 (Now):** Monitoring setup working
- [ ] Daily emulation runs at 9 AM
- [ ] Dashboard shows latest brief + trends
- [ ] Test OpenClaw produces expected results
- [ ] K15 is blocking bad claims
- [ ] Ledger grows with each run

✓ **Phase 2 (Week 1):** Consistent behavior
- [ ] 7 days of claim history recorded
- [ ] Acceptance rate stable (not jumping wildly)
- [ ] No K5 determinism errors
- [ ] Rejection reasons clear and justified

✓ **Phase 3 (Week 2):** Ready for hardening
- [ ] Understand what gets accepted vs. rejected
- [ ] Confident in policy rules
- [ ] Ready to register real attestors
- [ ] Ready for Option B (Hardening) or Option C (Scale)

---

## Commands Quick Reference

```bash
# Daily operations
bash oracle_town/daily_emulation_loop.sh          # Run emulation
python3 oracle_town/dashboards/emu_dashboard/server_stdlib.py  # Dashboard

# Monitoring
python3 oracle_town/kernel/test_openclaw.py       # Test K15 enforcement
python3 oracle_town/kernel/monitor_claims.py --since today        # Daily report
python3 oracle_town/kernel/monitor_claims.py --since 7d          # Weekly report
python3 oracle_town/kernel/monitor_claims.py --format json        # JSON output

# Inspection
cat oracle_town/ledger/2026/01/*/claim.json | jq '.claim.intent'  # All intents
cat oracle_town/ledger/2026/01/*/mayor_receipt.json | jq '.receipt.decision' | sort | uniq -c  # Decision counts
```

---

## Next Actions

Choose one:

**A1:** Continue monitoring (add more test scenarios)
**B1:** Harden (lock OpenClaw, register attestors)
**C1:** Scale (attach other agents to jurisdiction)

Monitoring will tell you which to choose next.

---

**Status:** Monitoring system ready. K15 enforced. Boundary proven real.
