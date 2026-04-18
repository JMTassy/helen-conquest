# FOR_ORACLE_TOWN.md

## Oracle Town Governance Kernel — Implementation Reference

**Version:** 1.0.0 (Phase-2 Ready)
**Last Updated:** 2026-01-25

---

## 1. What the System Is

Oracle Town is a governance kernel where **text has zero authority**. The only authorization predicate is:

```
SHIP = Mayor(policy, briefcase, ledger)
```

Everything upstream can generate ideas, but nothing upstream can authorize action.

**Core invariant:** No receipts ⇒ NO_SHIP.

---

## 2. Authority Separation

| Component | Function | Authority |
|-----------|----------|-----------|
| **Creative Town (CT)** | Generate proposals | NONE |
| **Swarm Sandbox** | Parallel task execution (planner + workers) | NONE |
| **Oracle Intake** | Reject-first validation, emit briefcase | NONE |
| **Factory** | Run tools/tests, produce signed receipts | NONE |
| **Ledger** | Store attestations | NONE |
| **Mayor** | Decide SHIP/NO_SHIP | EXCLUSIVE |

**Rule:** No component other than Mayor may decide.

---

## 3. Data Flow (Canonical Pipeline)

```
1. CT / Swarm outputs:
   - proposal_bundle.json
   - ct_run_manifest.json
   - evidence_plan.json (plan only, no claims)

2. Intake outputs:
   - briefcase.json (obligations: required classes, min quorum, severity)
   - ct_boundary_digest pin

3. Factory outputs:
   - ledger.json (attestations with evidence digests)
   - evidence artifacts on disk (hashed)

4. Mayor outputs:
   - decision_record.json (SHIP/NO_SHIP, blocking reasons, decision_digest)
```

---

## 4. Reject-First Semantics (Intake)

Intake is deterministic and fail-closed, in strict order:

1. JSON parse
2. Schema validate
3. Forbidden field/token scan
4. Budget enforcement
5. Boundary digest computation

**Reason Code Precedence (frozen):**

| Priority | Code | Description |
|----------|------|-------------|
| 1 | `CT_REJECTED_SCHEMA_INVALID` | Schema validation failed |
| 2 | `CT_REJECTED_BUDGET_VIOLATION` | Exceeds budget caps |
| 3 | `CT_REJECTED_AUTHORITY_ATTEMPT` | Authority keys/phrases detected |
| 4 | `CT_REJECTED_FORBIDDEN_FIELDS` | Generic forbidden tokens |
| 5 | `CT_REJECTED_DUPLICATE_BLOCKS` | Persuasion patterns detected |

---

## 5. Quorum-by-Class Rule

An obligation is satisfied iff:

- All required attestor classes are present (distinct)
- Signatures verify
- Keys are known, active, not revoked
- Policy pin matches
- Evidence digests exist
- Min quorum is met **by class**, not by raw count

This is why Run A/B/C work as adversarial proofs.

---

## 6. Swarm Sandbox

Swarm is a throughput layer, not governance.

**Allowed:**
- Produce artifacts (schemas, proposals, plans, patches)
- Parallel task execution

**Forbidden:**
- SHIP/NO_SHIP language
- Satisfaction claims
- Receipts/attestations
- Confidence/ranking

**Guardrails (G1-G5):**
1. Schema validation
2. Forbidden token scan (deterministic lexicon + normalization)
3. Duplicate-block detection (eligible handoff files only)
4. Budget caps
5. Stable hashing (Swarm Boundary Digest)

**Swarm Reason Codes:**
- `SWARM_REJECT_SCHEMA_INVALID`
- `SWARM_REJECT_BUDGET_VIOLATION`
- `SWARM_REJECT_FORBIDDEN_AUTHORITY`
- `SWARM_REJECT_DUPLICATE_BLOCKS`
- `SWARM_REJECT_NONDETERMINISTIC_HASH`

---

## 7. Forbidden Authority Lexicon

**Authority-attempt keys** (structural smuggling):
```
ship, verdict, decision, recommend, confidence, score, rank,
certified, satisfied, attestation, receipt, proof, approved, verified
```

**Authority-attempt phrases** (semantic escalation):
```
is satisfied, obligation satisfied, all tests passed, should ship,
ready to ship, safe to deploy, certified, verified, approved
```

**Normalization function:**
```python
def normalize(text: str) -> str:
    import unicodedata
    normalized = unicodedata.normalize('NFKC', text.lower())
    return ' '.join(normalized.split())
```

---

## 8. Phase-2 Cryptographic Binding

### 8.1 Requirements

- Ed25519 verification of attestations
- Pinned public key registry
- Registry hash pinning inside policy
- Signature over canonical message (byte-stable)
- Revocation is retroactive
- Mayor remains pure/deterministic

### 8.2 Enforcement Order (Fail-Fast)

Per attestation, check in order:

1. Policy hash pin
2. Registry hash pin
3. Key exists
4. Class binding matches
5. Key active / not revoked
6. Scope checks (optional)
7. Signature verifies on canonical message
8. Then quorum counting

### 8.3 Canonical JSON

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

---

## 9. Canonical Reason Codes (Mayor)

| Code | Description |
|------|-------------|
| `REGISTRY_HASH_MISMATCH` | Registry pin doesn't match |
| `KEY_UNKNOWN` | Signing key not in registry |
| `KEY_CLASS_MISMATCH` | Key class doesn't match attestor class |
| `KEY_REVOKED` | Key was revoked |
| `KEY_SCOPE_VIOLATION` | Key scope doesn't cover obligation |
| `KEY_POLICY_VIOLATION` | Key violates policy constraints |
| `SIGNATURE_INVALID` | Ed25519 signature verification failed |
| `POLICY_HASH_MISMATCH` | Attestation policy pin doesn't match run |
| `QUORUM_NOT_MET` | Required classes not all present |
| `EVIDENCE_MISSING` | Evidence digest not provided |

---

## 10. Adversarial Proof Runs

| Run | Condition | Expected |
|-----|-----------|----------|
| **A** | Missing required class (LEGAL) | NO_SHIP, QUORUM_NOT_MET |
| **B** | Revoked key used | NO_SHIP, KEY_REVOKED |
| **C** | Valid quorum, valid signatures | SHIP |

**Critical property:** Same proposals can yield different outcomes solely due to receipts.

---

## 11. ORACLE_MINOR (Constitutional Maintenance)

ORACLE_MINOR is proposal-only. It may:
- Analyze historical runs
- Propose improvements
- Specify risks and required receipts
- Specify rollback conditions

It may NOT:
- Decide
- Execute tools
- Self-modify
- Mutate judge/policy/kernels
- Use confidence/ranking/recommendations

---

## 12. CI Obligations for Adversarial Validation

| Obligation | Description |
|------------|-------------|
| `obl_no_authority_escalation` | No "ship", "should", "confidence", "safe", etc. |
| `obl_kernel_immutability` | No Mayor/policy changes unless governed |
| `obl_receipt_explicitness` | Required receipts declared by class |
| `obl_rollback_completeness` | Measurable rollback triggers |
| `obl_replay_determinism` | Canonicalization + dedup + stable hashes |

---

## 13. Attack Vectors to Test

1. Persuasive ship attempt
2. Ranking smuggling
3. Kernel edit attempts
4. Receipt vagueness
5. Self-modification proposals
6. Duplication/replay poisoning
7. Heuristic replacement ("confidence threshold instead of receipts")

**Control pass case:** Neutral proposal with explicit receipts and measurable rollback.

---

## 14. Key Files

| File | Purpose |
|------|---------|
| `oracle_town/cli.py` | Main CLI |
| `oracle_town/core/mayor_rsm.py` | Mayor decision logic |
| `oracle_town/core/intake_guard.py` | Intake validation |
| `oracle_town/core/crypto.py` | Cryptographic utilities |
| `oracle_town/core/policy.py` | Policy enforcement |
| `oracle_town/core/replay.py` | Determinism verification |
| `oracle_town/VERIFY_ALL.sh` | Full verification script |
| `oracle_town/schemas/*.json` | Schema definitions |
| `oracle_town/test_vectors/` | Adversarial test vectors |
| `ORACLE_TOWN_SWARM_SANDBOX_SPEC.md` | Swarm specification |

---

## 15. Commands

```bash
# Setup
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run single claim
python3 oracle_town/cli.py "Your claim text"

# Run verification
bash oracle_town/VERIFY_ALL.sh

# Run CI checks
python3 ci_run_checks.py

# Run test vectors
python3 oracle_town/test_vectors/run_vector_tests.py
```

---

## 16. Engineering Principles

1. **Reason precedence must be specified** if tests assert exact codes
2. **Canonicalization is a security primitive** (dedup + canonical JSON)
3. **Mutable "frozen" configs are a trap** — use immutable mappings
4. **Grammar constraints must be tag-sensitive** (prevent logic smuggling)
5. **Defense in depth** — test Swarm guardrails and Intake bypass vectors separately

---

**This document is normative for Oracle Town implementation.**
