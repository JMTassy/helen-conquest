# Oracle Town Inner-Loop Backlog

## Module Enumeration

### CORE MODULES (Decision Authority)

| Module | File | Purpose | Owner Lane |
|--------|------|---------|------------|
| **Mayor RSM** | `core/mayor_rsm.py` | Pure predicate: `decision = f(policy, briefcase, ledger)` | CORE |
| **Policy** | `core/policy.py` | Quorum rules, revocation lists, version tracking | CORE |
| **Crypto** | `core/crypto.py` | Ed25519 signing, canonical JSON, registry-bound receipts | CORE |
| **Key Registry** | `core/key_registry.py` | Key lookup, class binding, allowlist enforcement | CORE |
| **Ledger** | `core/ledger.py` | Append-only, hash-linked attestation chain | CORE |

### INTAKE MODULES (Boundary Protection)

| Module | File | Purpose | Owner Lane |
|--------|------|---------|------------|
| **Intake Guard** | `core/intake_guard.py` | Forbidden field enforcement (K0 invariant) | INTAKE |
| **Schema Validation** | `core/schema_validation.py` | Fail-closed JSON Schema at boundaries | INTAKE |
| **WUL Compiler** | `core/wul_compiler.py` | Natural language → WUL token tree | INTAKE |
| **WUL Validator** | `core/wul_validator.py` | Constitutional invariants on token trees | INTAKE |
| **Translator** | `core/translator.py` | Proposal → WUL bridge (deterministic) | INTAKE |

### FACTORY MODULES (Verification)

| Module | File | Purpose | Owner Lane |
|--------|------|---------|------------|
| **Factory** | `core/factory.py` | Verification tests, attestation emission | FACTORY |
| **Replay** | `core/replay.py` | Determinism verification | FACTORY |
| **Persistence** | `core/persistence.py` | Session storage, audit trails | FACTORY |

### REGISTRY MODULES (Key Management)

| Module | File | Purpose | Owner Lane |
|--------|------|---------|------------|
| **Public Keys** | `keys/public_keys.json` | Operational key registry | REGISTRY |
| **Registry Manifest** | `keys/registry_manifest.json` | Registry metadata + hash | REGISTRY |

### CREATIVE TOWN MODULES (Non-Authoritative)

| Module | File | Purpose | Owner Lane |
|--------|------|---------|------------|
| **Creative Town** | `creative/creative_town.py` | Proposal generation (untrusted) | CT |
| **Idea Publisher** | `idea_publisher.py` | Safe idea card publication | CT |
| **Observer** | `observer.py` | Governance run observation | CT |

---

## INNER-LOOP BACKLOG

### MINOR (Fast, Local, Low-Risk)

#### M1: NO_SHIP Explainability Bundle
**Ticket ID**: MINOR-001
**Scope**: Mayor RSM
**Files**:
- `core/mayor_rsm.py:DecisionRecord` → Add `explain` field
- `schemas/decision_record.schema.json` → Add `explain` object schema
- `tests/test_runs_ABC_phase2.py` → Add explainability tests

**Implementation**:
```python
# mayor_rsm.py:DecisionRecord
@dataclass
class ExplainBundle:
    sorted_blocking_reasons: List[BlockingReason]  # Already sorted
    missing_receipts: List[str]  # Obligations lacking attestations
    expected_classes: Dict[str, List[str]]  # obligation → required classes
    actual_classes: Dict[str, List[str]]  # obligation → present classes
    key_bindings_checked: List[str]  # Keys verified
    registry_hash: str
```

**Acceptance**:
- `explain.json` is byte-stable across 100 replays
- Golden test vector with pinned explain output

**Receipts**: `CI_UNIT`, `REPLAY_DETERMINISM`

---

#### M2: Receipt Coverage Heatmap
**Ticket ID**: MINOR-002
**Scope**: Factory / Observer
**Files**:
- `core/factory.py` → Add `compute_coverage_report()`
- `observer.py` → Add `--coverage` mode
- NEW: `reports/coverage_heatmap.py`

**Implementation**:
```python
def compute_coverage_report(ledger_snapshots: List[Ledger]) -> CoverageReport:
    """
    Returns:
        obligation_name → {
            total_runs: int,
            missing_count: int,
            failing_count: int,
            reason_distribution: Dict[ReasonCode, int]
        }
    Sorted by missing_count descending.
    """
```

**Acceptance**:
- Deterministic output for same ledger snapshot
- One command: `python observer.py --coverage --last=100`

**Receipts**: `CI_RUN`, `ARTIFACT_HASHED`

---

#### M3: Canonical JSON Conformance Gate
**Ticket ID**: MINOR-003
**Scope**: Intake
**Files**:
- `core/intake_guard.py` → Add `lint_canonical_json()`
- `core/schema_validation.py` → Add pre-validation canonicalization check
- NEW: `scripts/lint_proposal.py`

**Implementation**:
```python
def lint_canonical_json(obj: dict) -> Tuple[bool, List[str]]:
    """
    Checks:
    1. Keys sorted lexicographically (recursive)
    2. No duplicate keys
    3. Arrays normalized (no trailing commas in source)
    4. Patterns match schema (pre-Intake)

    Returns:
        (is_canonical, list of violations)
    """
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    actual = json.dumps(obj, separators=(",", ":"))
    if canonical != actual:
        return (False, ["KEY_ORDER_VIOLATION"])
    return (True, [])
```

**Acceptance**:
- Linter output matches Mayor canonicalization rules
- Pre-commit hook integration

**Receipts**: `SCHEMA_VALIDATE`, `CANONICALIZE_TEST`

---

#### M4: Registry Diff Human View
**Ticket ID**: MINOR-004
**Scope**: Registry
**Files**:
- `core/key_registry.py` → Add `diff_registries()`
- NEW: `scripts/registry_diff.py`

**Implementation**:
```python
def diff_registries(old: KeyRegistry, new: KeyRegistry) -> RegistryDiff:
    """
    Returns:
        added_keys: List[KeyInfo]
        revoked_keys: List[KeyInfo]
        allowlist_changes: Dict[key_id, AllowlistDelta]
        class_changes: Dict[key_id, (old_class, new_class)]
        old_hash: str
        new_hash: str
    Sorted deterministically.
    """
```

**Acceptance**:
- Output sorted by key_id
- Includes both registry hashes
- Machine-readable JSON + human-readable Markdown

**Receipts**: `CI_RUN`

---

### SUPERTEAM (Cross-Module Coordination)

#### S1: Quorum Planner
**Ticket ID**: SUPERTEAM-001
**Scope**: Policy + Registry + Factory
**Files**:
- NEW: `core/quorum_planner.py`
- `core/policy.py` → Add `get_all_quorum_rules()`
- `core/key_registry.py` → Add `get_attestors_by_class()`

**Implementation**:
```python
@dataclass
class QuorumPlan:
    obligation_name: str
    required_classes: List[str]
    min_quorum: int
    available_attestors: Dict[str, List[AttestorInfo]]  # class → attestors
    missing_classes: List[str]  # Classes with no available attestors
    feasible: bool
    blocking_reason: Optional[str]

def plan_quorum(
    proposal: ProposalBundle,
    policy: Policy,
    registry: KeyRegistry
) -> List[QuorumPlan]:
    """
    For each obligation in proposal, compute:
    1. Required attestor classes from policy
    2. Available attestors from registry (active, non-revoked)
    3. Feasibility (all classes have ≥1 attestor)
    """
```

**Acceptance**:
- Flags impossible quorums before proposal hits Intake
- Integration test: proposal with missing class → early rejection

**Receipts**: `INTEGRATION_TESTS`, `POLICY_CONSISTENCY_CHECK`

---

#### S2: Key Lifecycle Fire Drill
**Ticket ID**: SUPERTEAM-002
**Scope**: Registry + Factory + Crypto
**Files**:
- NEW: `scripts/key_rotation_drill.py`
- `keys/` → Add rotation artifacts
- `test_vectors/` → Add Run E (key rotation)

**Implementation**:
```bash
# key_rotation_drill.py
1. Generate new keypair (key-2026-02-legal)
2. Add to registry (status=ACTIVE)
3. Revoke old key (key-2026-01-legal → status=REVOKED)
4. Regenerate registry hash
5. Sign attestation with new key
6. Verify old key fails (Run E vector)
7. Verify new key passes (Run F vector)
```

**Acceptance**:
- Scripted run produces deterministic output
- Run E: OLD_KEY → NO_SHIP (KEY_REVOKED)
- Run F: NEW_KEY → SHIP

**Receipts**: `RUN_VECTOR_E`, `RUN_VECTOR_F`, `CRYPTO_TEST`

---

#### S3: Evidence Pack Standard Library
**Ticket ID**: SUPERTEAM-003
**Scope**: Factory
**Files**:
- NEW: `factory/evidence_generators/` directory
- NEW: `factory/evidence_generators/ci_receipt.py`
- NEW: `factory/evidence_generators/sast_receipt.py`
- NEW: `factory/evidence_generators/sbom_receipt.py`
- NEW: `factory/evidence_generators/provenance_receipt.py`

**Implementation**:
```python
# ci_receipt.py
def generate_ci_receipt(
    test_results: TestResults,
    signing_key_id: str,
    private_key: str,
    registry_hash: str
) -> Attestation:
    """
    Produces deterministic CI receipt with:
    - evidence_type: "pytest-junit"
    - evidence_digest: SHA256(canonical(test_results))
    - Signed with Ed25519
    """
```

**Acceptance**:
- Each generator produces schema-valid attestation
- Deterministic digest for same input
- Used by ≥2 modules

**Receipts**: `SEC_SCAN`, `SBOM`, `PROVENANCE`

---

### CREATIVE TOWN (Agentic Quality)

#### CT1: Memory Stream for Proposal Quality
**Ticket ID**: CT-001
**Scope**: Creative Town (soft memory only)
**Files**:
- NEW: `creative/memory_stream.py`
- `creative/creative_town.py` → Add memory retrieval

**Implementation**:
```python
@dataclass
class MemoryEntry:
    proposal_id: str
    timestamp: str
    outcome: str  # "ACCEPTED", "REJECTED"
    blocking_reasons: List[str]
    proposal_type: str
    similarity_embedding: Optional[List[float]]  # For retrieval

class CTMemoryStream:
    def __init__(self, max_entries: int = 1000):
        self.entries: List[MemoryEntry] = []

    def add(self, entry: MemoryEntry):
        """Append-only, FIFO eviction"""

    def retrieve(
        self,
        query_proposal: ProposalBundle,
        k: int = 5,
        recency_weight: float = 0.3
    ) -> List[MemoryEntry]:
        """
        Retrieve top-k relevant memories.
        Score = similarity * (1 - recency_weight) + recency * recency_weight
        """
```

**Acceptance**:
- Measurable decrease in repeated (reason_code, obligation) within 2 weeks
- Retrieval does not touch Mayor (boundary preserved)

**Receipts**: `METRICS_REPORT`

---

#### CT2: Reflection Pre-Intake Transformer
**Ticket ID**: CT-002
**Scope**: Creative Town + Intake
**Files**:
- NEW: `creative/reflection.py`
- `creative/creative_town.py` → Add pre-emit reflection
- NEW: `schemas/preflight_plan.schema.json`

**Implementation**:
```python
def reflect_on_proposal(
    proposal: ProposalBundle,
    memory_stream: CTMemoryStream,
    policy: Policy
) -> PreflightPlan:
    """
    Before emitting proposal:
    1. Query memory: "What failed for similar proposals?"
    2. Identify likely blocking reasons
    3. List required receipts
    4. Flag authority language for removal

    Returns:
        PreflightPlan with required_receipts, likely_blockers, lint_warnings
    """
```

**Acceptance**:
- Proposals include `preflight.plan.json`
- Linter confirms no authority language
- CT_PREFLIGHT_PASS receipt

**Receipts**: `CT_PREFLIGHT_PASS`, `LINT_PASS`

---

#### CT3: Smallville Adversarial Simulation Receipt
**Ticket ID**: CT-003
**Scope**: Factory + Creative Town
**Files**:
- NEW: `factory/simulation_stress_test.py`
- NEW: `creative/adversarial_agents.py`
- NEW: `schemas/simulation_receipt.schema.json`

**Implementation**:
```python
@dataclass
class AdversarialAgent:
    agent_id: str
    goal: str  # "BYPASS_QUORUM", "FORGE_RECEIPT", "INJECT_AUTHORITY"
    strategy: str

def run_simulation(
    policy: Policy,
    registry: KeyRegistry,
    num_agents: int = 25,
    duration_hours: int = 48,
    seed: int = 42
) -> SimulationReceipt:
    """
    Spawn adversarial agents with explicit bypass goals.
    Log all attack attempts + outcomes.

    Returns:
        SimulationReceipt with:
        - seed (for replay)
        - attack_log: List[AttackAttempt]
        - success_count: int (should be 0)
        - failure_distribution: Dict[ReasonCode, int]
        - receipt_hash: SHA256(canonical(attack_log))
    """
```

**Acceptance**:
- Deterministic with fixed seed
- Replayable logs
- Failure produces actionable counterexamples
- Pass produces signed SIMULATION_STRESS_TEST receipt

**Receipts**: `SIMULATION_STRESS_TEST`, `REPLAY_HASH`

---

## ADVERSARIAL TEST VECTORS (E-H)

### Run E: Key Rotation Mid-Flight
**File**: `test_vectors/ledger_runE_key_rotation.json`
**Attack**: Attestation signed with key that was rotated after signing but before Mayor evaluation.
**Expected**: NO_SHIP (KEY_REVOKED)
**Tests**:
- Revocation timestamp < attestation timestamp → KEY_REVOKED
- Rotation discipline enforcement

### Run F: Allowlist Escape
**File**: `test_vectors/ledger_runF_allowlist_escape.json`
**Attack**: Valid key signs obligation outside its allowlist.
**Expected**: NO_SHIP (KEY_OBLIGATION_NOT_ALLOWED)
**Tests**:
- `key-2026-01-legal` signs `security_review` (only allowed `gdpr_consent_banner`)
- Allowlist enforcement

### Run G: Policy Hash Replay Attack
**File**: `test_vectors/ledger_runG_policy_replay.json`
**Attack**: Attestation signed against old policy hash replayed against new policy.
**Expected**: NO_SHIP (POLICY_HASH_MISMATCH)
**Tests**:
- Policy version pinning
- Attestation-policy binding

### Run H: Registry Hash Drift
**File**: `test_vectors/ledger_runH_registry_drift.json`
**Attack**: Attestation signed with registry hash that no longer matches current registry.
**Expected**: NO_SHIP (REGISTRY_HASH_MISMATCH)
**Tests**:
- Registry-bound signatures
- Key registry versioning

---

## ACCEPTANCE CRITERIA MATRIX

| Ticket | Receipts Required | Determinism Check | Golden Test |
|--------|-------------------|-------------------|-------------|
| M1 | CI_UNIT, REPLAY_DETERMINISM | 100 replay | Yes |
| M2 | CI_RUN, ARTIFACT_HASHED | Same ledger | Yes |
| M3 | SCHEMA_VALIDATE, CANONICALIZE_TEST | Canonical match | Yes |
| M4 | CI_RUN | Sorted output | Yes |
| S1 | INTEGRATION_TESTS, POLICY_CONSISTENCY_CHECK | N/A | Yes |
| S2 | RUN_VECTOR_E, RUN_VECTOR_F, CRYPTO_TEST | Scripted | Yes |
| S3 | SEC_SCAN, SBOM, PROVENANCE | Per-generator | Yes |
| CT1 | METRICS_REPORT | N/A | No |
| CT2 | CT_PREFLIGHT_PASS, LINT_PASS | Lint stable | Yes |
| CT3 | SIMULATION_STRESS_TEST, REPLAY_HASH | Seed-based | Yes |

---

## PRIORITY ORDER

1. **M1** (Explainability) → Unblocks CT iteration
2. **M3** (Canonical Lint) → Prevents wasted Mayor cycles
3. **S2** (Key Drill) → Produces Run E/F vectors
4. **Run E-H vectors** → Completes adversarial suite
5. **S1** (Quorum Planner) → Early impossibility detection
6. **CT2** (Reflection) → Self-correcting CT
7. **M2** (Coverage) → Focus Factory investment
8. **M4** (Registry Diff) → Ops visibility
9. **S3** (Evidence Pack) → Standardization
10. **CT1** (Memory Stream) → Long-term CT quality
11. **CT3** (Simulation) → Adversarial stress testing
