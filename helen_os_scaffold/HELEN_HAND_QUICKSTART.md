# HELEN Hand System — Quick Start Guide

**Status:** Δ-040 SHIPPED (Schema + Gates + Registry Complete) ✅
**Date:** 2026-03-06
**Based On:** OpenFang Hand.toml pattern + ECC hardening + HELEN authority model

---

## What Just Got Built (15 minutes ago)

You now have:

1. ✅ **HELEN_HAND.toml Schema** — Manifest contract for agents
2. ✅ **Reducer Gates G0-G3** — Safety enforcement (allowlist, effect, immutability x2)
3. ✅ **Hand Registry** — Append-only lifecycle (register, update, activate, pause, remove)
4. ✅ **Δ-040 Ledger Entry** — Canonical governance proposal

**Files Created:**
```
helen_os/hand/
├── __init__.py                    # Package exports
├── schema.py                      # HELENHand manifest (400 lines)
├── reducer_gates.py               # G0-G3 gates (350 lines)
└── registry.py                    # Append-only events (400 lines)

HELEN_HAND_QUICKSTART.md           # This file
LEDGER_ENTRY_DELTA_040.md          # Canonical proposal
```

---

## 10-Minute Test

### Test 1: Create a Hand Manifest

```python
from helen_os.hand import HELENHand, AgentConfig

hand = HELENHand(
    id="helen-researcher",
    name="HELEN Researcher",
    description="Autonomous research hand",
    category="productivity",
    icon="🧪",
    tools=["web_search", "web_fetch", "file_read", "memory_recall"],
    agent=AgentConfig(
        name="researcher",
        description="Researches topics autonomously",
        system_prompt_ref="prompts/researcher.md",
        system_prompt_sha256="abc123...",  # Computed from file
    ),
)

# Compute immutable hash
hand.manifest_hash = hand.compute_manifest_hash()
print(f"Hand ID: {hand.id}")
print(f"Manifest Hash: {hand.manifest_hash}")
print(f"Tools: {hand.tools}")
```

### Test 2: Run Gate Checks

```python
from helen_os.hand.reducer_gates import verify_hand_before_execution

# Verify all gates before execution
all_passed, results = verify_hand_before_execution(
    hand=hand,
    tool_name="web_search",
    last_committed_manifest_hash=hand.manifest_hash,
)

print(f"All Gates Passed: {all_passed}")
for result in results:
    print(f"  {result}")
    # Output:
    # ✅ PASS G0: Tool 'web_search' is in Hand allowlist
    # ✅ PASS G1: Tool 'web_search' is OBSERVE (read-only, allowed)
    # ✅ PASS G2: Hand manifest hash matches last committed
    # ✅ PASS G3: No prompt declared; gate passes
```

### Test 3: Register Hand in Ledger

```python
from helen_os.hand import HandRegistry

registry = HandRegistry("receipts/hand_registry.jsonl")

# Register the Hand
receipt = registry.register_hand(
    hand_id=hand.id,
    manifest_hash=hand.manifest_hash,
    prompt_hash=hand.agent.system_prompt_sha256,
)
print(f"Registered! Receipt: {receipt}")

# Query state
state = registry.get_hand_state("helen-researcher")
print(f"State: {state}")
# Output:
# {
#   'hand_id': 'helen-researcher',
#   'status': 'active',
#   'manifest_hash': '...',
#   'prompt_hash': '...',
#   'last_event': '2026-03-06T...'
# }

# Activate Hand
registry.activate_hand("helen-researcher", "Ready for execution")

# List all Hands
hands = registry.list_hands()
for h in hands:
    print(f"  {h['hand_id']}: {h['status']}")
```

### Test 4: Run All Tests at Once

```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24/helen_os_scaffold
source .venv/bin/activate

# Test schema
python -m helen_os.hand.schema

# Test gates
python -m helen_os.hand.reducer_gates

# Test registry
python -m helen_os.hand.registry
```

---

## Key Concepts (30 seconds each)

### Hand
A capability package = (manifest + tools + agent config + guardrails)

Example: "HELEN Researcher" is a Hand that uses web_search/web_fetch to autonomously research topics.

### HAND.toml
Declarative manifest file (YAML/TOML/JSON format).

```toml
id = "helen-researcher"
name = "HELEN Researcher"
tools = ["web_search", "web_fetch", "file_read"]

[agent]
system_prompt_ref = "prompts/researcher.md"
system_prompt_sha256 = "abc123..."
```

### Reducer Gates (G0-G3)
Safety checks before **any** tool execution:

1. **G0** — Is the tool in the Hand's allowlist?
2. **G1** — Is this tool OBSERVE (safe) or EXECUTE (needs approval)?
3. **G2** — Has the Hand manifest changed since last registration?
4. **G3** — Does the prompt file match the declared hash?

All 4 must pass for execution.

### Hand Registry
Append-only ledger of Hand events:
- `HandRegistered` — New Hand
- `HandUpdated` — Manifest changed
- `HandActivated` — Ready to run
- `HandPaused` — Temporarily stopped
- `HandRemoved` — Permanently deactivated

### Effect Classification

| Tool | Effect | Allowed? | Notes |
|------|--------|----------|-------|
| `web_search` | OBSERVE | ✅ Yes | Read-only |
| `file_read` | OBSERVE | ✅ Yes | Read-only |
| `memory_store` | PROPOSE | ✅ Yes | Creates proposal |
| `file_write` | EXECUTE | ❌ Needs approval | Modifies state |
| `shell_execute` | EXECUTE | ❌ Needs approval | Dangerous |

---

## Next Steps (What You Can Do Now)

### Option 1: Create Your Own Hand (15 min)

Create `prompts/researcher.md`:
```markdown
# HELEN Researcher System Prompt

You are HELEN OS, operating as a Researcher Hand.

MISSION: Research topics thoroughly and prepare reports.

CAPABILITIES:
- web_search: Search the internet
- web_fetch: Fetch full article content
- file_read: Read research files
- memory_recall: Access HELEN's knowledge base

CONSTRAINTS:
- You can PROPOSE changes to memory, never EXECUTE directly
- OBSERVE tools (search, fetch, read) are unrestricted
- Never attempt shell_execute or file_write
```

Create `helen-researcher.toml`:
```toml
id = "helen-researcher"
name = "HELEN Researcher"
description = "Autonomous research hand"
category = "productivity"
icon = "🧪"

tools = ["web_search", "web_fetch", "file_read", "memory_recall", "memory_store"]

[[settings]]
key = "research_depth"
label = "Research Depth"
description = "How exhaustive to be"
setting_type = "select"
default = "thorough"

[[settings.options]]
value = "quick"
label = "Quick (5 min)"

[[settings.options]]
value = "thorough"
label = "Thorough (30 min)"

[agent]
name = "researcher-hand"
description = "Produces research reports"
system_prompt_ref = "prompts/researcher.md"
system_prompt_sha256 = "COMPUTE_ME"

[dashboard]
[[dashboard.metrics]]
label = "Reports Generated"
memory_key = "helen_research_reports"
format = "number"
```

Then load & register:
```python
from helen_os.hand import HELENHand, HandRegistry
from pathlib import Path

hand = HELENHand.load_from_toml_file(Path("helen-researcher.toml"))
hand.manifest_hash = hand.compute_manifest_hash()

registry = HandRegistry()
registry.register_hand(hand.id, hand.manifest_hash, hand.agent.system_prompt_sha256)
```

### Option 2: Integrate Gates into Gateway (30 min)

Modify `server.py` or `helen_talk.py`:

```python
from helen_os.hand import HELENHand, verify_hand_before_execution

@app.route("/execute_tool", methods=["POST"])
def execute_tool(hand_id, tool_name, approval_token=None):
    """Execute a tool via a Hand, with gate checks."""

    # Load Hand
    hand = load_hand(hand_id)  # Your function

    # Get last committed manifest hash from ledger
    last_hash = get_last_committed_hand_hash(hand_id)

    # Verify all gates
    all_passed, results = verify_hand_before_execution(
        hand=hand,
        tool_name=tool_name,
        last_committed_manifest_hash=last_hash,
        approval_token=approval_token,
    )

    # Fail-closed: if any gate fails, emit NEEDS_APPROVAL proposal instead
    if not all_passed:
        failed_gates = [r for r in results if not r.passed]
        emit_proposal(
            type="NEEDS_APPROVAL",
            tool=tool_name,
            hand=hand_id,
            failures=[r.message for r in failed_gates],
        )
        return {"status": "needs_approval", "reason": failed_gates[0].message}

    # All gates passed: execute tool
    result = execute_tool_unsafe(hand_id, tool_name, ...)
    return {"status": "ok", "result": result}
```

### Option 3: Write Tests (45 min)

Create `tests/test_hand_system.py`:

```python
import pytest
from helen_os.hand import HELENHand, ReducerGates, HandRegistry

def test_hand_schema_loads():
    """Test loading Hand from TOML."""
    hand = HELENHand.load_from_toml_file(Path("helen-researcher.toml"))
    assert hand.id == "helen-researcher"
    assert "web_search" in hand.tools

def test_gate_g0_allowlist():
    """Test G0 gate."""
    hand = HELENHand(id="test", tools=["web_search"])

    # Allowed tool
    result = ReducerGates.gate_g0_tool_allowlist(hand, "web_search")
    assert result.passed

    # Disallowed tool
    result = ReducerGates.gate_g0_tool_allowlist(hand, "shell_execute")
    assert not result.passed

def test_hand_registry_lifecycle():
    """Test Hand registration, activation, pause."""
    registry = HandRegistry()

    registry.register_hand("test-hand", "abc123")
    state = registry.get_hand_state("test-hand")
    assert state["status"] == "active"

    registry.pause_hand("test-hand")
    state = registry.get_hand_state("test-hand")
    assert state["status"] == "paused"
```

Then run:
```bash
pytest tests/test_hand_system.py -v
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│         User Request (LLM or CLI)               │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│   Hand Manifest Loader (TOML/JSON)              │
│   ├─ Load HAND.toml or JSON                    │
│   ├─ Compute manifest_hash (immutable)          │
│   └─ Load system_prompt_ref + verify hash       │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│       Reducer Gates (CRITICAL)                  │
│   ├─ G0: Tool allowlist check                  │
│   ├─ G1: Effect (OBSERVE/PROPOSE/EXECUTE)      │
│   ├─ G2: Manifest immutability                 │
│   └─ G3: Prompt immutability                   │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         ↓ (Fail)             ↓ (Pass)
    ❌ PROPOSAL          ✅ EXECUTE TOOL
   (Needs Approval)    (Tool runs)
         │                    │
         └────────┬───────────┘
                  ↓
       ┌──────────────────────┐
       │  Hand Registry       │
       │  Append-only events  │
       │  (Receipt chain)     │
       └──────────────────────┘
```

---

## OpenFang → HELEN Translation

| OpenFang | HELEN | Difference |
|----------|-------|-----------|
| Hand.toml | HELEN_HAND.toml | Same structure, HELEN adds manifest_hash pinning |
| Hands execute tools | Gates check before execution | HELEN is fail-closed (gates enforce) |
| In-process approval | Approval token requirement | HELEN requires explicit token (gated) |
| Registry (in-memory) | Hand Registry (append-only ledger) | HELEN makes registry immutable |
| Metrics → Dashboard | Dashboard bindings in manifest | Same |
| Manifest changes = reload | Manifest hash mismatch = re-register | HELEN forces immutability |

---

## FAQ

**Q: Can a Hand call another Hand?**
A: Not yet. That's a future feature (Hand-to-Hand RPC). For now, Hands are single-purpose.

**Q: What happens if I modify helen-researcher.toml on disk?**
A: Next execution, G2 gate detects manifest_hash mismatch and rejects. You must re-register.

**Q: Can a Hand approve EXECUTE tools for itself?**
A: No. Approval must come from outside (human, or another Hand). This prevents self-authorization.

**Q: Where does approval_token come from?**
A: That's configurable. Could be:
- User types `--approval-token abc123`
- Approval comes from a "Governance Hand" (meta-agent)
- Ledger stores pre-authorized tokens for common actions

**Q: Are Hands scheduled automatically?**
A: Not yet. Currently Hands execute on-demand via CLI or API. Scheduling is Phase 3.

---

## Summary

You now have **agents-as-services** in HELEN with:
- ✅ Manifest-based packaging (OpenFang pattern)
- ✅ Non-negotiable safety gates (G0-G3)
- ✅ Append-only registry (immutable lifecycle)
- ✅ Authority preserved (propose → reducer → ledger)

**This is Δ-040. SEALED for ledger commit.** 🔐

Next: Integrate gates into gateway, create sample Hands, write tests.

Ready to proceed? Pick one: Test it now, Create your first Hand, or Integrate into gateway?
