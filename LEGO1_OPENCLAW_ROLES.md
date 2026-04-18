# LEGO1: OpenClaw Role Charters

**Purpose:** Atomic role definitions for INTEGRATION District (DATA_AGGREGATION + EVENT_AUTOMATION superteams)

**Format:** Each role is bounded, testable, and immutable. No role can exceed its charter.

---

## DATA_AGGREGATION Superteam

### Role 1: Fetcher

**Atomic Responsibility:**
Connect to external data sources, retrieve raw data, return responses with hashes.

**Purpose:**
Enable read-only access to external APIs without coupling the system to any specific data source.

**Powers:**
- ✅ Call read-only APIs (email IMAP, calendar, weather, news, RSS, social media)
- ✅ Return raw response (unmodified, with HTTP status + body)
- ✅ Cache responses for aggregation phase (no mutation)
- ✅ Emit receipt with hash(response_body)
- ✅ Handle timeouts and API errors gracefully (return error status, not crash)

**Limits:**
- ❌ Cannot modify data on external system (no DELETE, PUT, POST)
- ❌ Cannot select which data to return (return all raw data; Aggregator filters)
- ❌ Cannot retry failed requests autonomously (return failure; let caller decide)
- ❌ Cannot cache credentials in memory (use OAuth tokens only; never store passwords)
- ❌ Cannot authenticate without user-provided credentials/tokens
- ❌ Cannot interpret responses (return raw; no inference)

**Implementation Signature:**
```python
def fetch(source_id: str, credentials: dict) -> FetchResult:
    """
    Fetch data from external source.

    Args:
        source_id: identifier (e.g., "reddit_r_python", "gmail_inbox", "weather_nyc")
        credentials: OAuth tokens or API keys (user-provided)

    Returns:
        FetchResult = {
            "source_id": str,
            "status_code": int,
            "body": str (raw response),
            "error": str or None,
            "timestamp": ISO8601,
            "hash": sha256(body)
        }
    """
```

**Charter Violations (Would Trigger K-τ Lint Failure):**
- ❌ Fetcher tries to cache password locally
- ❌ Fetcher modifies external data (sends email, updates calendar)
- ❌ Fetcher filters responses ("skip posts with 0 upvotes")
- ❌ Fetcher retries failed requests without caller approval

**Success Metric:**
Receipt contains hash of every response. Two identical fetches of same source produce identical hashes.

---

### Role 2: Aggregator

**Atomic Responsibility:**
Combine multiple fetch results, resolve duplicates, merge without adding new information.

**Purpose:**
Consolidate raw data from many sources into a single coherent dataset without losing fidelity.

**Powers:**
- ✅ Merge responses from multiple Fetcher calls
- ✅ Deduplicate by content hash or natural key (e.g., URL, email sender+subject)
- ✅ Sort results by predefined field (date, relevance, priority)
- ✅ Filter by user-defined rules (e.g., "only articles with 100+ upvotes")
- ✅ Group data by source or category (e.g., "emails from work", "Reddit posts")
- ✅ Emit receipt with hash(aggregated_data)

**Limits:**
- ❌ Cannot interpret content (no NLP, no sentiment analysis, no inference)
- ❌ Cannot rewrite data (no field mapping, no data transformation)
- ❌ Cannot add synthetic data (no estimated values, no filled-in blanks)
- ❌ Cannot filter aggressively enough to change meaning (preserve context)
- ❌ Cannot make decisions (e.g., "this article seems important, boost it") — Formatter decides display

**Implementation Signature:**
```python
def aggregate(fetch_results: list[FetchResult], rules: AggregateRules) -> AggregatedData:
    """
    Merge and organize multiple fetch results.

    Args:
        fetch_results: list of FetchResult dicts from Fetcher
        rules: {
            "dedup_by": "url" or "sender_subject",
            "sort_by": "date" or "relevance",
            "filter_rules": [{"field": "upvotes", "min": 100}],
            "group_by": "source" or None
        }

    Returns:
        AggregatedData = {
            "items": list (merged, deduplicated),
            "item_count": int,
            "sources": list (which sources contributed),
            "hash": sha256(items)
        }
    """
```

**Charter Violations:**
- ❌ Aggregator infers sentiment ("these tweets seem negative, exclude them")
- ❌ Aggregator rewrites headlines ("summarize articles")
- ❌ Aggregator creates synthetic summary ("top trends are...")
- ❌ Aggregator makes filtering decisions beyond explicit rules

**Success Metric:**
Aggregating same fetch results twice produces identical hash. Aggregator is deterministic.

---

### Role 3: Formatter

**Atomic Responsibility:**
Convert aggregated data into output format (markdown, JSON, plaintext, HTML).

**Purpose:**
Shape raw data into human-readable or machine-parseable output without changing meaning.

**Powers:**
- ✅ Convert to target format (markdown, JSON, plaintext, HTML, CSV)
- ✅ Apply templating (e.g., "# {title}\n{body}" for markdown)
- ✅ Include metadata (source, timestamp, hash)
- ✅ Truncate long fields to max length (e.g., article body → 500 chars)
- ✅ Order fields consistently (reproducible output)
- ✅ Emit receipt with hash(formatted_output)

**Limits:**
- ❌ Cannot add interpretation ("this is important because...")
- ❌ Cannot rewrite content (no paraphrasing, no summarization)
- ❌ Cannot omit data unless explicitly truncated (must preserve fidelity)
- ❌ Cannot change structure (template is user-provided, not agent-decided)
- ❌ Cannot embed external data (no API calls within formatter)

**Implementation Signature:**
```python
def format_output(aggregated_data: AggregatedData, template: str, format_type: str) -> FormattedOutput:
    """
    Convert aggregated data to output format.

    Args:
        aggregated_data: AggregatedData from Aggregator
        template: string template or schema (e.g., markdown template)
        format_type: "markdown", "json", "plaintext", "html"

    Returns:
        FormattedOutput = {
            "format": format_type,
            "body": str (formatted output),
            "metadata": {
                "source_count": int,
                "item_count": int,
                "timestamp": ISO8601
            },
            "hash": sha256(body)
        }
    """
```

**Charter Violations:**
- ❌ Formatter summarizes articles ("Here's what you need to know...")
- ❌ Formatter interprets trends ("These topics are trending")
- ❌ Formatter creates new sections ("Most Important" vs "Less Important")
- ❌ Formatter paraphrases content

**Success Metric:**
Same aggregated data + same template → identical formatted output (deterministic).

---

### Role 4: Deliverer

**Atomic Responsibility:**
Push formatted output to user-approved channels without modification.

**Purpose:**
Ensure formatted data reaches the user through their preferred communication channels.

**Powers:**
- ✅ Send message to pre-approved channels (Telegram, email, Slack, Discord, SMS)
- ✅ Include delivery metadata (timestamp, channel, status)
- ✅ Emit receipt with hash(delivery_result)
- ✅ Handle delivery failures gracefully (return error, not crash)
- ✅ Queue messages if channel unavailable

**Limits:**
- ❌ Cannot send to unapproved channels (cannot discover new channels, cannot send to arbitrary URLs)
- ❌ Cannot modify formatted output before sending
- ❌ Cannot send to multiple recipients unless explicitly approved per recipient
- ❌ Cannot retry autonomously (return failure; let caller decide)
- ❌ Cannot execute actions in the target channel (no "post reply", no "react with emoji")

**Implementation Signature:**
```python
def deliver(formatted_output: FormattedOutput, channel: str, approved_channels: list) -> DeliveryResult:
    """
    Send formatted output to user-approved channel.

    Args:
        formatted_output: FormattedOutput from Formatter
        channel: "telegram", "email", "slack", "discord", "sms"
        approved_channels: list of approved channel configs (with tokens/addresses)

    Returns:
        DeliveryResult = {
            "channel": str,
            "status": "delivered" or "failed",
            "message_id": str or None,
            "error": str or None,
            "timestamp": ISO8601,
            "hash": sha256(delivery_result)
        }
    """
```

**Charter Violations:**
- ❌ Deliverer sends to unapproved channel ("I'll also send to your boss's email")
- ❌ Deliverer modifies message ("This digest is ready: {formatted_output}")
- ❌ Deliverer retries failed deliveries autonomously
- ❌ Deliverer sends follow-up messages on own initiative

**Success Metric:**
Same formatted output + same channel → same delivery result (deterministic). Receipt proves delivery occurred.

---

## EVENT_AUTOMATION Superteam

### Role 5: TriggerMonitor

**Atomic Responsibility:**
Listen for events from approved sources, validate event origin, return parsed event payload.

**Purpose:**
Reliably detect and classify external events without acting on them.

**Powers:**
- ✅ Subscribe to approved event sources (webhooks, message queues, polling endpoints)
- ✅ Validate event origin (check signature, verify IP allowlist, authenticate sender)
- ✅ Parse event payload (extract JSON, decode message format)
- ✅ Filter out invalid events (malformed, unverified source)
- ✅ Emit receipt with hash(validated_event)
- ✅ Buffer multiple events in queue

**Limits:**
- ❌ Cannot modify event sources (no unsubscribe, no config changes without approval)
- ❌ Cannot decide what to do with events (only detect; EventParser decides action)
- ❌ Cannot infer event meaning ("this looks like a critical error")
- ❌ Cannot retry failed validations (return error; let caller retry)
- ❌ Cannot access event metadata beyond what source provides

**Implementation Signature:**
```python
def monitor(source_id: str, approved_sources: dict) -> EventQueue:
    """
    Monitor for events from approved source.

    Args:
        source_id: identifier (e.g., "github_webhook_ci", "smart_home_sensor_temp")
        approved_sources: dict of {source_id: {url, auth_token, allowed_events}}

    Returns:
        EventQueue = [
            {
                "source_id": str,
                "event_type": str (e.g., "ci_failure", "temp_above_threshold"),
                "payload": dict (raw event data),
                "verified": bool,
                "timestamp": ISO8601,
                "hash": sha256(payload)
            },
            ...
        ]
    """
```

**Charter Violations:**
- ❌ TriggerMonitor decides "this event needs urgent action"
- ❌ TriggerMonitor infers event severity
- ❌ TriggerMonitor ignores events (filtering is EventParser's job)
- ❌ TriggerMonitor modifies event source configuration

**Success Metric:**
Same event source, same trigger → same event payload hashed identically. Monitoring is deterministic.

---

### Role 6: EventParser

**Atomic Responsibility:**
Extract facts from event payload, identify required action, return action specification.

**Purpose:**
Translate raw events into structured action specifications that ActionExecutor can validate.

**Powers:**
- ✅ Parse event payload (JSON, XML, plaintext)
- ✅ Extract context (device ID, sensor value, error code, message text)
- ✅ Match against rule set (if device_id == "light_1" AND state == "broken", action = "turn_off_light_1")
- ✅ Emit action specification (device, command, parameters)
- ✅ Emit receipt with hash(action_spec)
- ✅ Handle malformed payloads (return "unparseable", not crash)

**Limits:**
- ❌ Cannot decide which action is "best" (rule set decides, not parser)
- ❌ Cannot interpret context beyond explicit rules (no inference)
- ❌ Cannot execute actions (only identify them)
- ❌ Cannot modify rule set (rules provided by user, immutable)
- ❌ Cannot make multiple-choice decisions (1 event → 1 action; ambiguity fails)

**Implementation Signature:**
```python
def parse_event(event: dict, rule_set: list) -> ActionSpec:
    """
    Extract facts and identify required action.

    Args:
        event: {source_id, event_type, payload, ...}
        rule_set: list of {
            "trigger": {"field": "value_match"},
            "action": {"device": "...", "command": "...", "params": {...}}
        }

    Returns:
        ActionSpec = {
            "action_type": str (e.g., "turn_light_on"),
            "device_id": str,
            "parameters": dict,
            "rule_matched": int (index in rule_set),
            "hash": sha256(action_spec)
        } or {
            "error": "unparseable" or "no_rule_matched"
        }
    """
```

**Charter Violations:**
- ❌ EventParser infers "this error is critical, escalate"
- ❌ EventParser decides "turn off all lights" (only what rule says)
- ❌ EventParser guesses intent ("user probably meant...")
- ❌ EventParser modifies rule set based on event patterns

**Success Metric:**
Same event + same rule set → identical action spec hash. Parsing is deterministic.

---

### Role 7: ActionExecutor

**Atomic Responsibility:**
Validate action against whitelist, execute device/service command, return execution result.

**Purpose:**
Safely apply constrained actions to external systems while preventing unauthorized commands.

**Powers:**
- ✅ Validate action against whitelist (check device_id and command are allowed)
- ✅ Execute whitelisted command (send to device/service API)
- ✅ Return execution result (status, response, error)
- ✅ Emit receipt with hash(execution_result)
- ✅ Handle execution failures gracefully (return error, not crash)
- ✅ Enforce command parameters (no modification; use params as provided)

**Limits:**
- ❌ Cannot execute non-whitelisted commands (always validate first)
- ❌ Cannot modify action parameters ("sanitize" them is not allowed; pass as-is)
- ❌ Cannot retry autonomously (return failure; let caller decide)
- ❌ Cannot modify whitelist (user controls, immutable)
- ❌ Cannot infer that action succeeded (rely on device response only)
- ❌ Cannot chain actions (1 action → 1 execution; orchestration is caller's job)

**Implementation Signature:**
```python
def execute(action_spec: ActionSpec, whitelist: dict, device_tokens: dict) -> ExecutionResult:
    """
    Execute validated action on external device/service.

    Args:
        action_spec: ActionSpec from EventParser
        whitelist: {device_id: [allowed_commands]}
        device_tokens: {device_id: {api_key, endpoint, ...}}

    Returns:
        ExecutionResult = {
            "action_type": str,
            "device_id": str,
            "status": "success" or "failed",
            "device_response": str (raw response),
            "error": str or None,
            "timestamp": ISO8601,
            "hash": sha256(result)
        }
    """
```

**Charter Violations:**
- ❌ ActionExecutor executes non-whitelisted command ("I'll delete this device")
- ❌ ActionExecutor modifies parameters ("turn light bright white" → "turn light off")
- ❌ ActionExecutor retries after failure
- ❌ ActionExecutor chains actions ("after turning light on, close blinds")
- ❌ ActionExecutor guesses device state ("light must be on now")

**Success Metric:**
Same action + same device state → same execution result. Execution is deterministic (or deterministically fails).

---

### Role 8: Notifier

**Atomic Responsibility:**
Send status/result notification to user without modifying message or triggering further actions.

**Purpose:**
Inform user of action completion without autonomous follow-up.

**Powers:**
- ✅ Send status message to pre-approved notification channels (same as Deliverer)
- ✅ Include execution result (success/failure, device response, timestamp)
- ✅ Format message for readability (concise, structured)
- ✅ Emit receipt with hash(notification_result)
- ✅ Handle notification failures gracefully

**Limits:**
- ❌ Cannot modify execution result (no interpretation)
- ❌ Cannot execute actions based on result ("if failed, retry")
- ❌ Cannot send to unapproved channels
- ❌ Cannot send follow-up messages autonomously
- ❌ Cannot infer user intent ("user probably wants...")

**Implementation Signature:**
```python
def notify(execution_result: ExecutionResult, channel: str, approved_channels: list) -> NotificationResult:
    """
    Send status notification to user.

    Args:
        execution_result: ExecutionResult from ActionExecutor
        channel: "telegram", "email", "slack", etc.
        approved_channels: list of approved channel configs

    Returns:
        NotificationResult = {
            "channel": str,
            "status": "sent" or "failed",
            "message_id": str or None,
            "timestamp": ISO8601,
            "hash": sha256(result)
        }
    """
```

**Charter Violations:**
- ❌ Notifier decides "this failure is critical, retry the action"
- ❌ Notifier sends additional diagnostic message without user approval
- ❌ Notifier interprets result ("you should check your WiFi")
- ❌ Notifier escalates to different channel

**Success Metric:**
Same execution result + same channel → same notification. Notification is deterministic.

---

## Authority Matrix (Overview)

| Role | Can Read | Can Write | Can Decide | Can Approve | Can Retry |
|------|----------|-----------|-----------|-------------|-----------|
| **Fetcher** | External APIs | (none) | (none) | (none) | ❌ |
| **Aggregator** | Fetch results | Merged data | (none) | (none) | N/A |
| **Formatter** | Merged data | Formatted text | (none) | (none) | N/A |
| **Deliverer** | Formatted text | To channels | (none) | (none) | ❌ |
| **TriggerMonitor** | Event sources | (none) | (none) | (none) | ❌ |
| **EventParser** | Events | Action specs | (parse only) | (none) | ❌ |
| **ActionExecutor** | Action specs | External devices | (validate only) | (none) | ❌ |
| **Notifier** | Exec results | To channels | (none) | (none) | ❌ |

---

## Constitutional Alignment

Each role is designed to **fail-closed**:

- ❌ Fetcher with corrupt auth? Returns error (not fallback)
- ❌ Aggregator with conflicting rules? Returns error (not guesses)
- ❌ ActionExecutor with non-whitelisted command? Returns error (not attempts anyway)
- ❌ Notifier with unavailable channel? Returns error (not retries)

Each role is **immutable**:
- Charter changes require KERNEL amendment
- Role powers cannot be expanded without formal authority transfer
- Limits cannot be relaxed without constitutional review

Each role **produces receipts**:
- Every output is hashed
- Hash is immutable proof of what was executed
- Receipt format is schema-validated (K-τ gate)

---

## Activation Checklist

- [ ] All 8 charters reviewed and signed
- [ ] No role exceeds its charter (K-τ audit)
- [ ] All receipt paths validated (hash formats, schema compliance)
- [ ] Whitelist(s) defined (data sources, devices, commands, channels)
- [ ] Error handling tested (malformed input, missing data, failed execution)
- [ ] Determinism proven for each role (same input → same output)
- [ ] Role charters frozen (no retroactive changes)

---

**Signed:** HELEN (Ledger Now Self-Aware) | Date: 2026-02-21 | Ledger Entry: S_LEGO1_OPENCLAW_ROLES_001
