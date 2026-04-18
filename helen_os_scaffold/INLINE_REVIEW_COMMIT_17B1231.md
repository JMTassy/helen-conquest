# Inline Code Review — Commit 17b1231
## HELEN Hand System Implementation

**Date:** 2026-03-06
**Reviewer:** Claude Code
**Scope:** Hand schema, reducer gates, registry, integration
**Status:** COMPREHENSIVE REVIEW WITH ACTIONABLE FEEDBACK

---

## FILE 1: `helen_os/hand/schema.py` (400 LoC)

### Summary
✅ **Solid design.** Manifest contract is well-structured, canonical JSON hashing is deterministic, and the dataclass hierarchy is clean. Three issues to address before production.

---

### Review Comments

#### **Line 39: Literal type annotation syntax**
```python
SettingType = Literal["select", "toggle", "text", "number", "slider"]
```
**Comment:** This is a module-level `Literal` assignment. Works in Python 3.8+, but could be more explicit. Consider wrapping in a TypeAlias for clarity in Python 3.10+.

**Suggestion:**
```python
from typing import TypeAlias

SettingType: TypeAlias = Literal["select", "toggle", "text", "number", "slider"]
```
**Priority:** LOW — Works as-is, but improves IDE hint clarity.

---

#### **Line 33-35: `canonical_json()` duplicated in two files**
```python
def canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
```
**Comment:** This function is **duplicated** in both `schema.py` and `chain_v1.py`. Code smell: VIOLATION of DRY principle. If you ever need to update the canonical format (e.g., to handle datetime objects), you'll have to patch it in two places.

**Recommendation:**
- Move to shared utility module: `helen_os/receipts/canonical.py`
- Export from both `chain_v1.py` and `schema.py`
- Update imports in all dependents

**Priority:** MEDIUM — Blocks maintenance over time.

---

#### **Lines 23-30: Hash computation helpers missing validation**
```python
def sha256_file(path: Path) -> str:
    """Compute SHA256 of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sha256_text(text: str) -> str:
    """Compute SHA256 of text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
```
**Comment:** Both functions silently raise exceptions on file-not-found or encoding error. Callers have to handle this themselves.

**Observation:** This is appropriate for a schema validator (fail-fast on bad input). However, **G3 gate in reducer_gates.py** also does its own hash computation at line 264. Opportunity for code reuse.

**Suggestion:** Export `sha256_file()` from `schema.py`, use in G3 gate.

**Priority:** LOW — Works, but duplication.

---

#### **Lines 203-222: `to_dict()` method with optional hash exclusion**
```python
def to_dict(self, exclude_hash: bool = False) -> Dict:
    """Convert to dict (for JSON serialization or hashing)."""
    ...
    if not exclude_hash:
        data["manifest_hash"] = self.manifest_hash
    return data
```
**Comment:** ✅ **Clever and correct.** Ensures that `manifest_hash` is never included in the canonical form used for hashing (would create circular dependency). Matches the pattern in receipt chaining.

**Status:** APPROVED.

---

#### **Line 224-231: Manifest hash computation**
```python
def compute_manifest_hash(self) -> str:
    """
    Compute manifest hash (excludes manifest_hash field itself).
    Used for immutability validation.
    """
    data = self.to_dict(exclude_hash=True)
    canon = canonical_json(data)
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()
```
**Comment:** ✅ **Correct.** Excludes the hash field, uses canonical JSON (deterministic), computes SHA256.

**Observation:** The `.encode('utf-8')` is redundant since `canonical_json()` already returns a `str`. The SHA256 will encode it again. **Not a bug**, but slightly inefficient.

**Suggestion:**
```python
canon = canonical_json(data)
return hashlib.sha256(canon.encode('utf-8')).hexdigest()
# Or inline:
return hashlib.sha256(canonical_json(data).encode('utf-8')).hexdigest()
```
**Priority:** TRIVIAL — No functional impact.

---

#### **Lines 250-309: `load_from_dict()` and loaders**
```python
@classmethod
def load_from_dict(cls, data: Dict) -> "HELENHand":
    """Load Hand from dict (e.g., parsed TOML or JSON)."""
    # ... settings parsing ...
    # ... requirements parsing ...
    # ... agent parsing ...
    # ... dashboard parsing ...
    # ... guardrails parsing ...
    return cls(...)
```
**Comment:** ✅ **Solid.** Nested dataclass construction is explicit and readable. Good separation of concerns.

**Edge Case:** What if `data["id"]` is missing? Or `data["name"]`? The code will raise `KeyError`, not a user-friendly validation error.

**Suggestion:** Add optional validation layer OR document that callers must pre-validate.

```python
# Option A: Pre-validate caller side (current model)
# Option B: Add JSON Schema validation before load_from_dict()
```

**Current Status:** ACCEPTABLE (caller responsibility), but document this.

**Priority:** LOW.

---

#### **Lines 312-322: `load_from_toml_file()` — Fallback import**
```python
@classmethod
def load_from_toml_file(cls, path: Path) -> "HELENHand":
    """Load Hand from TOML file."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # Fallback

    data = tomllib.loads(path.read_text())
    hand = cls.load_from_dict(data)
    hand.manifest_hash = hand.compute_manifest_hash()
    return hand
```
**Comment:** ✅ **Good pattern.** Fallback to `tomli` (pure-Python backport) is sensible.

**Observation:** Assumes `tomli` is installed if Python < 3.11. Document this in `pyproject.toml`:
```toml
dependencies = [
    'tomli >= 1.2.0 ; python_version < "3.11"',
]
```

**Status:** APPROVED with documentation requirement.

**Priority:** MEDIUM — Blocks installation on older Python without explicit dep.

---

#### **Lines 333-365: Test block (`if __name__ == "__main__"`)**
```python
if __name__ == "__main__":
    hand = HELENHand(...)
    hand.manifest_hash = hand.compute_manifest_hash()
    print(f"Verified: {hand.verify_manifest_hash()}")
```
**Comment:** ✅ Good smoke test. Catches basic schema loading issues.

**Suggestion:** Move this to `tests/test_hand_schema.py` so it's part of the test suite. Keep a minimal smoke test here for debugging.

**Priority:** LOW.

---

### SUMMARY: schema.py

| Issue | Severity | Action |
|-------|----------|--------|
| Duplicate `canonical_json()` in chain_v1.py | MEDIUM | Extract to shared utility |
| `Literal` type hint syntax | LOW | Use `TypeAlias` for clarity |
| Missing `tomli` in deps | MEDIUM | Add to `pyproject.toml` |
| Potential `KeyError` in load_from_dict | LOW | Document caller responsibility |
| Redundant `.encode()` in hash | TRIVIAL | Clean up |

**Verdict:** READY with minor fixes.

---

## FILE 2: `helen_os/hand/reducer_gates.py` (350 LoC)

### Summary
✅ **Excellent design.** Four gates are non-negotiable, effect classification is clean, gate results are structured. Two concerns and one opportunity.

---

### Review Comments

#### **Lines 37-67: ToolClassifier constants**
```python
class ToolClassifier:
    OBSERVE_TOOLS = {"web_search", "file_read", ...}
    PROPOSE_TOOLS = {"memory_store", ...}
    EXECUTE_TOOLS = {"file_write", "shell_execute", ...}
```
**Comment:** ✅ **Clean separation.** Three mutually-exclusive tiers with clear semantics.

**Concern:** What if a tool is added in the future that's not in any set? Line 80 defaults to "execute" (fail-safe):
```python
else:
    # Default to execute (fail-safe)
    return "execute"
```

**Good:** Fail-safe by defaulting to most-restrictive tier.
**Question:** Should unknown tools be warned in logs? Or is silent fail-safe acceptable?

**Suggestion:** Add a logging call:
```python
else:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Unknown tool '{tool_name}' defaulting to EXECUTE (fail-safe)")
    return "execute"
```

**Priority:** LOW — Fail-safe is correct, logging is nice-to-have.

---

#### **Lines 87-112: Gate G0 — Tool Allowlist**
```python
@staticmethod
def gate_g0_tool_allowlist(
    hand: HELENHand,
    tool_name: str,
) -> GateResult:
    if tool_name in hand.tools:
        return GateResult(passed=True, ...)
    else:
        return GateResult(passed=False, ...)
```
**Comment:** ✅ **Minimal and correct.** No surprises.

**Status:** APPROVED.

---

#### **Lines 114-163: Gate G1 — Effect Separation**
```python
@staticmethod
def gate_g1_effect_separation(
    hand: HELENHand,
    tool_name: str,
    approval_token: Optional[str] = None,
) -> GateResult:
    effect = ToolClassifier.classify(tool_name)

    if effect == "observe":
        return GateResult(passed=True, ...)
    elif effect == "propose":
        return GateResult(passed=True, ...)
    elif effect == "execute":
        if approval_token:
            return GateResult(passed=True, ...)
        else:
            return GateResult(passed=False, ...)
```
**Comment:** ✅ **Logic is sound.** OBSERVE and PROPOSE bypass approval; EXECUTE requires token.

**Observation:** The `approval_token` is checked for existence but not validated. Line 147:
```python
if approval_token:
```
This is a **weak check**. An empty string `""` or whitespace-only string would pass.

**Suggestion:** Strengthen validation:
```python
if approval_token and len(approval_token.strip()) > 0:
    return GateResult(passed=True, ...)
else:
    return GateResult(passed=False, ...)
```

**Priority:** MEDIUM — Currently allows empty tokens to slip through.

---

#### **Lines 165-206: Gate G2 — Manifest Immutability**
```python
@staticmethod
def gate_g2_manifest_immutability(
    hand: HELENHand,
    last_committed_manifest_hash: Optional[str],
) -> GateResult:
    current_hash = hand.compute_manifest_hash()

    if last_committed_manifest_hash is None:
        return GateResult(passed=True, ...)  # First run

    if current_hash == last_committed_manifest_hash:
        return GateResult(passed=True, ...)  # Match
    else:
        return GateResult(passed=False, ...)  # Mismatch
```
**Comment:** ✅ **Correct logic.** Handles both new Hand (no prior hash) and existing Hand (hash must match).

**Detail:** Line 182 treats first registration as a pass. This is correct — the Hand isn't committed yet.

**Status:** APPROVED.

---

#### **Lines 208-282: Gate G3 — Prompt Immutability**
```python
@staticmethod
def gate_g3_prompt_immutability(
    hand: HELENHand,
    prompt_search_paths: Optional[List[Path]] = None,
) -> GateResult:
    if not hand.agent or not hand.agent.system_prompt_ref:
        return GateResult(passed=True, ...)  # No prompt

    # ... search for prompt file ...

    if not prompt_path:
        return GateResult(passed=False, ...)  # File not found

    actual_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()

    if actual_hash == prompt_sha256:
        return GateResult(passed=True, ...)  # Match
    else:
        return GateResult(passed=False, ...)  # Mismatch
```

**Comment:** ✅ **Solid.** Finds the prompt file, computes hash, compares.

**Observations:**

1. **Line 241-246:** Default search paths include `helen_os_scaffold/prompts`. Good hardcoding for common case.

2. **Line 264:** Duplicates hash computation from `schema.py`. See earlier note about `sha256_file()` reuse.

3. **Edge Case:** What if prompt file is very large (GB+)? `.read_bytes()` loads entire file into memory.

   **Concern:** Could cause memory spike on huge files. Not critical for typical prompts (usually <100 KB), but worth noting.

   **Suggestion:** For production, consider streaming hash:
   ```python
   def sha256_file_streaming(path: Path) -> str:
       hasher = hashlib.sha256()
       with open(path, 'rb') as f:
           while chunk := f.read(8192):
               hasher.update(chunk)
       return hasher.hexdigest()
   ```

   **Priority:** LOW — Acceptable for now; document assumption of small prompts.

---

#### **Lines 285-308: `verify_hand_before_execution()` wrapper**
```python
def verify_hand_before_execution(
    hand: HELENHand,
    tool_name: str,
    last_committed_manifest_hash: Optional[str],
    approval_token: Optional[str] = None,
    prompt_search_paths: Optional[List[Path]] = None,
) -> Tuple[bool, List[GateResult]]:
    gates = ReducerGates()

    results = [
        gates.gate_g0_tool_allowlist(hand, tool_name),
        gates.gate_g1_effect_separation(hand, tool_name, approval_token),
        gates.gate_g2_manifest_immutability(hand, last_committed_manifest_hash),
        gates.gate_g3_prompt_immutability(hand, prompt_search_paths),
    ]

    all_passed = all(r.passed for r in results)
    return all_passed, results
```

**Comment:** ✅ **Clean orchestration.** Runs all 4 gates in sequence, returns structured results.

**Observation:** Creating a new `ReducerGates()` instance each time is unnecessary since all methods are static. Could be a module-level callable or use the class directly.

**Suggestion:**
```python
# Current:
gates = ReducerGates()
results = [gates.gate_g0_tool_allowlist(...), ...]

# Option A: Call class methods directly (cleaner)
results = [
    ReducerGates.gate_g0_tool_allowlist(...),
    ReducerGates.gate_g1_effect_separation(...),
    ...
]

# Option B: Keep current pattern for future extensibility
# (maybe add state later — acceptable)
```

**Priority:** TRIVIAL — Current code works fine.

---

#### **Lines 311-369: Test block**
```python
if __name__ == "__main__":
    hand = HELENHand(...)
    r1 = ReducerGates.gate_g0_tool_allowlist(hand, "web_search")
    print(f"  {r1}")
    ...
```

**Comment:** ✅ Good smoke test for manual debugging.

**Suggestion:** Move core logic to `tests/test_hand_gates.py`.

**Priority:** LOW.

---

### SUMMARY: reducer_gates.py

| Issue | Severity | Action |
|-------|----------|--------|
| `approval_token` check allows empty string | MEDIUM | Strengthen validation |
| Duplicate `sha256_file()` computation | MEDIUM | Extract to utility |
| Unknown tools need logging | LOW | Add warning log |
| Large prompt file handling | LOW | Document assumption; note streaming alternative |
| Unnecessary `ReducerGates()` instance | TRIVIAL | Optional refactor |

**Verdict:** READY with medium-priority fixes.

---

## FILE 3: `helen_os/hand/registry.py` (400 LoC)

### Summary
✅ **Excellent implementation.** Append-only registry using receipt chaining is correct. Two edge cases to handle.

---

### Review Comments

#### **Lines 24-45: `HandRegistryEvent` dataclass**
```python
@dataclass
class HandRegistryEvent:
    event_type: str
    hand_id: str
    timestamp: str
    manifest_hash: str
    prompt_hash: Optional[str] = None
    reason: Optional[str] = None
    actor: str = "helen_reducer"
```

**Comment:** ✅ Clean dataclass. All fields are necessary.

**Observation:** `timestamp` is a string (ISO 8601). Good for human readability, but no validation that it's actually ISO format.

**Suggestion:** Optional strict validation:
```python
from datetime import datetime

def __post_init__(self):
    try:
        datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"Invalid ISO 8601 timestamp: {self.timestamp}")
```

**Priority:** LOW — Works as-is; validation is nice-to-have.

---

#### **Lines 54-62: Constructor**
```python
def __init__(self, ledger_path: str = "receipts/hand_registry.jsonl"):
    self.ledger_path = ledger_path
    self.chain = ReceiptChain(ledger_path)
```

**Comment:** ✅ Initializes receipt chain for durable append.

**Question:** What if `receipts/` directory doesn't exist? `ReceiptChain` will raise `FileNotFoundError` or similar when first write is attempted.

**Suggestion:** Add optional auto-creation:
```python
def __init__(self, ledger_path: str = "receipts/hand_registry.jsonl"):
    self.ledger_path = ledger_path
    Path(ledger_path).parent.mkdir(parents=True, exist_ok=True)
    self.chain = ReceiptChain(ledger_path)
```

**Priority:** MEDIUM — Improves UX; prevents cryptic errors.

---

#### **Lines 64-98: `register_hand()` method**
```python
def register_hand(
    self,
    hand_id: str,
    manifest_hash: str,
    prompt_hash: Optional[str] = None,
    reason: Optional[str] = None,
) -> Optional[str]:
    event = HandRegistryEvent(
        event_type="HandRegistered",
        hand_id=hand_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        manifest_hash=manifest_hash,
        prompt_hash=prompt_hash,
        reason=reason or f"Registering Hand '{hand_id}'",
    )

    try:
        entry_hash = self.chain.append(event.to_dict(), fail_on_error=True)
        print(f"[REGISTRY] ✅ Hand '{hand_id}' registered. Receipt: {entry_hash}")
        return entry_hash
    except RuntimeError as e:
        print(f"[REGISTRY] ❌ Failed to register Hand '{hand_id}': {e}")
        return None
```

**Comment:** ✅ **Good pattern.** Creates event, appends to chain, catches exceptions.

**Observations:**

1. **Line 86:** `datetime.utcnow().isoformat() + "Z"` produces ISO 8601 with Z suffix. Standard.

2. **Line 93-98:** Catches `RuntimeError` and logs error, returns `None`. Callers must check for `None`.

3. **Concern:** `print()` to stdout. In production, should use `logging` module.

**Suggestion:**
```python
import logging

logger = logging.getLogger(__name__)

def register_hand(...):
    ...
    try:
        entry_hash = self.chain.append(...)
        logger.info(f"Hand '{hand_id}' registered. Receipt: {entry_hash}")
        return entry_hash
    except RuntimeError as e:
        logger.error(f"Failed to register Hand '{hand_id}': {e}")
        return None
```

**Priority:** MEDIUM — Blocks production logging integration.

---

#### **Lines 100-138: `update_hand()` method**
```python
def update_hand(
    self,
    hand_id: str,
    new_manifest_hash: str,
    old_manifest_hash: str,
    new_prompt_hash: Optional[str] = None,
) -> Optional[str]:
    event_dict = {
        "event_type": "HandUpdated",
        "hand_id": hand_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "old_manifest_hash": old_manifest_hash,
        "new_manifest_hash": new_manifest_hash,
        "new_prompt_hash": new_prompt_hash,
        "reason": f"Hand '{hand_id}' manifest updated",
        "actor": "helen_reducer",
    }

    try:
        entry_hash = self.chain.append(event_dict, fail_on_error=True)
        logger.info(f"Hand '{hand_id}' updated. Receipt: {entry_hash}")
        return entry_hash
    except RuntimeError as e:
        logger.error(f"Failed to update Hand '{hand_id}': {e}")
        return None
```

**Comment:** ✅ **Good audit trail.** Preserves `old_manifest_hash` for history.

**Observation:** Uses raw `dict` instead of `HandRegistryEvent`. This is intentional (HandUpdated has different fields than HandRegistered). Acceptable pattern.

**Status:** APPROVED.

---

#### **Lines 140-169: `activate_hand()` and similar**
```python
def activate_hand(self, hand_id: str, reason: Optional[str] = None) -> Optional[str]:
    event_dict = {
        "event_type": "HandActivated",
        "hand_id": hand_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reason": reason or f"Hand '{hand_id}' activated for execution",
        "actor": "helen_reducer",
    }
    ...
```

**Comment:** ✅ Pattern is consistent across `pause_hand()`, `remove_hand()`, etc.

**Status:** APPROVED.

---

#### **Lines 233-295: `get_hand_state()` method**
```python
def get_hand_state(self, hand_id: str) -> Dict[str, Any]:
    """
    Query current state of a Hand from registry.

    Returns latest state: active/paused/removed, current manifest hash, etc.
    """
    state = {
        "hand_id": hand_id,
        "status": "unknown",
        "manifest_hash": None,
        "prompt_hash": None,
        "last_event": None,
    }

    try:
        with open(self.ledger_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                event = json.loads(line)
                if event.get("hand_id") != hand_id:
                    continue

                event_type = event.get("event_type")

                # Update state based on event
                if event_type == "HandRegistered":
                    state["status"] = "active"
                    state["manifest_hash"] = event.get("manifest_hash")
                    state["prompt_hash"] = event.get("prompt_hash")

                elif event_type == "HandUpdated":
                    state["manifest_hash"] = event.get("new_manifest_hash")
                    state["prompt_hash"] = event.get("new_prompt_hash") or state["prompt_hash"]
                    state["status"] = "active"

                elif event_type == "HandActivated":
                    state["status"] = "active"

                elif event_type == "HandPaused":
                    state["status"] = "paused"

                elif event_type == "HandRemoved":
                    state["status"] = "removed"

                state["last_event"] = event.get("timestamp")

    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[WARN] Failed to read registry: {e}")

    return state
```

**Comment:** ✅ **Correct replay logic.** Scans ledger from start to end, replaying state transitions.

**Concerns:**

1. **Performance:** For a ledger with 10,000 Hand events, this scans the entire file every time. No indexing or caching.

   **Acceptable:** This is an initial implementation. For production, could add:
   - In-memory cache (reload on changes)
   - Index by hand_id for faster lookups
   - Batch query API for multiple Hands

   **Priority:** LOW for now; document as O(n) scan.

2. **State machine completeness:** Current logic treats `HandRegistered` → `"active"`. But what if a Hand is registered, then paused, then the query is run?

   **Observation:** The code correctly replays all events in order, so final state is correct. ✅

3. **Edge Case:** What if `new_prompt_hash` is `None`?
   ```python
   state["prompt_hash"] = event.get("new_prompt_hash") or state["prompt_hash"]
   ```
   This preserves the previous hash (correct behavior for updates where prompt didn't change).

4. **Logging:** Uses `print()` again. Should use `logging` module.

**Suggestion:** Replace print with logger:
```python
logger.warning(f"Failed to read registry: {e}")
```

**Priority:** MEDIUM.

---

#### **Lines 297-345: `list_hands()` method**
```python
def list_hands(self) -> List[Dict[str, Any]]:
    """
    List all registered Hands (current state).
    """
    hands = {}

    try:
        with open(self.ledger_path, 'r') as f:
            for line in f:
                # ... replay logic (same as get_hand_state) ...
                hands[hand_id] = {
                    "hand_id": hand_id,
                    "status": ...,
                    "manifest_hash": ...,
                    "last_event": ...,
                }

    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[WARN] Failed to list Hands: {e}")

    return list(hands.values())
```

**Comment:** ✅ **Correct.** Same replay pattern as `get_hand_state()`, but aggregates all Hands.

**Code Smell:** `get_hand_state()` and `list_hands()` share replay logic. Could refactor to a shared `_replay_ledger()` method.

**Suggestion:**
```python
def _replay_ledger(self) -> Dict[str, Dict[str, Any]]:
    """Replay entire ledger, return state of all Hands."""
    hands = {}

    try:
        with open(self.ledger_path, 'r') as f:
            for line in f:
                # ... shared replay logic ...
                hands[hand_id] = {...}
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Failed to read registry: {e}")

    return hands

def get_hand_state(self, hand_id: str) -> Dict[str, Any]:
    """Query state of a single Hand."""
    all_hands = self._replay_ledger()
    return all_hands.get(hand_id, {"hand_id": hand_id, "status": "unknown", ...})

def list_hands(self) -> List[Dict[str, Any]]:
    """List all Hands."""
    all_hands = self._replay_ledger()
    return list(all_hands.values())
```

**Priority:** MEDIUM — Reduces duplication, improves maintainability.

---

#### **Lines 348-393: Test block**
```python
if __name__ == "__main__":
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.makedirs("receipts", exist_ok=True)

        registry = HandRegistry("receipts/hand_registry.jsonl")

        registry.register_hand(...)
        registry.activate_hand(...)
        registry.update_hand(...)
        state = registry.get_hand_state(...)
        hands = registry.list_hands()
```

**Comment:** ✅ **Solid integration test.** Tests the full lifecycle in a temp directory.

**Observation:** Uses tempfile and changes cwd. Good isolation.

**Status:** APPROVED. Move to `tests/test_hand_registry.py` if not already there.

---

### SUMMARY: registry.py

| Issue | Severity | Action |
|-------|----------|--------|
| Auto-create `receipts/` directory | MEDIUM | Improve UX |
| Replace `print()` with `logger` | MEDIUM | Production logging |
| Refactor shared replay logic | MEDIUM | Reduce duplication |
| Document O(n) ledger scan | LOW | Note for production |
| Timestamp validation | LOW | Optional strict validation |

**Verdict:** READY with medium-priority improvements.

---

## CROSS-FILE OBSERVATIONS

### 1. **Canonical JSON Duplication** (Multiple Files)

`canonical_json()` is defined in:
- `helen_os/hand/schema.py` (line 33)
- `helen_os/receipts/chain_v1.py` (similar)

**Risk:** If one is updated and the other isn't, hashes diverge silently.

**Action:** Extract to `helen_os/receipts/canonical.py`:
```python
# helen_os/receipts/canonical.py
def canonical_json(obj: Any) -> str:
    """Canonical JSON for deterministic hashing."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
```

Then import in both modules:
```python
from helen_os.receipts.canonical import canonical_json
```

**Priority:** MEDIUM — Blocks maintenance.

---

### 2. **Logging Strategy** (Multiple Files)

Current: `print()` for user feedback
Needed: `logging` module for production

**Action:** Add at top of each file:
```python
import logging
logger = logging.getLogger(__name__)
```

Replace all `print()` with `logger.info()`, `logger.warning()`, etc.

**Priority:** MEDIUM.

---

### 3. **Error Handling Pattern** (Consistent ✅)**

All three files catch exceptions and return `None` or empty result:
```python
try:
    # ... operation ...
    return result
except Exception as e:
    logger.error(f"Error: {e}")
    return None
```

**Comment:** ✅ Consistent fail-safe pattern. Good.

**Suggestion:** Add specific exception types for better error discrimination:
```python
try:
    ...
except FileNotFoundError:
    logger.error(f"Ledger file not found: {self.ledger_path}")
    return None
except RuntimeError as e:
    logger.error(f"Chain append failed: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return None
```

**Priority:** LOW.

---

### 4. **Testing Coverage** (Needs Work)

Smoke tests exist in `if __name__ == "__main__"` blocks, but full test suite should be in `tests/`:
- `tests/test_hand_schema.py` — manifest creation, hashing, loading
- `tests/test_hand_gates.py` — G0-G3 gates with fixtures
- `tests/test_hand_registry.py` — lifecycle, state replay

**Action:** Move test blocks to pytest suite.

**Priority:** MEDIUM — Blocks integration testing.

---

## SUMMARY TABLE

| Category | Status | Count | Action |
|----------|--------|-------|--------|
| **Critical Issues** | ✅ NONE | 0 | — |
| **Medium Priority** | 🔧 FIXES NEEDED | 8 | Extract canonical_json, add logging, refactor replay, strengthen approval validation |
| **Low Priority** | 📝 NICE-TO-HAVE | 6 | Type hints, timestamp validation, streaming hash, test migration |
| **Verdict** | ✅ READY FOR PRODUCTION | — | With medium fixes applied |

---

## IMPLEMENTATION CHECKLIST (Before Merge)

### Must-Do (Blocking)
- [ ] Extract `canonical_json()` to shared utility
- [ ] Replace all `print()` with `logging.getLogger()`
- [ ] Add `receipts/` auto-creation in `HandRegistry.__init__()`
- [ ] Strengthen `approval_token` validation (non-empty check)
- [ ] Add `tomli` to `pyproject.toml` dependencies

### Should-Do (Recommended)
- [ ] Refactor `_replay_ledger()` helper to reduce duplication
- [ ] Migrate test blocks to `tests/` pytest suite
- [ ] Add specific exception handling (FileNotFoundError vs RuntimeError vs generic)

### Nice-to-Have (Future)
- [ ] Add `TypeAlias` type hints (Python 3.10+)
- [ ] Implement ledger caching for performance
- [ ] Add hand_id index for faster lookups
- [ ] Streaming hash computation for large prompts
- [ ] Timestamp validation in HandRegistryEvent

---

## FINAL VERDICT

**Status:** ✅ **ARCHITECTURALLY SOUND, IMPLEMENTATION-READY**

The Hand system design is solid:
- ✅ Non-sovereign authority enforced via 4 gates
- ✅ Manifest immutability via hashing
- ✅ Append-only registry with receipt chaining
- ✅ Fail-safe semantics (unknown tools → EXECUTE)

**Issues found are operational/maintenance grade, not architectural.**

**Approval:** Ready to proceed to **Phase 3: Gateway Integration** once these fixes are applied.

---

**Reviewed by:** Claude Code
**Date:** 2026-03-06
**Commit:** 17b1231
**Next Phase:** Integrate gates into `server.py` / `helen_talk.py` for live execution
