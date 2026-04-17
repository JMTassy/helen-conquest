# ORACLE TOWN Kernel Contracts (for Runner Use)

## Purpose

This document specifies the EXACT signatures and contracts that runner modules must use when calling core kernel functions. No guessing. No adapting. One canonical interface per function.

---

## 1. Policy Interface

**Import:**
```python
from oracle_town.core.policy import Policy
```

**Load function:**
```python
@staticmethod
def load(path: str) -> Policy:
    """Load policy from JSON file (policy.schema.json)."""
    # Returns Policy with policy_hash = sha256:...
```

**Contract:**
- Input: file path (must exist, must be valid JSON, must match policy.schema.json)
- Output: Policy dataclass with all required fields
- `policy.policy_hash` is ALWAYS set to `sha256:HEX64`
- May raise: FileNotFoundError, json.JSONDecodeError, ValueError (schema mismatch)

**Used by:** factory_adapter, mayor_adapter, context_builder

---

## 2. KeyRegistry Interface

**Import:**
```python
from oracle_town.core.key_registry import KeyRegistry
```

**Constructor:**
```python
def __init__(self, registry_path: str):
    """Load key registry from JSON file."""
    # registry_hash = sha256(canonical JSON of registry)
    # stores public keys indexed by key_id
```

**Verify method:**
```python
def verify_ed25519(
    signing_key_id: str,
    canonical_message_bytes: bytes,
    signature_b64: str
) -> bool:
    """Verify Ed25519 signature."""
    # Returns True iff signature valid
    # May raise: KeyError (key_id not found), ValueError (invalid base64)
```

**Contract:**
- registry_hash is sha256:HEX64
- Key IDs are strings (e.g., "key-2026-01-ci-prod")
- Public keys are Ed25519 format
- Signatures are base64-encoded 64-byte values
- May raise: KeyError if key_id not in registry

**Used by:** factory_adapter (signing), mayor_adapter (verification)

---

## 3. Cryptographic Utilities

**Import:**
```python
from oracle_town.core.crypto import (
    build_canonical_message,
    canonical_json_bytes,
    verify_ed25519
)
```

**canonical_json_bytes:**
```python
def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    """Convert object to canonical JSON bytes for signing.

    Rules:
    - Keys sorted lexicographically
    - No whitespace
    - UTF-8 encoding
    - Deterministic (same object → same bytes)
    """
    # Returns UTF-8 encoded canonical JSON
```

**build_canonical_message:**
```python
def build_canonical_message(
    run_id: str,
    claim_id: str,
    obligation_name: str,
    attestor_id: str,
    attestor_class: str,
    policy_hash: str,
    evidence_digest: str,
    policy_match: int,
    key_registry_hash: Optional[str] = None
) -> Dict[str, Any]:
    """Build canonical message for signature."""
    # Returns dict ready for canonical_json_bytes
```

**verify_ed25519:**
```python
def verify_ed25519(
    public_key: bytes,
    canonical_message_bytes: bytes,
    signature_bytes: bytes
) -> bool:
    """Verify Ed25519 signature."""
    # Returns True iff valid
```

**Contract:**
- canonical_json_bytes is deterministic (same input → same output)
- Signature verification is strict (no lenience)
- All fields in canonical message MUST match signed attestation

**Used by:** factory_adapter (signing), mayor_adapter (verification)

---

## 4. IntakeGuard Interface

**Import:**
```python
from oracle_town.core.intake_guard import (
    IntakeGuard,
    IntakeDecision,
    RejectionCode
)
```

**evaluate method:**
```python
def evaluate(self, proposal_bundle: Dict[str, Any]) -> IntakeDecision:
    """Validate proposal bundle against schema and forbidden fields.

    Returns:
        IntakeDecision with:
        - decision: "PASS" | "REJECT"
        - reason_code: RejectionCode enum value
        - detail: str explanation
        - normalized_bundle: (if PASS) normalized dict
    """
```

**Contract:**
- Input: proposal_bundle as dict (must be JSON-parseable)
- Output: IntakeDecision (frozen dataclass)
- reason_code is ALWAYS one of the enum values (no strings)
- normalized_bundle is only present if decision == "PASS"
- May raise: ValueError only for non-JSON dicts (fail closed)

**Rejection codes:**
- `CT_REJECTED_FORBIDDEN_FIELDS`: contains forbidden language
- `CT_REJECTED_SCHEMA_INVALID`: doesn't match proposal.schema.json
- `CT_REJECTED_BUDGET_VIOLATION`: exceeds patch/proposal size limits
- `CT_REJECTED_MALFORMED_JSON`: not valid JSON

**Used by:** intake_adapter

---

## 5. MayorRSM Interface

**Import:**
```python
from oracle_town.core.mayor_rsm import MayorRSM, DecisionRecord
```

**Constructor:**
```python
def __init__(
    policy: Policy,
    registry: KeyRegistry,
    briefcase: Dict[str, Any],
    ledger: Dict[str, Any]
):
    """Initialize Mayor with constitutional data."""
    # Stores all refs; no side effects
```

**decide method:**
```python
def decide(
    run_id: str,
    claim_id: str
) -> DecisionRecord:
    """Pure function: (policy, registry, briefcase, ledger) -> decision.

    Returns:
        DecisionRecord with:
        - decision: "SHIP" | "NO_SHIP"
        - reason_code: frozen code (e.g., "KEY_REVOKED", "QUORUM_MISSING")
        - decision_record_hash: sha256:HEX64
    """
```

**Contract:**
- Pure function: same inputs → identical outputs
- NO I/O, NO environment reads, NO timestamps in logic
- May raise: ValueError (invariant violation, fail closed)
- reason_code is ALWAYS a frozen kernel code, never free text

**Invariants enforced:**
- K0: Authority Separation (only registered attestors)
- K1: Fail-Closed (default NO_SHIP)
- K2: No Self-Attestation (agent ≠ attestor)
- K3: Quorum-by-Class (min N distinct attestor classes)
- K5: Determinism (same inputs → same outputs)

**Used by:** mayor_adapter

---

## 6. Attestation Schema Contract

**File:** `oracle_town/schemas/attestation.schema.json`

**Required fields (in signature):**
- `run_id` (str)
- `claim_id` (str)
- `obligation_name` (str, pattern: `^[a-z0-9_]{3,64}$`)
- `attestor_id` (str)
- `attestor_class` (enum: CI_RUNNER, SECURITY, LEGAL, DOMAIN_OWNER, RELEASE_MANAGER, MOCK_FACTORY)
- `policy_hash` (pattern: `^sha256:[a-fA-F0-9]{64}$`)
- `key_registry_hash` (pattern: `^sha256:[a-fA-F0-9]{64}$` or null)
- `evidence_digest` (pattern: `^sha256:[a-fA-F0-9]{64}$`)
- `signing_key_id` (str)
- `signature` (pattern: `^ed25519:[A-Za-z0-9+/=]+$`)
- `policy_match` (enum: 0, 1)
- `timestamp` (ISO 8601)

**Contract:**
- Attestation validates against attestation.schema.json
- Signature is base64(64-byte Ed25519 signature)
- No attestation without evidence_digest (NO_RECEIPT = NO_SHIP)
- policy_hash and key_registry_hash are immutable per run

---

## 7. DecisionRecord Schema Contract

**File:** `oracle_town/schemas/decision_record.schema.json`

**Required fields:**
- `run_id` (str)
- `claim_id` (str)
- `decision` (enum: SHIP, NO_SHIP)
- `reason_code` (frozen kernel code)
- `decision_record_hash` (pattern: `^sha256:[a-fA-F0-9]{64}$`)
- `timestamp` (ISO 8601)

**Contract:**
- decision_record_hash = sha256(canonical JSON of all fields except hash itself)
- Immutable per run (append-only ledger)
- reason_code determines remediation roadmap (if applicable)

---

## Implementation Rules

### Rule 1: Reuse. Don't Duplicate.

If crypto.py has `build_canonical_message`, use it everywhere. Don't build your own.

Example ✓:
```python
from oracle_town.core.crypto import build_canonical_message, canonical_json_bytes

message = build_canonical_message(
    run_id="run_001",
    claim_id="claim_001",
    obligation_name="test_pass",
    ...
)
msg_bytes = canonical_json_bytes(message)
```

Example ✗:
```python
# Don't hand-build or use different function
message = {
    "run_id": "run_001",
    "claim_id": "claim_001",
    ...
}
msg_bytes = json.dumps(message, sort_keys=True).encode()  # Wrong! Different canonical form.
```

### Rule 2: Fail Closed. Never Silent.

If a required field is missing or invalid, raise an exception with a frozen code name.

Example ✓:
```python
if not evidence_digest or not evidence_digest.startswith("sha256:"):
    raise ValueError("EVIDENCE_DIGEST_MISSING", detail="...")
```

Example ✗:
```python
# Silent fallback
evidence_digest = evidence_digest or "sha256:0000..."  # NO!
```

### Rule 3: Signature is Immutable

Once signed, the canonical message's bytes are final. Never re-encode or reformat.

Example ✓:
```python
msg_bytes = canonical_json_bytes(message)
signature_bytes = ed25519_sign(private_key, msg_bytes)
signature_b64 = base64.b64encode(signature_bytes).decode()
attestation["signature"] = f"ed25519:{signature_b64}"
```

Example ✗:
```python
# Different encoding breaks determinism
msg_str = json.dumps(message)  # Might differ from canonical form!
```

### Rule 4: Registry and Policy Hashes

Both MUST be pre-computed and immutable per run. Never compute them on demand or cache them across runs.

Example ✓:
```python
policy = Policy.load("policy.json")
registry = KeyRegistry("keys/public_keys.json")
attestation["policy_hash"] = policy.policy_hash
attestation["key_registry_hash"] = registry.registry_hash
```

Example ✗:
```python
# Wrong: computing hash during attestation
attestation["policy_hash"] = sha256(policy_json).hex()  # Might differ!
```

---

## Testing

Each interface is tested via:
1. Unit tests in `oracle_town/core/`
2. Phase-2 test vectors (A–H in `oracle_town/test_vectors/`)
3. Runner integration tests (in `oracle_town/runner/tests/`)

**Rule: If kernel tests pass but runner fails, the bug is in runner, not kernel.**

