# Oracle Town: Audit Manifest System

**Purpose:** Make "which evidence was reviewed" machine-verifiable and replayable.

**Status:** ✅ Live and tested

---

## The Problem

**Narrative claim:** "I reviewed runA, runB, and runC evidence. The 5 breakthroughs are valid."

**Problem:** How do we know which files were actually reviewed? What if someone claims to have reviewed evidence but only skimmed one file?

**Solution:** Deterministic audit manifest with SHA256 hashes of all reviewed artifacts.

---

## How It Works

### Step 1: Generate Audit Manifest

```bash
python3 scripts/make_audit_manifest.py --run runA_no_ship_missing_receipts
```

**Output:**
```
✅ Manifest generated: receipts/oracle_town_audit_manifest.json
   Artifacts audited: 6
   Manifest SHA256: f166b3d35737e28e...
```

**What gets included:**
- All run artifacts (decision_record.json, policy.json, hashes.json, ledger.json, briefcase.json)
- Evidence report (ORACLE_TOWN_EMULATION_EVIDENCE.md)
- Bibliothèque submissions (oracle_town/memory/bibliotheque/**)

### Step 2: Manifest Hash (Canonical JSON)

The manifest itself is hashed using deterministic JSON serialization:

```python
canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
manifest_sha256 = sha256(canonical)
```

This means:
- Same manifest → same SHA256
- Any artifact modification → manifest hash changes
- Replayable: `sha256(manifest_json) == recorded_hash`

### Step 3: Verify Integrity

```bash
python3 scripts/verify_audit_manifest.py receipts/oracle_town_audit_manifest.json
```

**Output:**
```
✅ Manifest hash verified
✅ MANIFEST INTEGRITY VERIFIED
   6 artifacts checked
   All hashes match
```

---

## Commands Reference

### Generate Manifest

```bash
# For specific run
python3 scripts/make_audit_manifest.py --run runA_no_ship_missing_receipts

# For all runs
python3 scripts/make_audit_manifest.py

# Custom output path
python3 scripts/make_audit_manifest.py --output my_audit.json
```

### Verify Manifest

```bash
python3 scripts/verify_audit_manifest.py receipts/oracle_town_audit_manifest.json
```

### In Month 1 Workflow

**Week 1: Review runA**
```bash
python3 scripts/make_audit_manifest.py --run runA_no_ship_missing_receipts --output receipts/week1_runA.json
# Review work
python3 scripts/verify_audit_manifest.py receipts/week1_runA.json
git add receipts/week1_runA.json && git commit -m "audit: week 1 reviewed runA"
```

Repeat for weeks 2, 3, 4 with different runs.

---

## Getting Started

### Generate Your First Manifest

```bash
mkdir -p receipts
python3 scripts/make_audit_manifest.py --run runA_no_ship_missing_receipts
python3 scripts/verify_audit_manifest.py receipts/oracle_town_audit_manifest.json
git add receipts/oracle_town_audit_manifest.json
git commit -m "audit: initial manifest for runA evidence"
```

---

## Manifest Schema

```json
{
  "schema_version": "oracle_town_audit_manifest_v1",
  "generated_at_epoch": 1769702080,
  "generated_at_iso": "2026-01-29T15:54:40Z",
  "run_filter": "runA_no_ship_missing_receipts",
  "items_count": 6,
  "items": [
    {
      "id": "evidence/ORACLE_TOWN_EMULATION_EVIDENCE.md",
      "path": "/full/path/to/file",
      "size_bytes": 12910,
      "sha256": "b87fa435a9433bab...",
      "mtime_epoch": 1769636635
    }
  ],
  "manifest_sha256": "f166b3d35737e28e..."
}
```

---

## What Gets Captured

Each artifact is recorded with:

```json
{
  "id": "run/decision_record.json",
  "path": "/path/to/file",
  "size_bytes": 646,
  "sha256": "69681040...",
  "mtime_epoch": 1769186235
}
```

**Files included:**
- `decision_record.json` — the decision + blocking reasons
- `policy.json` — governance rules (K3 quorum, etc.)
- `hashes.json` — decision_digest, policy_hash
- `ledger.json` — all attestations (append-only)
- `briefcase.json` — context + obligations
- `ORACLE_TOWN_EMULATION_EVIDENCE.md` — the 5 breakthroughs
- Bibliothèque submissions (if present)

---

## Why This Matters for Month 1

### Without Manifest

```
"I reviewed runA evidence"
→ Unverifiable (which files? how long?)
→ Can't detect modification
→ Not reproducible
```

### With Manifest

```
"I reviewed runA evidence"
+ receipts/week1_runA.json (6 files, hashes recorded)
+ git commit (timestamp + author)
+ verify script (✅ all hashes match)
→ Verifiable (exact files listed)
→ Modification detected (hash change)
→ Reproducible (same files, same hash)
```

---

## Status

✅ Scripts live: `scripts/make_audit_manifest.py`, `scripts/verify_audit_manifest.py`
✅ Example manifest created: `receipts/oracle_town_audit_manifest.json`
✅ Verification passed: 6 artifacts, all hashes match
✅ Ready for Month 1 workflow

