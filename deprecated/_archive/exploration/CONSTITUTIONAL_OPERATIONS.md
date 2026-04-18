# Constitutional Operations: The Correct Model

**Status:** Fixing autonomous mode to respect tribunal + receipts model

**The Problem I Introduced:**
- Claimed "autonomous mode" with direct commits to main
- Bypassed PR + receipts entirely
- Violated the tribunal/constitutional model I defined
- Mixed narrative with capability (claimed things worked that didn't follow the rules)

**The Fix:** Everything through PR + CI attestation. No exceptions.

---

## The Constitutional Model (Correct)

```
User Input (via inbox or chat)
    ↓
[Town Bot] Proposes PR (branch, diff, receipts)
    ↓
[CI] Attests (hashes, secrets scan, schema validation)
    ↓
[Tribunal] Reviews (human decision)
    ↓
[Merge] Only if receipts valid + tribunal approval
    ↓
[Main] Updated with full audit trail
```

**What this prevents:**
- Bot cannot write to main directly ✅
- All changes are reviewable ✅
- CI receipts are mandatory ✅
- Human has final decision ✅
- Full replayable audit trail ✅

---

## Bibliothèque Intake (Correct Implementation)

### Step 1: User Provides Content (to Inbox)

**Inbox is untrusted buffer:**
```
oracle_town/inbox/
├── REQUESTS.json          (what town is asking for)
├── REQ_001/               (user drops content here)
│   └── my_proof.tex
├── REQ_002/
│   └── old_code.py
└── REQ_003/
    └── research.md
```

**You upload files here (or paste into chat, we save to inbox).**

### Step 2: Generate Intake Manifest (Receipts)

```bash
python3 scripts/bibliotheque_manifest.py
```

**Output:** `receipts/bibliotheque_intake_manifest.json`
```json
{
  "schema_version": "bibliotheque_intake_manifest_v1",
  "generated_at_iso": "2026-01-29T17:00:00Z",
  "inbox_dir": "oracle_town/inbox",
  "items_count": 3,
  "items": [
    {
      "path": "REQ_001/my_proof.tex",
      "size_bytes": 1234,
      "sha256": "abc123...",
      "mtime_epoch": 1769702400
    }
  ],
  "manifest_sha256": "def456..."
}
```

**This proves:**
- Exactly what was offered
- When it was offered
- No tampering (SHA256 immutable)

### Step 3: Bot Proposes Integration PR (Not Autonomous)

**Bot's workflow (to be implemented):**
1. Read intake manifest
2. Validate each file (schema, no secrets, determinism)
3. Create normalized copies → `oracle_town/memory/bibliotheque/`
4. Generate metadata (request_id, source hash, parsed summary)
5. **Create draft PR** (not merge to main)
   - Branch: `intake/REQ_001_REQ_002_REQ_003`
   - Diff shows: normalized files + metadata
   - Commit message: links manifest hash + request IDs
6. Post PR (human review)

**PR content looks like:**
```
Title: Intake: K5 proof + legacy code + research (3 items)
Body:
  Intake manifest: receipts/bibliotheque_intake_manifest.json
  Manifest hash: def456...

  Items:
  - REQ_001: K5 proof (sha256: abc123...)
  - REQ_002: legacy code (sha256: bcd234...)
  - REQ_003: research (sha256: cde345...)

  CI checks:
  - ✅ Manifest hash matches
  - ✅ No secrets detected
  - ✅ Schema valid
  - ✅ Determinism: normalized → same output

  Ready for tribunal review.
```

### Step 4: CI Attests (Mandatory Receipts)

**CI validates:**
```bash
# 1. Manifest integrity
python3 scripts/verify_audit_manifest.py receipts/bibliotheque_intake_manifest.json

# 2. Normalization determinism
python3 scripts/verify_intake_normalization.py \
  oracle_town/inbox/ \
  oracle_town/memory/bibliotheque/

# 3. Schema validation
python3 -m jsonschema --instance oracle_town/memory/bibliotheque/*/metadata.json \
  oracle_town/schemas/bibliotheque_metadata.schema.json

# 4. Secret scan
gitleaks detect --source=oracle_town/memory/bibliotheque/
```

**If all pass:** CI posts ✅ to PR
**If any fail:** CI posts ❌, blocks merge

### Step 5: Tribunal Merges (Human Decision)

**You (tribunal) decide:**
- Is this knowledge valuable?
- Are the sources trustworthy?
- Should it be integrated?

**Only if approved:**
```bash
# Merge the PR (git records everything)
git merge pull/123
```

**Result on main:**
- All changes traceable to specific PR
- All receipts preserved
- Full audit trail
- K5 determinism verified
- No silent mutations

---

## Workflow Example: You Submit Math Proof

### Day 1: Request Exists

```json
{
  "request_id": "REQ_001",
  "type": "MATH_DRAFT",
  "title": "K5 Determinism Proof",
  "why_needed": "Formalize same-input → same-output invariant",
  "status": "OPEN"
}
```

### Day 2: You Provide Content

**Option A: Upload via chat**
```
User: "Here's the K5 proof"
[Claude saves to oracle_town/inbox/REQ_001/proof.tex]
```

**Option B: Local file**
```bash
# You put file in:
oracle_town/inbox/REQ_001/proof.tex
```

### Day 3: Generate Receipt

```bash
python3 scripts/bibliotheque_manifest.py
# Output: receipts/bibliotheque_intake_manifest.json
# Manifest hash: abc123def456...
```

### Day 4: Bot Proposes PR

```
[Claude reads intake manifest]
[Claude creates branch: intake/REQ_001]
[Claude normalizes proof → oracle_town/memory/bibliotheque/math_proofs/001/]
[Claude creates metadata.json + digest.sha256]
[Claude opens PR with manifest hash in commit message]
```

**PR shows:**
```
Title: Intake: K5 Determinism Proof (REQ_001)

Body:
  Source: oracle_town/inbox/REQ_001/proof.tex
  Manifest hash: abc123def456...
  Content hash: def456abc123...

  CI Status: ✅ All checks passed
  - Manifest integrity verified
  - No secrets detected
  - Schema valid
  - Determinism confirmed

  Ready for tribunal merge.
```

### Day 5: You Review + Merge

```bash
# Review the PR (see normalized content + metadata)
git show origin/intake/REQ_001

# If approved:
git merge origin/intake/REQ_001

# Result: main updated with full audit trail
git log --oneline -3
  abc1234 Merge PR #123: Intake K5 proof (manifest: abc123def456)
  def5678 Intake: normalize K5 proof + metadata (REQ_001)
  ghi9012 Intake: record manifest (3 items in inbox)
```

---

## How to Proceed (Correct)

**I will NOT:**
- Commit to main autonomously
- Propose "autonomous mode" without tribunal
- Claim things work that bypass receipts

**I WILL:**

1. **Provide REQUESTS.json** (what town needs) ✅
2. **Implement intake manifest** (pure receipts) ✅
3. **Wait for your content** (inbox input)
4. **Generate manifest** (prove what was offered)
5. **Propose PR (draft, not merged)**
6. **Post diff + receipts** (for your review)
7. **You decide merge** (tribunal final say)

---

## Where Do You Upload Content?

**Two options:**

### Option A: Paste Into Chat (This Session)

```
User: "Here's the K5 proof"
[Paste math content]

Claude: [Saves to oracle_town/inbox/REQ_001/]
        [Generates manifest]
        [Shows proposed PR diff]
        [Waits for your approval to merge]
```

### Option B: Local Folder

```
You: put file in oracle_town/inbox/REQ_002/
Claude: python3 scripts/bibliotheque_manifest.py
        [Shows what's in inbox]
        [Proposes PR]
        [Waits for approval]
```

---

## Status

✅ **Inbox directory created** (oracle_town/inbox/)
✅ **Requests file created** (REQUESTS.json with 4 open requests)
✅ **Intake manifest script created** (bibliotheque_manifest.py, receipts only)
✅ **Constitutional model documented** (this file)

❌ **NOT autonomous mode** (requires tribunal + receipts)
❌ **NOT writing to main** (PR-only)
❌ **NOT claiming capability** (showing actual process)

---

## Next Step: Your Choice

**Which option for content intake?**

A) Paste content into this chat (I save to inbox, generate manifest, propose PR)
B) Local folder (you upload, I generate manifest, propose PR)
C) Both (some items via chat, some via folder)

Once you choose, we implement the full workflow with receipts + tribunal approval before any main branch merge.

