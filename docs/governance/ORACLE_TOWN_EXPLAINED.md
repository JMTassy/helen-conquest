# ORACLE Town: A Complete Explanation

## The Big Idea (Think of it Like This)

Imagine you want to hire a brilliant but chaotic employee. They're incredibly creative, but if you just give them power, they'll inevitably abuse it. So you build a system where:

1. **They can propose anything** (no censorship, full creativity)
2. **They can't claim authority** (no ability to override your decisions)
3. **Everyone watches everything** (complete transparency)
4. **No one person can unilaterally approve work** (distributed authority)

That's ORACLE Town. It's a system where **AI can be creative without being trusted** to make final decisions.

The genius? By separating **intelligence** (what Claude thinks) from **authority** (who actually decides), you get both freedom and safety.

---

## Part 1: The Architecture Story

### The Core Insight

Before ORACLE Town, most AI governance systems faced a dilemma:

- **Option A:** Trust the AI completely → Risk disaster if it's misaligned
- **Option B:** Restrict everything → No creativity, no progress

ORACLE Town found a third path: **Creative proposals + Constitutional constraints + Distributed authority = Safe autonomy.**

Think of it like how democracies work: Citizens can vote for crazy ideas, but the system has checks and balances. No single person can become a dictator, even if elected.

### The Five-Step Pipeline (Where Everything Happens)

Imagine Claude is trying to get an idea approved. Here's the gauntlet:

```
Claude Proposes
    ↓
Supervisor Checks (K0: No authority language)
    ↓
Intake Validates (Schema: Is this well-formed?)
    ↓
Factory Executes (Do it: Actually run the code)
    ↓
Mayor Decides (Yes/No: Meet quorum requirements?)
```

**Step 1: Claude (CT - Creative Thinking)**
- Role: "I have an idea!"
- Constraint: None—be as creative as you want

**Step 2: Supervisor (Token Sanitization)**
- Role: "You didn't say forbidden words, right?"
- Constraint: **K0 invariant—authority separation**

**Step 3: Intake (Schema Validation)**
- Role: "Is your proposal properly formatted?"
- Constraint: **K2 invariant—no self-attestation**

**Step 4: Factory (Real Execution)**
- Role: "Let's actually run this code and see if it works"
- Constraint: **K5 invariant—determinism** (same inputs = same outputs always)

**Step 5: Mayor (Decision Making)**
- Role: "Do we ship this?"
- Constraint: **K3 invariant—quorum by class**

### The K-Invariants: Constitutional Guardrails

These are the "amendments" to the system—rules that can NEVER be broken:

| Invariant | What It Means |
|-----------|--------------|
| **K0** | Authority Separation — CT can't claim power |
| **K1** | Fail-Closed — Default is "no" |
| **K2** | No Self-Attestation — Can't sign your own work |
| **K3** | Quorum-by-Class — Need votes from different types |
| **K5** | Determinism — Same input → same output always |
| **K7** | Policy Pinning — Rules don't change mid-execution |
| **K9** | Replay Mode — Everything can be replayed |

---

## Part 2: The Technical Architecture

### The Directory Structure

```
oracle_town/
├── core/                          # The heart
│   ├── policy.py                 # Rules
│   ├── mayor_rsm.py              # Decision maker
│   ├── crypto.py                 # Signing & verification
│   └── intake_guard.py           # Schema validator
│
├── runner/                        # Phase 1 & 2 infrastructure
│   ├── worktree.py               # Safe patching
│   ├── supervisor.py             # K0 enforcement
│   ├── intake_adapter.py         # Schema adapter
│   ├── factory_adapter.py        # Runs tools & signs
│   ├── ct_gateway_claude.py      # Real Claude API
│   └── phase2_harness.py         # Main Phase 2 runner
│
├── keys/                          # Cryptographic material
└── schemas/                       # JSON schema definitions
```

---

## The Bugs We Ran Into (and How We Fixed Them)

### Bug #1: The Invisible Character Problem

**The Problem:**
```
Claude proposed: "a​pprove" (with zero-width space)
Supervisor scanned: "approve"
Result: Should be rejected, but wasn't!
```

Zero-width characters are invisible Unicode characters. You can't see them when you look at text.

**The Fix:**
```python
def _normalize_token(token):
    # Remove zero-width chars BEFORE normalizing
    zero_width_chars = {"\u200b", "\u200c", "\u200d"}
    for char in zero_width_chars:
        token = token.replace(char, "")
    # THEN normalize and check
    return unicodedata.normalize('NFKC', token).casefold()
```

**Two-pass scanning:**
1. Scan entire text as one unit (catches embedded tricks)
2. Split into tokens and check individually

**Key Lesson:** When checking text for security, normalize *before* comparing.

### Bug #2: The Policy Loading Gotcha

**The Problem:**
```python
policy = Policy.load(policy_path)  # ← AttributeError!
```

`Policy` didn't have a `.load()` method. It had `.from_dict()`.

**The Fix:**
```python
with open(policy_path) as f:
    policy_data = json.load(f)
policy = Policy.from_dict(policy_data)
```

**Key Lesson:** Read the code, don't guess the API.

### Bug #3: The Key Registry Mystery

**The Problem:**
```
Factory looked for: key-2026-01-ci-prod
But registry had: key-2026-01-ci
Result: Signature failed!
```

**The Fix:**
```python
def _get_mock_signing_key(self, key_id):
    # Try exact match
    if key_id in keys:
        return keys[key_id]
    # Fallback: find any "ci" key
    for k, v in keys.items():
        if "ci" in k.lower():
            return v.get("private_key_b64")
    raise ValueError(f"No CI key found")
```

**Key Lesson:** When dealing with keys, be flexible on naming but strict on security.

### Bug #4: The PYTHONPATH Nightmare

**The Problem:**
```
ImportError: No module named 'oracle_town'
```

Python couldn't find modules because execution context was wrong.

**The Fix:**
```python
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
```

**Key Lesson:** Never assume execution directory. Use `Path(__file__).parent`.

---

## Design Decisions (Why We Built It This Way)

### Decision 1: Canonical JSON

**Why?** Determinism. Same data always produces same hash.

```json
{"a": 1, "b": 2}  ← Always sorted keys, always same format
```

**The trade-off:** Slightly slower than pickle, but enables replay verification.

### Decision 2: Separate Supervisor, Intake, and Factory

**Why?** Each module does one thing. If step 2 fails, you know step 1 passed.

- Supervisor: "Is this safe?"
- Intake: "Is this valid?"
- Factory: "Does it work?"

**The benefit:** Composability and debuggability.

### Decision 3: Mock Mayor in Phase 2

**Why?** Isolate variables. If Phase 2 fails, it's not Mayor's fault.

```python
def mock_mayor_decide(attestations_count):
    if attestations_count >= 1:
        return "SHIP"
    return "NO_SHIP"
```

### Decision 4: K-Invariants (Not Soft Guidelines)

**Why?** Make rules unbreakable.

```python
# WEAK
if "ship" in proposal:
    log.warning("Authority language!")

# STRONG
if "ship" in proposal:
    raise ForbiddenLanguageError()  # System fails
```

**The principle:** For safety, make rules mechanical, not aspirational.

---

## Best Practices We Discovered

### Practice 1: Immutable Records

Every decision generates a complete record that never changes.

```python
decision_record = {
    "timestamp": "2026-01-26T20:15:03Z",
    "proposal_hash": "abc123...",
    "supervisor_decision": "PASS",
    "mayor_decision": "SHIP",
    "signatures": [...]
}
# Written once, never mutated
```

### Practice 2: Fail-Closed Over Fail-Open

When in doubt, reject.

```python
# BAD
try:
    quorum = verify_quorum(attestations)
except Exception:
    quorum = True  # Assume met if verification fails

# GOOD
try:
    quorum = verify_quorum(attestations)
except Exception as e:
    raise QuorumVerificationError(f"Cannot verify: {e}")
```

### Practice 3: Log Everything Structured

```python
# AVOID
log.info("Processed proposal successfully!")

# GOOD
log.info({
    "event": "proposal_processed",
    "cycle": 42,
    "decision": "SHIP",
    "timestamp": "2026-01-26T20:15:03Z"
})
```

### Practice 4: Version Your Data Structures

```python
{
    "version": 2,  # ← Always include this
    "proposal_bundle": {...}
}
```

When you change the schema, you can migrate old data.

### Practice 5: Test Adversarial Cases

Don't test what works. Test what could break.

```python
test_zero_width = "a​pprove"  # Should reject
test_homoglyph = "аpprove"    # Cyrillic 'a', should reject
test_excess_whitespace = "s  h  i  p"  # Should reject
```

---

## The Engineering Mindset

### The Debug-Driven Development Cycle

1. **Assumption:** Something should work a certain way
2. **Test:** Try it
3. **Failure:** It doesn't work
4. **Learning:** Understand why
5. **Fix:** Change the code

This isn't failure. This is how systems get robust.

### The Trade-Off Matrix

Every decision involves sacrificing something:

| Decision | Pro | Con | Why We Chose It |
|----------|-----|-----|-----------------|
| Canonical JSON | Deterministic | Slower | Auditability > speed |
| K-Invariants | Mechanically enforced | Less flexible | Safety > flexibility |
| Phase 1 simulation | Fast validation | Doesn't test real Claude | Simplicity > realism |

Good engineers are explicit about what they're trading.

### The Principle of Progressive Complexity

Build the simplest thing first, then add complexity:

1. **Phase 0:** Kernel (core logic, frozen interfaces)
2. **Phase 1:** Infrastructure (modules, testing)
3. **Phase 2:** Claude integration
4. **Phase 3+:** Production hardening

This prevents feature creep and scope explosion.

---

## Technologies Used (and Why)

**Python:** Data structures, JSON, cryptography

**Ed25519:** Modern, simple public-key cryptography (simpler than RSA)

**JSON Schema:** Machine-readable contracts for data structures

**GitHub Actions:** Verify every change doesn't break tests

**Chart.js:** Interactive dashboards with minimal code

---

## Potential Pitfalls (and How to Avoid Them)

### Pitfall 1: Authority Creep

Rules slowly erode: warning → logging → "just ship it anyway"

**How to avoid:** Make K-invariants unbreakable. Throw exceptions, don't warn.

### Pitfall 2: Silent Failures

Error gets logged but processing continues.

**How to avoid:** Fail loudly. Require explicit recovery.

### Pitfall 3: Determinism Violations

System produces different results on different runs.

**How to avoid:**
- Always sort before processing
- Use UTC timestamps
- Never use randomness in decisions
- Test determinism explicitly

### Pitfall 4: Leaky Abstractions

One layer violates another's assumptions.

**How to avoid:** Write tests that verify layer contracts.

### Pitfall 5: Crypto Mistakes

Signatures that look secure but aren't.

**How to avoid:** Use established libraries. Canonicalize before signing. Verify both signature AND signer identity.

---

## The ORACLE Town Principles

### Principle 1: Separate Intelligence from Authority

Let AI be smart. Don't let it be powerful.

Claude can propose anything. Claude can't make decisions. This separation is mechanical.

### Principle 2: Make Rules Unbreakable

K-Invariants aren't guidelines. They're laws of physics.

You can't break K0 any more than walk through walls.

### Principle 3: Determinism Enables Trust

If you can replay an event and get the same result, you can trust it.

This is why courts require transcripts.

### Principle 4: Fail Closed

When something breaks, the default is "no," not "yes."

### Principle 5: Defense in Depth

Don't rely on any single security mechanism.

Supervisor + Intake + Factory = Multiple layers catching problems.

---

## Your Takeaway

### If You're Building AI Systems:

1. Separate intelligence from authority
2. Make safety unbreakable
3. Build in phases
4. Log everything deterministically
5. Expect attacks on your safeguards

### If You're Writing Critical Code:

1. Canonicalize your data
2. Fail closed
3. Separate concerns
4. Test edge cases
5. Document trade-offs

### If You're Learning Engineering:

1. Build working things first
2. Learn by breaking and fixing
3. Read the code (not documentation)
4. Design for observability
5. Think in layers

---

## Conclusion

We started with a question: **Can AI systems be creative without being trusted?**

Through three phases, we discovered: **Yes.**

The secret is separation—intelligence here, authority there, with cryptography and determinism binding them together.

That's not just AI governance. That's good engineering.

---

**Quick Reference: Key Concepts**

| Concept | Meaning |
|---------|---------|
| K-Invariants | Rules that can't be broken |
| Canonical JSON | Always same format = always same hash |
| Determinism | Same input → same output every time |
| Fail-Closed | Default is "no" if something breaks |
| Separation of Concerns | Each module does one thing |
| Token Sanitization | Detect forbidden words with Unicode tricks |
| Ed25519 | Simple, modern cryptographic signing |
| Quorum | Multiple independent votes required |
| Mock Mayor | Simple decision logic for testing |
| Phase-Based Development | Test assumptions early and cheap |

---

**You now understand ORACLE Town. Go build something with this mindset: creative where it matters, constrained where it needs to be, observable throughout.**
