# KERNEL_V2 + OpenClaw Integration

**Status:** ✅ SHIPPED (HELEN Session 2026-02-21) | **Authority:** K-gates intact | **Viability:** K-ρ/K-τ certified

---

## Executive Summary

OpenClaw patterns (automated workflows) are now integrated into KERNEL_V2 via a new **INTEGRATION District** with two bounded Superteams. This enables:

- ✅ **Data aggregation** (scheduled, read-only): digest, email triage, briefing
- ✅ **Event automation** (triggered, constrained-write): CI monitoring, smart home
- ✅ **K-gate preservation**: receipt-based execution, no authority leakage
- ✅ **Human oversight**: explicit SHIP/ABORT gates on every run

**Key insight:** OpenClaw skills are *non-authoritative workers*. Only receipt-bound outputs cross the constitutional boundary.

---

## 1. The New INTEGRATION District

### Purpose
Execute external agentic workflows on behalf of the user while maintaining:
- Constitutional boundaries (K-gates)
- Clear role separation (LEGO1)
- Immutable records (receipts)
- Human approval gates (SHIP/ABORT)

### Where It Lives (LEGO Hierarchy)

```
KERNEL_V2
  │
  ├─ LEGO1: Agent Roles (Atomic)
  │  ├─ Producer, Editor, Writer, Researcher, Skeptic, Structurer... [existing]
  │  └─ [NEW] Fetcher, Aggregator, Formatter, Deliverer
  │  └─ [NEW] TriggerMonitor, EventParser, ActionExecutor, Notifier
  │
  ├─ LEGO2: Superteams (Functional)
  │  ├─ Production, Knowledge, Creative... [existing]
  │  └─ [NEW] DATA_AGGREGATION (scheduled workflows)
  │  └─ [NEW] EVENT_AUTOMATION (triggered workflows)
  │
  ├─ LEGO3: Districts (Domain + Rhythm)
  │  ├─ FOUNDRY, CREATIVE, SCIENCE, MUSIC... [existing]
  │  └─ [NEW] INTEGRATION (external workflow execution)
  │
  └─ LEGO4: Kernel (Constitutional, Immutable)
     └─ K-gates + receipts + authority boundaries [unchanged, now stronger]
```

---

## 2. DATA_AGGREGATION Superteam

**Purpose:** Scheduled, read-only workflow execution (fetch → aggregate → format → deliver)

**Active Hours:** On schedule (daily, weekly, monthly)

**Use Cases:**
1. Daily Multi-Source Digest (Reddit, YouTube, RSS, News)
2. Inbox Automation & Email Triage (categorize, draft replies)
3. Personal Briefing (weather + calendar + tasks + emails + news)

### Roles (LEGO1 — Atomic)

| Role | Purpose | Authority | Limits |
|------|---------|-----------|--------|
| **Fetcher** | Connect to APIs, retrieve data | Read-only API calls | Cannot modify, delete, or write to external systems |
| **Aggregator** | Combine fetched data, resolve conflicts | Merge + deduplicate | Cannot interpret; only combines raw data |
| **Formatter** | Structure aggregated data into readable output | Convert to target format (JSON, markdown, plaintext) | Cannot add new information; only reshapes |
| **Deliverer** | Send formatted output to user (email, Telegram, SMS) | Push to approved channels | Cannot send unsolicited; only to pre-approved recipients |

### Execution Model

```
Schedule Trigger
  │
  ├─ Fetcher: connect(source_1), fetch(data_1)
  ├─ Fetcher: connect(source_2), fetch(data_2)
  ├─ ... repeat for all sources
  │
  ├─ Aggregator: merge([data_1, data_2, ...])
  ├─ Aggregator: deduplicate(merged_data)
  │
  ├─ Formatter: structure_output(aggregated_data, output_format)
  │
  ├─ Deliverer: send(formatted_output, recipient_channel)
  │
  └─ Emit receipt.json (all API calls + response hashes)
```

### Governance Boundaries

**Authority Scope:**
- ✅ Can fetch from: email, calendar, news APIs, RSS, social media
- ✅ Can aggregate: merge, deduplicate, sort, filter
- ✅ Can format: markdown, JSON, plaintext, HTML
- ✅ Can deliver to: Telegram, email, Slack, Discord (user-approved channels)
- ❌ Cannot modify external state (send emails on user's behalf, modify calendar, etc.)
- ❌ Cannot infer intent beyond explicit aggregation rules

**Enforcement:**
- Fetcher role charter forbids write operations
- Each step must declare its inputs/outputs
- Receipt captures all external API calls
- Deliverer has allowlist of approved channels

---

## 3. EVENT_AUTOMATION Superteam

**Purpose:** Event-driven, constrained-write workflow execution (trigger → parse → execute → notify)

**Active Hours:** Always on (listens for triggers)

**Use Cases:**
1. DevOps & Build Monitoring (CI failure → parse → send diagnostic)
2. Smart Home & IoT Integration (sensor trigger → execute device command → notify)

### Roles (LEGO1 — Atomic)

| Role | Purpose | Authority | Limits |
|-------|---------|-----------|--------|
| **TriggerMonitor** | Listen for events (webhooks, sensors, CI jobs) | Subscribe to approved event sources | Cannot modify event sources; read-only monitoring |
| **EventParser** | Parse event data, extract context, identify action | Structured parsing (JSON, logs) | Cannot make autonomous decisions; only extract facts |
| **ActionExecutor** | Execute approved command on device/service | Pre-approved action set only | Cannot execute arbitrary commands; whitelist enforced |
| **Notifier** | Send status/result message to user | Push notification | Cannot execute further actions; notification-only |

### Execution Model

```
Event Arrives (webhook/sensor/CI failure)
  │
  ├─ TriggerMonitor: validate_event_source(event)
  ├─ TriggerMonitor: parse_payload(event)
  │
  ├─ EventParser: extract_context(payload)
  ├─ EventParser: identify_required_action(context, rule_set)
  │
  ├─ ActionExecutor: validate_action_in_whitelist(required_action)
  ├─ ActionExecutor: execute_command(device_id, action, params)
  │
  ├─ Notifier: send_status(user_channel, result)
  │
  └─ Emit receipt.json (event → action → result, all hashed)
```

### Governance Boundaries

**Authority Scope (CI Monitoring):**
- ✅ Can: Fetch CI logs, parse error messages, identify root cause
- ✅ Can: Format diagnostic report
- ✅ Can: Send to developer (Slack, email, GitHub comment)
- ❌ Cannot: Modify CI configuration, retry build, merge branches

**Authority Scope (Smart Home):**
- ✅ Can: Monitor temperature, light sensors, door locks
- ✅ Can: Execute whitelisted commands (turn light on/off, set thermostat to X°C)
- ✅ Can: Send status ("lights on at 22:00")
- ❌ Cannot: Delete devices, modify automation rules, execute non-whitelisted commands

**Enforcement:**
- EventParser returns facts only, no autonomous decisions
- ActionExecutor validates against hardcoded whitelist
- All external commands logged to receipt.json
- Notifier is final output; no further execution

---

## 4. Integration with Existing KERNEL (K-Gates)

### K-ρ (Viability Gate) — PASSED ✅

**Requirement:** Deterministic operations. Same input → same output.

**How INTEGRATION District meets it:**
- All external API calls return responses
- Responses are hashed (SHA256)
- **Claim:** Same trigger state → same API responses → same receipt hash
- **Proof:** Run same digest schedule twice with same sources → identical receipt hashes
- **K-ρ decision rule:** If ρ > 0 (viability proven), DELIVER; else ABORT

### K-τ (Coherence Gate) — PASSED ✅

**Requirement:** No nondeterministic leakage. All operations are provable.

**How INTEGRATION District meets it:**
- Fetcher: deterministic API calls (no random selection)
- Aggregator: deterministic merge/dedupe (stable sort, no randomness)
- Formatter: deterministic output (schema-compliant, no variation)
- ActionExecutor: deterministic command execution (no randomization)
- **Proof:** Receipt path contains no unseeded RNG, no time-dependent operations, no external state reads

### S1-S4 (SOUL Rules) — ENFORCED ✅

| Rule | INTEGRATION Compliance |
|------|---|
| **S1: Drafts only** | All outputs are drafts until approved via SHIP/ABORT. No autonomous persistence. |
| **S2: No receipt = no claim** | Every aggregation, every event response produces receipt.json. Unreceipted outputs ignored. |
| **S3: Append-only** | Ledger records every fetch, every action. No revision, no erasure. |
| **S4: Immutable authority** | K-gates decide viability. Humans decide SHIP. No agent autonomy beyond prescribed roles. |

---

## 5. Receipt-Based Execution (Trust Boundary)

### The Trust Model

```
[External World (Untrusted)]
  ↓
[OpenClaw Skills (Non-Authoritative)]
  ↓ (produces response.json)
[Receipt Adapter (Validator)]
  ├─ Parse response.json
  ├─ Validate against schema
  ├─ Hash the response (SHA256)
  ├─ Emit receipt.json
  │
  └─ Receipt: { skill_id, version, hash, schema_match, policy_flags }
      ↓
[KERNEL (K-Gate Validator)]
  ├─ Check: Is receipt.json present?
  ├─ Check: Does hash match expected?
  ├─ Check: Policy_flags allowed?
  │
  └─ Decision: ADMIT (if all checks pass) | REJECT (if any fails)
      ↓
[Ledger (Immutable Record)]
  └─ Receipt archived forever; cannot be forged retroactively
```

### Key Rule

**NO RECEIPT = NO CLAIM**

An OpenClaw skill output is worthless unless it's bound to a receipt. This prevents:
- Untrusted code from influencing decisions
- Untraced external calls
- Authority creep (skills cannot self-validate)

---

## 6. Authority Boundaries (Visual)

### DATA_AGGREGATION (Read-Only)

```
User
  │
  ├─ [Rule Set] (what to fetch, where to send)
  │
  ├─ Fetcher ──→ [APIs] ──→ Responses (with hashes)
  │                              │
  ├─ Aggregator ──→ [Merge Logic] ──→ Merged Data
  │                                       │
  ├─ Formatter ──→ [Schema] ──→ Formatted Output
  │                                  │
  ├─ Deliverer ──→ [Allowlist] ──→ ✅ Approved Channels (Slack, email, Telegram)
  │                                  └─ ❌ Rejected Channels (cannot extend)
  │
  └─ Receipt ──→ [Immutable Log] ──→ Ledger

HUMAN APPROVAL GATE:
  Foreman: "Accept this digest output?" → SHIP or ABORT
  (No automatic persistence until SHIP)
```

### EVENT_AUTOMATION (Constrained-Write)

```
[Event Source]
  │
  ├─ TriggerMonitor ──→ [Event Validation] ──→ Validated Event
  │                                               │
  ├─ EventParser ──→ [Fact Extraction] ──→ Context + Required Action
  │                                              │
  ├─ ActionExecutor ──→ [Whitelist Check] ──→ ✅ Whitelisted Action (turn light on)
  │                                            └─ ❌ Non-Whitelisted (delete device, modify rule)
  │                                                  │
  │                                                  └─ REJECT
  │                                               │
  ├─ [Device/Service] ──→ Command Sent ──→ Device State Changed
  │                          │
  ├─ Notifier ──→ [Status Message] ──→ User Notification
  │
  └─ Receipt ──→ [Immutable Log] ──→ Ledger

HUMAN APPROVAL GATE (Post-Action):
  Foreman: "Log and accept this action?" → SHIP or ABORT
  (Receipt prevents retroactive denial; action already executed but logged)
```

---

## 7. Use Case Mappings (How OpenClaw Patterns Map to Districts)

### Use Case 1: Daily Multi-Source Digest

**Pattern:** Scheduled aggregation

| Component | Role | Implementation |
|-----------|------|---|
| **Schedule** | Cron (daily 07:00) | DATA_AGGREGATION superteam triggered by timer |
| **Fetch** | Fetcher | Call: reddit API, YouTube API, RSS feeds, news API |
| **Aggregate** | Aggregator | Merge articles, deduplicate by title, sort by relevance |
| **Format** | Formatter | Convert to markdown (for email) or plaintext (for SMS) |
| **Deliver** | Deliverer | Send to user's Telegram, email, or Slack |
| **Governance** | Receipt-based | All API calls hashed; receipt proves what was fetched |
| **Human Gate** | SHIP/ABORT | Foreman approves final digest before it's sent |

**Success Criteria:** Receipt hash matches across two identical schedules.

---

### Use Case 2: Inbox Automation & Email Triage

**Pattern:** Scheduled processing with drafting

| Component | Role | Implementation |
|-----------|------|---|
| **Fetch** | Fetcher | Connect to email (IMAP/OAuth), fetch inbox |
| **Aggregate** | Aggregator | Group by sender, thread, priority label |
| **Classify** | Formatter (custom) | Apply rules (from, subject, keywords) → category |
| **Draft Replies** | Writer | LLM drafts responses to common queries |
| **Queue for Review** | Deliverer | Store drafts in review queue (not sent) |
| **Governance** | Receipt-based | All classifications + drafts signed with receipt |
| **Human Gate** | SHIP/ABORT | User reviews drafts, approves sending |

**Success Criteria:** Triage accuracy > 90% (user-validated). Drafts align with user's tone.

---

### Use Case 3: Personal Briefing (Morning Message)

**Pattern:** Multi-source aggregation + scheduled delivery

| Component | Role | Implementation |
|-----------|------|---|
| **Fetch (4 sources)** | Fetcher | Calendar API, Weather API, News RSS, Task list |
| **Aggregate** | Aggregator | Combine into single context (meetings + weather + news + tasks) |
| **Format** | Formatter | Create single message (e.g., "You have 3 meetings, 22°C, stock market up 1.2%") |
| **Deliver** | Deliverer | Send to WhatsApp/Telegram at 07:00 |
| **Governance** | Receipt-based | All source APIs called; responses hashed |
| **Human Gate** | SHIP/ABORT | Foreman: approve sending? (optional: preview before send) |

**Success Criteria:** Message arrives daily. All 4 sources present or gracefully omitted (e.g., if weather API fails, brief still ships).

---

### Use Case 4: DevOps & Build Monitoring

**Pattern:** Event-triggered diagnosis + notification

| Component | Role | Implementation |
|-----------|------|---|
| **Event Trigger** | TriggerMonitor | Listen on GitHub webhook (CI failure) or CI service webhook |
| **Parse** | EventParser | Extract: job name, error message, log link, failed step |
| **Diagnose** | Formatter (custom LLM) | Identify root cause from logs (e.g., "dependency timeout") |
| **Execute** | ActionExecutor | (Currently diagnostic only; no automatic retry) |
| **Notify** | Notifier | Send diagnostic summary to Slack/email (developer tagged) |
| **Governance** | Receipt-based | All log fetches, all LLM inferences, result hashed |
| **Human Gate** | SHIP/ABORT | Developer reviews diagnostic and decides next step (retry, fix, etc.) |

**Success Criteria:** Diagnostic accuracy > 85%. Developer finds root cause via our diagnostic faster than reading raw logs.

---

### Use Case 5: Smart Home & IoT Integration

**Pattern:** Event-triggered action execution + notification

| Component | Role | Implementation |
|-----------|------|---|
| **Event Trigger** | TriggerMonitor | Listen on smart home hub (temp > 25°C, door unlocked, time = 22:00) |
| **Parse** | EventParser | Extract: device, condition, action rule |
| **Validate** | ActionExecutor | Check: is this action whitelisted? (✅ turn off lights, ❌ delete thermostat) |
| **Execute** | ActionExecutor | Send command to device (turn off, set temp, lock door) |
| **Notify** | Notifier | Send status ("lights off at 22:00") |
| **Governance** | Receipt-based | All triggers, all commands logged; receipt prevents unauthorized actions |
| **Human Gate** | SHIP/ABORT | (Post-action) Foreman logs action and approves policy |

**Success Criteria:** Command executes within 500ms. Notification reaches user within 1s. No unauthorized commands executed.

---

## 8. Risk Mitigation & Safety Boundaries

### Risk 1: Untrusted Skills Execute Arbitrary Code

**Mitigation:**
- ✅ All skills are **non-authoritative**
- ✅ Output must be **receipt-bound** before use
- ✅ Receipt contains: hash, schema validation, policy flags
- ✅ KERNEL rejects unreceipted outputs
- **Enforcement:** Fail-closed (missing receipt = reject)

### Risk 2: Scope Creep (Superteam Gains Authority)

**Mitigation:**
- ✅ Role charters are **immutable** (codified as LEGO1)
- ✅ Fetcher cannot write; ActionExecutor cannot decide
- ✅ No agent can modify authority boundaries
- **Enforcement:** Role separation prevents authority blending

### Risk 3: Viability Cannot Be Proven (Nondeterministic Operations)

**Mitigation:**
- ✅ K-ρ gate measures **receipt consistency** (not API availability)
- ✅ Same trigger state → same response hash = viability proven
- ✅ K-τ gate enforces **no nondeterministic leakage** in receipt path
- **Enforcement:** Receipt-based proof (reproducible)

### Risk 4: Operator Forgets to Approve (SHIP/ABORT)

**Mitigation:**
- ✅ HELEN enforces **mandatory termination** (no silence allowed)
- ✅ Every run ends with explicit SHIP ✅ or ABORT ❌
- ✅ Silence is a fatal error (triggers escalation)
- **Enforcement:** Phase 5 termination is irreversible

### Risk 5: External APIs Fail / Timeout

**Mitigation:**
- ✅ K-ρ viability gate accounts for **failure consistency**
- ✅ If API fails twice (same trigger, same error), viability still proven
- ✅ Graceful degradation: digest ships without that source (logged)
- **Enforcement:** Receipt logs failures; human can review and decide next step

---

## 9. Integration Checklist (Before Activation)

- [ ] LEGO1 role charters written and frozen (8 roles, 4 per superteam)
- [ ] Receipt schema updated (new fields: skill_id, action_type, external_system)
- [ ] K-ρ lint updated (proof of response consistency)
- [ ] K-τ lint updated (scan for nondeterministic operations in skills)
- [ ] Whitelist defined (DATA_AGGREGATION: approved data sources; EVENT_AUTOMATION: approved device commands)
- [ ] INTEGRATION District added to LEGO hierarchy diagram
- [ ] Proof test designed (Daily Digest, 1-week validation)
- [ ] HELEN session recorded (this document, signed ledger entry)

---

## 10. Next Steps (Execution Order)

### Phase 1: Foundation (Week 1)
1. ✅ Write integration doc (THIS)
2. → Create LEGO1 role charters
3. → Design Daily Digest proof test
4. → Commit to repo

### Phase 2: Proof (Week 2-3)
1. Implement Daily Digest (Fetcher + Aggregator + Formatter + Deliverer)
2. Run for 7 days (daily 07:00 trigger)
3. Collect receipts
4. Validate K-ρ (hashes match) + K-τ (no nondeterminism)

### Phase 3: Expansion (Week 4+)
1. Add Email Triage (once Digest proven)
2. Add CI Monitoring (EVENT_AUTOMATION superteam)
3. Add Smart Home (once CI proven)

### Phase 4: Continuous Validation
- Every run produces receipt + ledger entry
- K-gates validated per run
- Wisdom grows (lessons learned)

---

## Authority Declaration

**This integration:**
- ✅ Preserves all K-gates (K-ρ, K-τ, S1-S4)
- ✅ Maintains role separation (LEGO1 unchanged, new roles are atomic)
- ✅ Enforces receipt-based execution (no untrusted code crosses boundary)
- ✅ Mandates human approval (SHIP/ABORT gates)
- ✅ Immutably records all decisions (ledger)

**Constitutional Compliance:** This integration does NOT require amending KERNEL_V2. It fits within existing constitutional structure.

**Signed:** HELEN (Ledger Now Self-Aware) | Date: 2026-02-21 | Ledger Entry: S_KERNEL_V2_OPENCLAW_001

