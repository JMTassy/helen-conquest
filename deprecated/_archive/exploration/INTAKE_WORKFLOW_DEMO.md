# Bibliothèque Intake Workflow: Demonstration

**Status:** Ready for user content submission

This document demonstrates the complete intake workflow for knowledge integration, using the mathematical content mentioned as an example.

## The Constitutional Workflow

### Phase 1: User Provides Content (Option A: Chat Paste)

User pastes mathematics paper into chat:
```
User: "Here's a certification proof for Riemann hypothesis bounds..."
[Paste LaTeX or markdown content]
```

**I respond:** "Content received. Saving to inbox..."
```bash
# Created: oracle_town/inbox/REQ_001/certificate_proof.tex
```

### Phase 2: Generate Intake Manifest (Receipts Only)

I run:
```bash
python3 scripts/bibliotheque_manifest.py
```

**Output:** `receipts/bibliotheque_intake_manifest.json`
```json
{
  "schema_version": "bibliotheque_intake_manifest_v1",
  "generated_at_epoch": 1769705400,
  "generated_at_iso": "2026-01-29T18:30:00Z",
  "inbox_dir": "oracle_town/inbox",
  "items_count": 1,
  "items": [
    {
      "path": "REQ_001/certificate_proof.tex",
      "size_bytes": 12847,
      "sha256": "f4a7c9e2b1d8a3f6e5c9b2a7d4f1e8c3b6a9d2e5f8c1b4a7d0e3f6a9c2",
      "mtime_epoch": 1769705300
    }
  ],
  "manifest_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a"
}
```

**What this proves:**
- Exactly 1 file was offered (REQ_001/certificate_proof.tex)
- File size: 12,847 bytes
- Content hash: deterministic SHA256 of raw bytes
- Timestamp: when manifest was generated
- Manifest integrity: manifest_sha256 proves no tampering

### Phase 3: I Propose Integration PR (Not Autonomous)

I create a branch and prepare diff:
```bash
git checkout -b intake/REQ_001_math_proof
```

**Normalize and add metadata:**
```bash
# Created: oracle_town/memory/bibliotheque/math_proofs/001/
#   ├── source.tex (copy of raw file)
#   ├── metadata.json (request_id, source_hash, etc.)
#   └── digest.sha256 (verification hash)
```

**metadata.json:**
```json
{
  "request_id": "REQ_001",
  "request_type": "MATH_DRAFT",
  "source_path": "oracle_town/inbox/REQ_001/certificate_proof.tex",
  "source_sha256": "f4a7c9e2b1d8a3f6e5c9b2a7d4f1e8c3b6a9d2e5f8c1b4a7d0e3f6a9c2",
  "intake_manifest_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a",
  "title": "Certification Proof for Riemann Hypothesis Bounds",
  "author": "Jean Marie Tassy Simeoni",
  "submitted_date": "2026-01-29T18:30:00Z",
  "status": "PROPOSED"
}
```

**Create PR on GitHub (or in git as draft):**
```
Title: Intake: K5 Determinism Proof (REQ_001)

Body:
Intake manifest: receipts/bibliotheque_intake_manifest.json
Manifest hash: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a

Items:
- REQ_001: K5 Determinism Proof
  - Format: .tex
  - Size: 12,847 bytes
  - SHA256: f4a7c9e2b1d8a3f6e5c9b2a7d4f1e8c3b6a9d2e5f8c1b4a7d0e3f6a9c2

CI Checks:
- ✅ Manifest hash verified
- ✅ No secrets detected (gitleaks)
- ✅ Content normalized
- ✅ Metadata schema valid

Ready for tribunal review.
```

### Phase 4: CI Validates (Mandatory Receipts)

CI runs:
```bash
# 1. Verify manifest integrity
python3 scripts/verify_audit_manifest.py receipts/bibliotheque_intake_manifest.json
# Output: ✅ MANIFEST INTEGRITY VERIFIED (1 items, all hashes match)

# 2. Check for secrets
gitleaks detect --source=oracle_town/memory/bibliotheque/
# Output: ✅ No secrets found

# 3. Validate schema
python3 -m jsonschema --instance oracle_town/memory/bibliotheque/math_proofs/001/metadata.json \
  oracle_town/schemas/bibliotheque_metadata.schema.json
# Output: ✅ Schema valid

# 4. Determinism check (normalize same file twice, compare hashes)
python3 scripts/verify_intake_normalization.py oracle_town/inbox/REQ_001/ oracle_town/memory/bibliotheque/math_proofs/001/
# Output: ✅ Determinism verified (same input → same output)
```

**CI posts to PR:**
```
✅ All checks passed (4/4)
- Manifest integrity: VERIFIED
- Secret scan: CLEAR
- Schema validation: VALID
- Determinism: CONFIRMED

Ready for tribunal merge approval.
```

### Phase 5: Tribunal Decides (Human Review)

**You review the PR:**
- Is this mathematical knowledge valuable?
- Are the sources trustworthy?
- Should it be integrated into Bibliothèque?

**If approved:**
```bash
# Merge the PR
git merge origin/intake/REQ_001_math_proof
```

**Result on main:**
```bash
git log --oneline -3
# abc1234 Merge PR #456: Intake K5 proof (manifest: a1b2c3d4e5...)
# def5678 Intake: normalize K5 proof + metadata (REQ_001)
# ghi9012 Intake: record manifest (1 item in inbox)
```

All changes are:
- Traceable to specific PR
- Auditable (manifest hash in commit)
- Reversible (git history)
- Replayable (same input → same normalization)

---

## Key Constitutional Guarantees

✅ **Bot does NOT write to main** — Only through PR (human merge decision)
✅ **Receipts are mandatory** — SHA256 hashes of all files before integration
✅ **No self-attestation** — Bot proposes, CI validates, tribunal decides
✅ **Full audit trail** — All receipts preserved in git history
✅ **Determinism verified** — Same file → same output (replayable)

---

## How to Submit Content

### Option A: Paste into This Chat

```
User: "Here's math content..."
[Paste text, LaTeX, markdown, or code]

I respond:
1. Save to oracle_town/inbox/REQ_NNN/
2. Generate manifest
3. Show proposed PR diff
4. Wait for your merge approval
```

### Option B: Local Folder Upload

```
You: Place file in oracle_town/inbox/REQ_NNN/

I respond:
1. Run: python3 scripts/bibliotheque_manifest.py
2. Generate manifest
3. Show proposed PR diff
4. Wait for your merge approval
```

---

## Status

✅ Infrastructure ready:
- `oracle_town/inbox/` directory exists (untrusted buffer)
- `REQUESTS.json` defines what town needs (4 open requests)
- `scripts/bibliotheque_manifest.py` generates receipts
- Workflow documented (constitutional model)

⏳ **Awaiting user content:**
- Option A: Paste content into chat
- Option B: Place files in local inbox folder
- Option C: Both (some items via chat, some via folder)

Once content arrives, workflow executes: inbox → manifest → PR → CI → tribunal → merge.

