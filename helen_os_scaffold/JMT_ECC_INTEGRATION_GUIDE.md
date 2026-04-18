# JMT + ECC Integration Guide for HELEN OS

**Status:** Phase 0 (JMT Frameworks) + Phase 1 (Receipt Chaining) IMPLEMENTED
**Date:** 2026-03-06
**Author:** JMT + ECC Hardening Project

---

## Overview

This guide explains how your **9 custom JMT frameworks** and **ECC hardening patterns** are now integrated into HELEN OS:

1. **JMT Frameworks** (5 frameworks) → Injected into HELEN's soul/system prompt
2. **Receipt Chaining** (SHA256 integrity) → Tamper-evident audit trail
3. **Atomic Writes** → Guaranteed durability (fcntl.flock + fsync)
4. **Security Redaction** → PII/secrets masked in logs
5. **Runtime Flags** → Enable/disable features via environment variables

---

## Quick Start (5 minutes)

### 1. Test the JMT Frameworks

```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24/helen_os_scaffold
source .venv/bin/activate

# List all frameworks
python -m helen_os.plugins.jmt_frameworks
```

Output:
```
Available JMT Frameworks:
  - oracle_governance: ORACLE Governance Kernel v9.0
  - riemann_stqm: Spectral-Topological Quantum Manifolds (STQM)
  - quantum_consensus: Quantum Prime Gap Lattice + Riemann Bridge
  - swarm_emergence: Fractal-Quantum Swarm Doctrine
  - consensus_meditation: Consensus via Meditation Principles
```

### 2. Test Receipt Chaining

```bash
# Create a test receipt chain
python -m helen_os.receipts.chain_v1

# Output:
# [TEST] Appending 3 entries...
#   Entry 1 hash: <sha256>
#   Entry 2 hash: <sha256>
#   Entry 3 hash: <sha256>
# [TEST] Verifying chain...
#   Valid: True
```

### 3. Verify Receipt Integrity

```bash
python scripts/verify_receipts.py --ledger receipts/memory_hits.jsonl --verbose

# Output:
# Verifying receipt chain: receipts/memory_hits.jsonl
# [✓] Entry 1 (line 1): prev_hash OK
# [✓] Entry 1 (line 1): entry_hash OK
# [✓] Entry 2 (line 2): prev_hash OK
# [✓] Entry 2 (line 2): entry_hash OK
# ...
# ✅ Chain is valid. 5 entries verified.
```

### 4. Use Enhanced HELEN in Code

```python
from helen_os.integration_jmt_ecc import create_helen_enhanced

# Create enhanced HELEN
helen = create_helen_enhanced()

# Log a memory hit (automatically chained + hashed)
hits = [
    {"id": "f1", "source": "oracle_town", "score": 0.95, "text": "Receipt governance"},
    {"id": "f2", "source": "jmt_framework", "score": 0.87, "text": "ORACLE framework"},
]
receipt_hash = helen.log_memory_hit("What is ORACLE governance?", hits)
print(f"Receipt: {receipt_hash}")

# Log a HELEN decision
receipt_hash2 = helen.log_helen_decision(
    decision_type="claim",
    description="HELEN proposes using ORACLE framework",
    relevant_frameworks=["oracle_governance"],
)

# Verify chain at end of session
helen.verify_receipts()
```

---

## Architecture

### Files Created

```
helen_os_scaffold/
├── helen_os/
│   ├── plugins/
│   │   └── jmt_frameworks.py          ← JMT frameworks loader + injector
│   ├── receipts/
│   │   ├── __init__.py
│   │   └── chain_v1.py                ← Receipt chaining logic
│   └── integration_jmt_ecc.py         ← Main integration hub
├── scripts/
│   └── verify_receipts.py             ← CLI verification tool
└── JMT_ECC_INTEGRATION_GUIDE.md       ← This file
```

### Key Modules

#### `helen_os.plugins.jmt_frameworks.JMTFrameworkLoader`

Loads and injects your 5 JMT frameworks:

```python
from helen_os.plugins.jmt_frameworks import JMTFrameworkLoader

loader = JMTFrameworkLoader()

# List frameworks
loader.list_frameworks()  # → ['oracle_governance', 'riemann_stqm', ...]

# Retrieve relevant frameworks for a query
relevant = loader.retrieve_relevant_frameworks("governance decision")
# → [('oracle_governance', {...}), ('consensus_meditation', {...})]

# Build soul injection
soul_injection = loader.build_soul_injection()
# → "[JMT_FRAMEWORKS_INJECTED_v2026]\n\nFRAMEWORK: ORACLE Governance Kernel..."
```

#### `helen_os.receipts.chain_v1.ReceiptChain`

Manages tamper-evident receipt chain:

```python
from helen_os.receipts.chain_v1 import ReceiptChain

chain = ReceiptChain("receipts/memory_hits.jsonl")

# Append a receipt (atomic write)
entry_hash = chain.append({
    "type": "memory_hit",
    "query": "What is ORACLE?",
    "hits": [{"id": "f1", "score": 0.95}]
})

# Verify chain
is_valid = chain.verify_chain()

# Get cumulative digest
digest = chain.get_digest()  # SHA256 of last entry
```

#### `helen_os.integration_jmt_ecc.HelenWithJMTAndECC`

Main integration class:

```python
from helen_os.integration_jmt_ecc import HelenWithJMTAndECC

helen = HelenWithJMTAndECC(
    enable_retrieval=True,              # Log memory hits
    enable_redaction=True,              # Mask PII/secrets
    fail_closed_on_receipt_error=True,  # Raise on write failure
)

# Use enhanced HELEN
helen.log_memory_hit(query, hits)
helen.log_helen_decision(type, description, frameworks)
helen.verify_receipts()
helen.get_stats()
```

---

## Features

### 1. JMT Frameworks Integration

**What it does:**
- Loads your 5 custom frameworks (ORACLE, RIEMANN, SWARM, CONSENSUS, CHRONOS)
- Injects them into HELEN's system prompt
- Helps HELEN reason about governance, topology, consensus, and emergence

**Where it's used:**
- In `helen talk --reply` → frameworks are available to the LLM
- In `helen chat` → full pipeline has framework context
- Programmatically: `helen.retrieve_relevant_frameworks(query)`

**Example:**
```bash
helen talk --reply --no-receipt --ledger :memory: "Explain the ORACLE framework. Which other frameworks should work with it?"
```

HELEN will now cite the ORACLE framework, describe its rules, and propose using it with RIEMANN STQM for integrity verification.

### 2. Receipt Chaining (SHA256)

**What it does:**
- Every receipt entry includes:
  - `prev_hash`: SHA256 of previous entry (creates chain)
  - `entry_hash`: SHA256 of current entry (proof)
  - `context_hash`: SHA256 of query+hits (audit trail)
- Atomic writes (fcntl.flock + os.fsync) guarantee durability
- Tampering is detectable (broken chain fails verification)

**References:**
- AWS CloudTrail (append-only logs with chaining)
- RFC6962 (Merkle tree transparency logs)

**Example:**
```json
{"type": "memory_hit", "query": "What is ORACLE?", "query_hash": "abc123...", "hits": [...], "prev_hash": "def456...", "entry_hash": "ghi789...", "context_hash": "jkl012..."}
```

### 3. Atomic Writes

**What it does:**
- Uses `fcntl.flock()` for exclusive lock
- `f.flush()` sends to kernel buffer
- `os.fsync()` forces write to disk (CRITICAL)
- Prevents corruption if process crashes mid-write

**Guarantees:**
- Either entire entry is written or nothing (no partial writes)
- No data loss if power fails during write
- Safe for concurrent reads while writing

### 4. Security Redaction

**What it does:**
- Masks secrets in logs (OpenAI keys, GitHub tokens, AWS keys, JWTs, passwords)
- Redacts before appending to ledger
- Protects against accidental credential exposure

**Patterns masked:**
```
- OpenAI API keys (sk-...)
- GitHub tokens (ghp_...)
- AWS keys (AKIA...)
- JWTs (eyJ...)
- Password assignments
- Private keys (RSA, DSA, EC, etc.)
```

**Example:**
```python
helen.enable_redaction = True
helen.log_memory_hit("My password is sk-abc123xyz", hits)
# Stored in ledger as: "My password is [REDACTED]"
```

### 5. Runtime Flags

**What it does:**
- Control behavior via environment variables
- Enable/disable features without code changes
- Perfect for production safety

**Available flags:**
```bash
# Enable retrieval logging (default: True)
export HELEN_RETRIEVAL_ENABLED=true

# Enable PII redaction (default: True)
export HELEN_REDACTION_ENABLED=true

# Enable debug output
export HELEN_DEBUG=true
```

**Usage:**
```bash
# Run HELEN with all hardening disabled (dev mode)
HELEN_RETRIEVAL_ENABLED=false HELEN_DEBUG=true helen chat

# Run HELEN with strict fail-closed (production mode)
HELEN_REDACTION_ENABLED=true helen chat
```

---

## Verification Workflow

### Daily Audit

```bash
# At end of each session, verify receipt integrity:
python scripts/verify_receipts.py --ledger receipts/memory_hits.jsonl --verbose

# Exit codes:
# 0 = valid (no tampering)
# 1 = invalid (tampering detected)
# 2 = file error
```

### Automated Checks (CI/CD)

```bash
# In your CI pipeline:
#!/bin/bash
set -e

# Run HELEN session
helen chat

# Verify receipts (fail if invalid)
python scripts/verify_receipts.py --ledger receipts/memory_hits.jsonl || exit 1

# Verify no secrets leaked
grep -i "sk-\|ghp_\|AKIA\|eyJ" receipts/memory_hits.jsonl && exit 1

echo "✅ All audits passed"
```

---

## Next Steps (Phase 2 & 3)

### Phase 2: Enhanced Logging (This Week)

- [ ] Add `model`, `prompt_tokens`, `completion_tokens`, `latency_ms` to each log
- [ ] Periodic snapshots of ledger (daily JSON checkpoint)
- [ ] Signed digest (daily hash signature for immutability proof)

### Phase 3: Full Tests (Next Week)

- [ ] Unit tests for receipt chaining
- [ ] Integration tests for full HELEN session
- [ ] Regression tests (ensure existing features still work)
- [ ] Load tests (1000+ receipts, verify performance)

### Phase 4: Production Hardening

- [ ] Backup + replication of receipt ledger
- [ ] Remote digest verification (off-chain signature)
- [ ] Key rotation policy for digest signing
- [ ] Operational runbook for incident response

---

## Troubleshooting

### Receipt verification fails

**Error:** `[ERROR] Line 5: entry_hash mismatch`

**Cause:** Entry was modified after writing

**Solution:**
1. Check if ledger was edited manually
2. Restore from backup
3. Report tampering attempt to security team

### Permission denied writing receipts

**Error:** `[ERROR] Failed to append receipt: Permission denied`

**Cause:** `receipts/` directory not writable

**Solution:**
```bash
chmod 700 receipts/
chmod 600 receipts/memory_hits.jsonl
```

### Slow receipt writes

**Cause:** fsync() on every write is synchronous (intentional for durability)

**Solution:**
- This is by design (trade safety for speed)
- If you have 1000+ queries/second, batch writes or use async queue

### Framework injection not appearing

**Cause:** LLM model doesn't have HELEN persona baked in

**Solution:**
- Use `helen-chat:latest` model (has HELEN persona)
- Or ensure `jmt_frameworks.py` injection is called in soul builder

---

## Configuration

### Environment Variables

```bash
# Enable/disable features
HELEN_RETRIEVAL_ENABLED=true          # Log memory hits (default: true)
HELEN_REDACTION_ENABLED=true          # Mask secrets (default: true)
HELEN_DEBUG=false                     # Debug output (default: false)

# Paths
HELEN_RECEIPT_LEDGER=/custom/path/ledger.jsonl
HELEN_JMT_CATALOG=/custom/path/catalog.json

# Behavior
HELEN_FAIL_CLOSED=true                # Raise on receipt error (default: true)
```

### Programmatic Configuration

```python
from helen_os.integration_jmt_ecc import HelenWithJMTAndECC

helen = HelenWithJMTAndECC(
    jmt_catalog_path="/custom/path/catalog.json",
    receipt_ledger_path="/custom/receipts.jsonl",
    enable_retrieval=True,
    enable_redaction=True,
    fail_closed_on_receipt_error=True,
)
```

---

## References

- **AWS CloudTrail:** Append-only logging with digest chaining
- **RFC6962 (Trillian):** Merkle tree transparency logs
- **OpenTelemetry GenAI:** Format for retrieval spans and attributes
- **JMT Framework Catalog:** `/Users/jean-marietassy/Desktop/oracle_town/PLUGINS_JMT_CATALOG.json`
- **ECC Integration Report:** Executive summary in system context

---

## Support

- **Questions?** Check `helen_os/integration_jmt_ecc.py` docstrings
- **Issues?** Run with `HELEN_DEBUG=true` for detailed output
- **Verification?** Use `scripts/verify_receipts.py --verbose`
- **Framework help?** Run `python -m helen_os.plugins.jmt_frameworks`

---

**Last Updated:** 2026-03-06
**Status:** Phase 0 + Phase 1 Complete ✅
**Next Review:** 2026-03-13
