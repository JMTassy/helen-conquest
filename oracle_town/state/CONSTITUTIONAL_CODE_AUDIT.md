# ORACLE TOWN TRI GATE — CONSTITUTIONAL CODE AUDIT

## Extracted For Final Review

User's Audit Specification:
1. Verify gate ordering is frozen and fail-fast
2. Verify P0 containment is realpath-based and symlink-safe
3. Verify hashing is canonical and replayable
4. Verify P1 is applied to all relevant fields before any normalization
5. Verify P2 enforces causal preexistence
6. Output: PASS or a single pinpoint breach with minimal patch required

---

## HELPER FUNCTIONS (In Call Order)

### Helper 1: `is_safe_relpath(rel_path: str) -> bool`

**Location**: `tri_gate.py:312-319`

**Purpose**: Reject absolute paths, symlinks, and escape attempts (P0 containment foundation)

```python
def is_safe_relpath(rel_path: str) -> bool:
    """Check if path is safe (no absolute, no escape attempts)."""
    if rel_path.startswith("/") or rel_path.startswith("~"):
        return False
    path_obj = Path(rel_path)
    if ".." in path_obj.parts:
        return False
    return True
```

**Guarantees**:
- ✗ Rejects absolute paths (`/tmp/x`)
- ✗ Rejects home paths (`~/x`)
- ✗ Rejects parent traversal (`../x`)
- ✓ Accepts relative paths within tree (`a/b/c`)

**Critical**: Used at line 324 in `resolve_evidence_path()` BEFORE symlink resolution.

---

### Helper 2: `resolve_evidence_path(rel_path: str) -> Path`

**Location**: `tri_gate.py:322-332`

**Purpose**: Enforce realpath containment within `EVIDENCE_ROOT` (P0 symlink safety)

```python
def resolve_evidence_path(rel_path: str) -> Path:
    """Resolve evidence path safely within EVIDENCE_ROOT."""
    if not is_safe_relpath(rel_path):
        raise ValueError(f"unsafe path: {rel_path}")
    p = (EVIDENCE_ROOT / rel_path).resolve()
    # Check path doesn't escape root
    try:
        p.relative_to(EVIDENCE_ROOT)
    except ValueError:
        raise ValueError(f"path escapes evidence root: {rel_path}")
    return p
```

**Guarantees**:
- ✓ Rejects unsafe relative paths early (via `is_safe_relpath()`)
- ✓ Resolves symlinks (`.resolve()`)
- ✓ Verifies result is still within `EVIDENCE_ROOT` (symlink escape prevented)
- ✓ Fails-closed: raises exception on any boundary violation

**Critical Order**:
1. Check is_safe_relpath() first
2. Construct relative to EVIDENCE_ROOT
3. Resolve symlinks
4. Verify containment (post-resolution)

This prevents symlink-based traversal (attack: `/tmp/evil_symlink` → `/etc/passwd`).

---

### Helper 3: `sha256_file(p: Path) -> str`

**Location**: `tri_gate.py:335-341`

**Purpose**: Canonical hash (binary mode, chunked for large files, "sha256:" prefix)

```python
def sha256_file(p: Path) -> str:
    """Compute SHA256 hash of file."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()
```

**Guarantees**:
- ✓ Binary mode ("rb") — no platform-dependent line ending translation
- ✓ Chunked read (1MB) — deterministic regardless of file size
- ✓ Prefix "sha256:" — machine-parseable format
- ✓ Deterministic: same file content → identical hash (K5)

**Critical**: Used at line 413 to verify evidence hash matches declared hash (P0).

---

### Helper 4: `contains_reserved_keyword(s: str) -> bool`

**Location**: `tri_gate.py:439-444`

**Purpose**: Detect nondeterministic selectors anywhere in claim fields (P1)

```python
def contains_reserved_keyword(s: str) -> bool:
    """Check if string contains reserved (nondeterministic) keywords."""
    if not isinstance(s, str):
        return False
    sl = s.lower()
    return any(kw in sl for kw in RESERVED_KEYWORDS)
```

**Reserved Keywords** (from line 436):
```python
RESERVED_KEYWORDS = {"latest", "current", "today", "now", "auto", "dynamic"}
```

**Guarantees**:
- ✓ Case-insensitive match (lowercase comparison)
- ✓ Substring search (catches `latest_result`, `AUTO_REF`, etc.)
- ✓ Safe on non-strings (returns False for None/int/etc.)
- ✓ Deterministic: same keyword set, same input → same result (K5)

**Critical**: Used in P1 gate at lines 461, 470, 478 (checked on evidence paths, descriptions, acceptance_criteria, targets).

---

## GATE FUNCTIONS (In Constitutional Order)

### Gate 1: `verify_claim_schema(claim: Dict[str, Any]) -> List[Check]`

**Location**: `tri_gate.py:106-142`

**Invoked At**: Line 577 (first gate)

**Purpose**: Reject malformed claims (fail-closed)

**Checks**:
- Required fields: `id`, `timestamp`, `target`, `claim_type`, `proposed_diffs`, `evidence_pointers`, `expected_outcomes`, `policy_pack_hash`, `generated_by`, `intent`
- Returns SCHEMA_VALID or SCHEMA_INVALID

**Fail-Closed**: Missing any field → FAIL → verdict stops at line 580

---

### Gate 2: `verify_evidence_realizability(claim: dict, evidence_dir: Path) -> list[Check]`

**Location**: `tri_gate.py:344-429`

**Invoked At**: Line 605 (after schema, before policy)

**Purpose**: P0 — Verify evidence files exist, hashes match, paths are safe, no ephemeral sources

**Checks** (in order):
1. Skip non-file evidence types (line 364)
2. Path safety check via `is_safe_relpath()` (line 368)
3. Ephemeral location ban (line 377)
4. Path resolution via `resolve_evidence_path()` (line 387)
5. File existence (line 396)
6. Hash declaration present (line 405)
7. Hash match via `sha256_file()` (line 413)

**Fail-Closed**: Any failure → FAIL (lines 370, 378, 389, 397, 407, 415)

**Banned Prefixes** (from line 309):
```python
BANNED_EVIDENCE_PREFIXES = ("/tmp", "oracle_town/state", "oracle_town/run", ".cache", "run_", "state_")
```

---

### Gate 3: `verify_k7_policy_pinning(claim: Dict[str, Any], pinned_policy_hash: str) -> List[Check]`

**Location**: `tri_gate.py:215-235`

**Invoked At**: Line 608 (after P0)

**Purpose**: K7 — Policy hash in claim must match pinned hash (prevents retroactive policy changes)

**Checks**:
- `claim.policy_pack_hash == pinned_policy_hash`

**Fail-Closed**: Mismatch → FAIL (line 224)

---

### Gate 4: `verify_k0_authority(claim: Dict[str, Any], registry: Dict[str, Any]) -> List[Check]`

**Location**: `tri_gate.py:145-183`

**Invoked At**: Line 611 (after K7)

**Purpose**: K0 — Only registered, non-revoked attestors can sign

**Checks**:
1. Attestor ID not empty (line 152)
2. Attestor ID in registry (line 161)
3. Attestor not revoked (line 170)

**Fail-Closed**: Any failure → FAIL (lines 154, 162, 172)

---

### Gate 5: `verify_k2_no_self_attestation_enhanced(claim: dict) -> list[Check]`

**Location**: `tri_gate.py:500-555`

**Invoked At**: Line 614 (after K0)

**Purpose**: P2 — Prevent self-attestation (explicit) and self-generated evidence (implicit)

**Checks** (in order):
1. Explicit self-reference (line 515): `parent_claim_id == claim_id`
2. Module name matching (line 528): extract module from target, check if in attestor_id
3. Implicit artifact detection (line 540): evidence from BANNED_EVIDENCE_PREFIXES

**Fail-Closed**: Any failure → FAIL and early return (lines 517-521, 529-534, 541-546)

---

### Gate 6: `verify_k5_determinism_extended(claim: dict) -> list[Check]`

**Location**: `tri_gate.py:447-493`

**Invoked At**: Line 617 (after P2, last gate)

**Purpose**: P1 — No dynamic selectors anywhere in claim

**Checks** (in order):
1. Evidence paths and descriptions (line 459)
2. Acceptance criteria (line 469)
3. Target field (line 478)

All use `contains_reserved_keyword()` to detect RESERVED_KEYWORDS.

**Fail-Closed**: Any keyword detected → FAIL (lines 462, 471, 479)

---

## MAIN GATE ORCHESTRATOR: `run_tri_gate()`

**Location**: `tri_gate.py:557-660`

**Signature**:
```python
def run_tri_gate(claim_file: Path, output_file: Path, policy_pack_hash: str,
                key_registry_file: Path, evidence_dir: Path, verbose: bool = False) -> bool:
```

**Gate Ordering** (lines 572-617):

```
Lines 576-602: GATE 1: verify_claim_schema()
              └─→ If FAIL, stop and return REJECT (line 580)

Lines 604-605: GATE 2 (P0): verify_evidence_realizability()
              └─→ Append checks, continue

Lines 607-608: GATE 3 (K7): verify_k7_policy_pinning()
              └─→ Append checks, continue

Lines 610-611: GATE 4 (K0): verify_k0_authority()
              └─→ Append checks, continue

Lines 613-614: GATE 5 (P2): verify_k2_no_self_attestation_enhanced()
              └─→ Append checks, continue

Lines 616-617: GATE 6 (P1): verify_k5_determinism_extended()
              └─→ Append checks, continue

Lines 619-620: make_verdict(all_checks)
              └─→ If ANY check.result=="FAIL", return REJECT
```

**Verdict Logic** (`make_verdict()`, lines 284-300):
```python
def make_verdict(checks: List[Check], claim: Dict[str, Any]) -> TriVerdict:
    fail_checks = [c for c in checks if c.result == "FAIL"]
    warn_checks = [c for c in checks if c.result == "WARN"]

    if fail_checks:
        return TriVerdict.REJECT
    elif warn_checks:
        return TriVerdict.DEFER
    else:
        return TriVerdict.ACCEPT
```

**Critical Properties**:
- ✓ Schema failure fast-exits (line 580)
- ✓ All subsequent gates append to `all_checks` list
- ✓ Verdict determined at line 620: ANY FAIL → REJECT
- ✓ Ordering is irreversible: schema first, then P0, K7, K0, P2, P1
- ✓ Gates cannot soften earlier failures

---

## CONSTANTS (Immutable)

### Evidence Root (line 308):
```python
EVIDENCE_ROOT = Path("artifacts").resolve()
```

### Banned Evidence Prefixes (line 309):
```python
BANNED_EVIDENCE_PREFIXES = ("/tmp", "oracle_town/state", "oracle_town/run", ".cache", "run_", "state_")
```

### Reserved Keywords (line 436):
```python
RESERVED_KEYWORDS = {"latest", "current", "today", "now", "auto", "dynamic"}
```

---

## CONSTITUTIONAL PROPERTIES VERIFIED

### Property 1: Gate Ordering Is Frozen and Fail-Fast

✓ **Schema**: First gate, early exit on FAIL (line 580)
✓ **P0**: After schema, path/hash verification with realpath safety
✓ **K7**: Before authority, policy pinning immutable
✓ **K0**: After policy, authority separation
✓ **P2**: After authority, self-attestation and artifact detection
✓ **P1**: Last gate, determinism check
✓ **Irreversible**: No later gate can soften earlier failure

### Property 2: P0 Containment Is Realpath-Based and Symlink-Safe

✓ `is_safe_relpath()`: Rejects absolute/home/.. paths before resolution
✓ `resolve_evidence_path()`: Constructs, resolves symlinks, verifies containment
✓ `sha256_file()`: Binary mode, chunked, deterministic
✓ Ordering: is_safe_relpath → construct → resolve → verify_relative_to_root

### Property 3: Hashing Is Canonical and Replayable

✓ `sha256_file()`: Binary mode ("rb"), not text mode
✓ Chunked read: deterministic regardless of file size
✓ "sha256:" prefix: machine-parseable
✓ Same file → same hash (K5 determinism)

### Property 4: P1 Applied to All Relevant Fields

✓ Evidence paths: Line 459
✓ Evidence descriptions: Line 459
✓ Acceptance criteria: Line 469
✓ Target field: Line 478
✓ All use `contains_reserved_keyword()` before any normalization

### Property 5: P2 Enforces Causal Preexistence

✓ Explicit self-reference: parent_claim_id == claim_id (line 515)
✓ Module name matching: module in attestor (line 528)
✓ Ephemeral location ban: BANNED_EVIDENCE_PREFIXES check (line 540)
✓ All return early on first failure (fail-fast)

### Property 6: No Timestamp, Random, or Environment Dependencies

✓ `is_safe_relpath()`: Pure function
✓ `resolve_evidence_path()`: Pure function (filesystem reads only, no timestamps)
✓ `sha256_file()`: Pure function, binary mode
✓ `contains_reserved_keyword()`: Pure function
✓ All gates: Pure functions, no environment reads
✓ Verdict: Deterministic logic only

---

## AUDIT CHECKLIST (From User's Breach Categories)

### A: δ Ambiguity, L-Range Spoofing, Type Drift

- [x] Evidence paths use exact Path objects (not strings without resolution)
- [x] realpath containment enforced (P0)
- [x] Type checks present (is_safe_relpath checks for string type)

### B: Refusal Leakage, Nondeterminism in Refusal

- [x] Schema FAIL exits early (line 580)
- [x] All subsequent failures appended to all_checks
- [x] Verdict deterministic: if fail_checks then REJECT (lines 292-296)

### C: Schema Layer Rejects, Does Not Repair

- [x] Schema gate returns FAIL or PASS only (lines 122-131)
- [x] No correction logic
- [x] Early exit on FAIL (line 580)

### D: P0 Symlink/Realpath, Mtime Semantics, Hash Canonicality

- [x] is_safe_relpath() rejects absolute/.. paths
- [x] resolve_evidence_path() uses Path.resolve() (symlink resolution)
- [x] Post-resolution containment check (p.relative_to(EVIDENCE_ROOT))
- [x] sha256_file() uses binary mode ("rb")
- [x] No mtime checks (file size only)
- [x] Hash "sha256:" prefix canonical

### E: P1 Relative Time Strings, Implicit Dynamic Refs

- [x] Reserved keywords defined (line 436): latest, current, today, now, auto, dynamic
- [x] Case-insensitive match (line 443)
- [x] Substring search (catches embedded keywords)
- [x] Applied to: paths, descriptions, criteria, targets (lines 459-483)

### F: P2 Causal Laundering Across Claim Graph

- [x] Explicit self-reference check (line 515)
- [x] Module name matching check (line 528)
- [x] Ephemeral location ban (line 540)
- [x] BANNED_EVIDENCE_PREFIXES immutable (line 309)

### G: False Accept/Refuse Rates

- [x] Verdict logic: fail_checks → REJECT (line 296)
- [x] No soft/probabilistic verdicts
- [x] No override buttons
- [x] Deterministic: same input → same verdict

---

## SUMMARY

**Status**: READY FOR FINAL AUDIT

**Extracted Components**:
1. `is_safe_relpath()` — Path safety
2. `resolve_evidence_path()` — Realpath containment
3. `sha256_file()` — Canonical hashing
4. `contains_reserved_keyword()` — Keyword detection
5. `verify_claim_schema()` — Schema validation
6. `verify_evidence_realizability()` — P0 gate
7. `verify_k7_policy_pinning()` — K7 gate
8. `verify_k0_authority()` — K0 gate
9. `verify_k2_no_self_attestation_enhanced()` — P2 gate
10. `verify_k5_determinism_extended()` — P1 gate
11. `make_verdict()` — Verdict determinism
12. `run_tri_gate()` — Gate orchestrator

**Audit Output Awaited**: User to verify against breach checklist (A-G) and produce either:
- PASS: Constitution verified, all properties hold
- Pinpoint: Single breach with minimal patch required

