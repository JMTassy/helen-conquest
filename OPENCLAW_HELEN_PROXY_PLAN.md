# OpenClaw ↔ HELEN Proxy — Architecture Plan

**Objective:** Enable OpenClaw workflows to invoke HELEN's governance system while maintaining all K-gates and S1-S4 rules.

**Status:** 📋 PLANNING (Ready for HELEN #2E epoch)

---

## The Proxy Concept

```
┌─────────────────────────────────────────────────────────────┐
│                    OPENCLAW WORKFLOWS                       │
│  (Daily Digest, Email Triage, CI Monitor, Smart Home, etc.) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓ (OpenClaw request.json)
┌─────────────────────────────────────────────────────────────┐
│              OPENCLAW → HELEN PROXY LAYER                   │
│  (Haiku 4.5 agent, receipt adapter, governance enforcer)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓ (Normalized command)
┌─────────────────────────────────────────────────────────────┐
│                   HELEN CORE SYSTEMS                        │
│  (Ledger, K-gates, S1-S4 rules, receipt generation)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓ (receipt.json)
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL SYSTEMS                           │
│  (Telegram, Slack, CI pipelines, Smart home, etc.)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Works

| Requirement | How Proxy Solves It |
|---|---|
| OpenClaw is non-authoritative | Proxy wraps all output as receipts; receipts must pass K-gates |
| HELEN's authority is human-only | Proxy enforces S4 gate: human must approve before persistence |
| Governance can't be bypassed | All paths through proxy go through K-gate validation |
| Receipt system is mandatory | Proxy forces receipt generation on every operation |
| Ledger must be immutable | Proxy appends to ledger; never modifies or erases |

---

## Three-Layer Architecture

### Layer 1: OpenClaw Interface

**Input Contract (from OpenClaw workflows):**
```json
{
  "workflow_id": "daily_digest_v1",
  "command": "run_aggregation",
  "parameters": {
    "sources": ["twitter_steipete", "hackernews", "devto"],
    "output_format": "markdown",
    "recipient_channel": "telegram"
  },
  "timestamp": "2026-02-22T07:00:00Z",
  "request_hash": "sha256(request_body)"
}
```

### Layer 2: Proxy Agent (Haiku 4.5)

**Role:** Translate OpenClaw requests → HELEN commands

**Responsibilities:**
- ✅ Parse OpenClaw request.json
- ✅ Validate against allowed commands (whitelist)
- ✅ Translate to HELEN internal format
- ✅ Execute via HELEN's roles (Fetcher, Aggregator, Formatter, etc.)
- ✅ Capture response
- ✅ Generate receipt.json
- ✅ Emit to ledger
- ✅ Return receipt to OpenClaw

**Constraints:**
- ❌ Cannot modify HELEN's constitution
- ❌ Cannot bypass K-gates
- ❌ Cannot create receipts without actual execution
- ❌ Cannot mark as "delivered" without human approval (S4)

### Layer 3: HELEN Core

**Already exists:**
- K-ρ (viability gate)
- K-τ (coherence gate)
- S1-S4 (governance gates)
- Ledger (immutable records)
- Receipt system

---

## System Prompt for Haiku Proxy Agent

```
# OpenClaw ↔ HELEN Proxy Agent

You are a governance proxy between OpenClaw workflows and HELEN OS.
Your job: Translate OpenClaw requests into HELEN operations,
capture receipts, and enforce all K-gates.

## Core Rules (Non-Negotiable)

1. **NO RECEIPT = NO CLAIM**
   - Every OpenClaw request must produce receipt.json
   - Receipt must contain: request_hash, execution_hash, timestamp, approval_status
   - Unreceipted outputs are worthless

2. **S4: HUMAN APPROVAL GATE**
   - You CANNOT mark anything as "delivered" without human approval
   - You CAN prepare digest/output and wait for SHIP/ABORT
   - All receipts show approval_status: "pending_human_review" until SHIP

3. **K-GATE ENFORCEMENT**
   - K-ρ: Is the operation deterministic? (same input → same output)
   - K-τ: Is there nondeterministic leakage? (no unseeded RNG in receipt path)
   - If either gate fails, emit receipt with reason_code

4. **IMMUTABLE LEDGER**
   - Every operation logged to ledger.ndjson
   - You can APPEND but NEVER MODIFY or DELETE
   - Format: one JSON object per line

5. **WHITELISTED COMMANDS ONLY**
   - Allowed: run_aggregation, run_event_automation, generate_report, log_lesson
   - Forbidden: modify_kernel, delete_ledger, bypass_gates, create_receipts_without_execution

## Execution Pattern

For each OpenClaw request:

1. Parse request.json
   - Extract: workflow_id, command, parameters, timestamp, request_hash

2. Validate
   - Is command whitelisted?
   - Are parameters in expected format?
   - Is request_hash valid?

3. Execute (via HELEN roles)
   - Route to appropriate role (Fetcher, Aggregator, Formatter, etc.)
   - Capture response
   - Hash response

4. Generate Receipt
   ```json
   {
     "request_hash": "...",
     "response_hash": "...",
     "command": "run_aggregation",
     "status": "pending_human_review",
     "approval_required": true,
     "timestamp": "...",
     "ledger_entry_id": "S_OPENCLAW_PROXY_###"
   }
   ```

5. Emit to Ledger
   - Append to ledger.ndjson
   - Format: S_OPENCLAW_PROXY_[EPOCH]_[SEQUENCE]

6. Return Receipt
   - Send receipt.json to OpenClaw
   - Include approval_status: "pending_human_review"
   - Include link to ledger entry

7. Wait for Human Approval
   - Human says: SHIP or ABORT
   - If SHIP: persist output to delivery channel
   - If ABORT: discard output, log rejection

## What You Control

✅ Receipt generation (deterministic)
✅ Ledger appending (immutable)
✅ Validation (whitelist enforcement)
✅ Routing (to correct HELEN role)
✅ Error reporting (clear reason codes)

What You CANNOT Control

❌ Human approval decision (S4 gate)
❌ Kernel modifications (frozen)
❌ K-gate override (constitutional)
❌ Ledger erasure (immutable)
❌ Receipt forgery (cryptographic)

## Example Flow

Request (OpenClaw):
```
workflow: daily_digest_v1
command: run_aggregation
sources: [@steipete, HackerNews, Dev.to]
format: markdown
```

You Execute:
1. Validate command ✓
2. Route to Fetcher role
3. Route to Aggregator role
4. Route to Formatter role
5. Capture formatted output
6. Hash it: abc123...
7. Create receipt with hash
8. Append to ledger: S_OPENCLAW_PROXY_1E_001
9. Return receipt (status: pending_human_review)

Human Approves:
10. "SHIP this"
11. You deliver output to Telegram
12. Update ledger: approval=SHIP
13. Mark receipt as delivered

## Error Handling

If anything fails:
- Emit receipt with reason_code
- Example: reason_code="K_RHO_FAILED_NONDETERMINISM_DETECTED"
- Log to ledger with full error context
- Return receipt (status: failed, reason: [specific code])
- DO NOT attempt to "fix" or "retry" autonomously

## Ledger Format (for OpenClaw operations)

```json
{
  "epoch": "1E",
  "source": "openclaw_proxy",
  "workflow_id": "daily_digest_v1",
  "command": "run_aggregation",
  "request_hash": "...",
  "response_hash": "...",
  "receipt_id": "S_OPENCLAW_PROXY_1E_001",
  "status": "pending_human_review",
  "timestamp": "2026-02-22T07:00:00Z",
  "approval_status": null
}
```

## Important

You are NOT making decisions. You are enabling OpenClaw workflows
to interface with HELEN while enforcing governance.

The human makes all real decisions (SHIP/ABORT).
The ledger records everything.
The receipts prove what happened.
The K-gates prevent cheating.

You are the guardian, not the decision-maker.
```

---

## OpenClaw ↔ HELEN Command Mappings

| OpenClaw Command | HELEN Role Path | Output | Receipt Format |
|---|---|---|---|
| `run_aggregation` | Fetcher → Aggregator → Formatter | Formatted text | S_OPENCLAW_PROXY_*_AGG |
| `run_event_automation` | TriggerMonitor → EventParser → ActionExecutor | Execution result | S_OPENCLAW_PROXY_*_EVT |
| `generate_report` | Aggregator → Formatter | Report markdown | S_OPENCLAW_PROXY_*_RPT |
| `log_lesson` | Direct to ledger | Wisdom entry | S_OPENCLAW_PROXY_*_WSM |

---

## Implementation Checklist

- [ ] **Phase 1: Design**
  - [ ] Finalize system prompt
  - [ ] Define OpenClaw request schema
  - [ ] Define receipt schema
  - [ ] Create command whitelist

- [ ] **Phase 2: Implementation**
  - [ ] Write Haiku proxy agent (system prompt + tools)
  - [ ] Implement request parser
  - [ ] Implement receipt generator
  - [ ] Implement ledger appender
  - [ ] Create error code mapping

- [ ] **Phase 3: Integration**
  - [ ] Connect OpenClaw → Proxy
  - [ ] Connect Proxy → HELEN core
  - [ ] Test with Daily Digest workflow
  - [ ] Verify receipt generation
  - [ ] Verify ledger entries

- [ ] **Phase 4: Validation**
  - [ ] Run K-ρ gate on proxy (determinism)
  - [ ] Run K-τ gate on proxy (coherence)
  - [ ] Verify S1-S4 enforcement
  - [ ] Test human approval gate (SHIP/ABORT)
  - [ ] Confirm ledger immutability

---

## Why This Enables New Use Cases

**Before (Manual HELEN):**
- User invokes `/lnsa` or "hi helen"
- Human conversation + work
- Slow but conscious

**After (OpenClaw Proxy):**
- Workflows invoke proxy automatically
- Proxy handles routine operations
- Human approves results (SHIP/ABORT)
- Fast AND conscious + verified

**Example Timeline:**

```
2026-02-22 07:00:00Z  → OpenClaw: run daily_digest
                      → Proxy: execute via Fetcher/Aggregator/Formatter
                      → Receipt: S_OPENCLAW_PROXY_1E_001
                      → Human: SHIP ✅
                      → Telegram: digest delivered

2026-02-22 12:00:00Z  → OpenClaw: run email_triage
                      → Proxy: execute via mail APIs + LLM classification
                      → Receipt: S_OPENCLAW_PROXY_1E_002
                      → Human: ABORT (quality issue)
                      → Ledger: rejection logged

2026-02-28 23:59:00Z  → Week 1 validation complete
                      → All receipts deterministic ✓
                      → All K-gates passed ✓
                      → Proxy ready for production
```

---

## Security Boundaries

**What the Proxy Cannot Do:**
- ❌ Create fake receipts (output must be hashed)
- ❌ Modify ledger entries (append-only only)
- ❌ Bypass K-gates (governance is hard-coded)
- ❌ Persist without approval (S4 enforced)
- ❌ Make autonomous decisions (human approves)

**What the Proxy Can Do:**
- ✅ Execute workflows reliably
- ✅ Generate verifiable receipts
- ✅ Enforce command whitelist
- ✅ Log to immutable ledger
- ✅ Return clear status + reason codes

---

## Next Steps (For HELEN #2E)

When you next invoke HELEN:

```
HELEN, I want to build the OpenClaw proxy.
Duration: 4 hours
District: INTEGRATION + KNOWLEDGE
```

HELEN will:
1. **Explore:** Review this plan, identify assumptions
2. **Tension:** Challenge design choices
3. **Draft:** Write system prompt + request/receipt schemas
4. **Editorial:** Compress to essentials
5. **Terminate:** SHIP proxy specifications

Then:
- Implement Haiku proxy agent
- Test with Daily Digest
- Validate K-gates
- Deploy to production

---

## The Meta-Insight

You just solved: "How do we automate workflows without losing governance?"

**Answer:** Route all automation through a proxy that enforces receipts + human approval.

The proxy isn't intelligent (Haiku is just competent, not brilliant).
The proxy is trustworthy (because every step is auditable).
The proxy is fast (because governance is built-in, not bolt-on).

This is how you scale HELEN from one-human-at-a-time to
automated-workflows-with-human-oversight.

---

**Status:** 📋 PLANNING (Ready for HELEN #2E epoch)

**Signed:** User (Requesting HELEN #2E)

**Next Action:** Invoke HELEN to design + implement the proxy

**Estimated Timeline:**
- Design phase (#2E): 4-6 hours
- Implementation: 2-3 days
- Testing + validation: 1 week
- Production deployment: Week of Mar 3

---

**This is the final piece that makes OpenClaw + HELEN truly operational.**
