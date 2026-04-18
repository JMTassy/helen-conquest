# Next Phase: Three Options

**Status:** Architecture complete, audited, hardened
**Decision Point:** How to proceed with Phase 1

---

## Option 1: Standalone Kernel Repo

**Scope:** Extract Oracle Town kernel as independent project

**Deliverables:**
- New repo: `github.com/oracle-town/oracle-kernel`
- Clean separation from daily OS
- Documented integration APIs
- Example integrations (Moltbot, hypothetical framework)

**Time to Implement:**
- Organize: 1 hour
- Write integration guide: 2 hours
- Create example configs: 1 hour
- Total: 4 hours

**Advantages:**
- Clear positioning for ecosystem adoption
- Other agent frameworks can integrate independently
- Makes kernel reusability obvious
- Easier marketing (standalone safety product)

**Disadvantages:**
- No working code yet (still specification)
- Requires proof of concept first to avoid vaporware
- Repository management overhead

**Recommendation:** **Do this AFTER Option B** (proof that gates work)

---

## Option 2: Implement Gate A (Proof of Concept)

**Scope:** Build one real gate to prove control boundary

**Deliverables:**
- `oracle_town/kernel/gates.py` (Gate A only)
- Fetch freeze mechanism
- Shell command detection (bash, python, curl, eval)
- 10 test cases (adversarial skills)

**Time to Implement:**
- Fetch freeze (capture to file): 15 min
- Shell detection (regex): 15 min
- Error handling: 10 min
- Tests (adversarial): 20 min
- Total: ~60 minutes

**Code Estimate:** ~80 lines of Python

```python
# Pseudocode
def gate_fetch(fetched_content: bytes, evidence_dir: Path) -> GateResult:
    """Gate A: Fetch Gate"""

    # 1. Freeze (capture bytes)
    evidence_file = evidence_dir / f"fetch_{claim_id}.snapshot"
    evidence_file.write_bytes(fetched_content)

    # 2. Detect shell commands
    text = fetched_content.decode('utf-8', errors='ignore')
    forbidden_patterns = [
        r'\bbash\b', r'\bpython\b', r'\bcurl\b', r'\bwget\b',
        r'\beval\b', r'\bexec\b', r'\bsystem\b'
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, text):
            return GateResult.FAIL(f"GATE_FETCH_EXEC_SHELL: {pattern}")

    return GateResult.PASS()
```

**Advantages:**
- Proves gates work in practice
- Shows how control boundary functions
- Takes 1 hour (low risk)
- Provides concrete code to design around

**Disadvantages:**
- Only one gate (incomplete)
- No daemon integration yet
- No receipt generation
- Still can't run end-to-end

**Recommendation:** **Do this first** (30 min → credibility)

---

## Option 3: Implement Complete MVP (Gates + Mayor + Daemon)

**Scope:** Full Phase 1 implementation

**Deliverables:**
- Gate A, B, C (all three gates)
- Mayor (pure function)
- Kernel daemon (socket server)
- Claim router
- Receipt ledger
- Test suite (adversarial)

**Time to Implement:**
- Gates (3 × 50 lines): 90 min
- Mayor (30 lines): 30 min
- Daemon (100 lines): 90 min
- Router/Ledger (100 lines): 60 min
- Tests: 120 min
- Total: ~6 hours

**Code Estimate:** ~350 lines of Python + tests

**Advantages:**
- End-to-end working system
- Can integrate with Moltbot
- Demonstrates full capability
- Ready for Phase 2

**Disadvantages:**
- Significant implementation effort
- More surface area for bugs
- Harder to debug if something fails
- May hit unknown issues

**Recommendation:** **Do this AFTER Option 2** (proof first, then complete)

---

## My Recommendation: Option B → Option A → Option 3

### Sequence
1. **Start with Option B** (Gate A PoC, 1 hour)
   - Shows gates work
   - Builds confidence
   - Discovers implementation gotchas early
   - Low risk, high credibility

2. **Then Option A** (Standalone repo, 4 hours)
   - Extract to clean repo
   - Write integration guide
   - Create example configs
   - Position for ecosystem

3. **Then Option 3** (Complete MVP, 6 hours)
   - Build all gates
   - Implement mayor + daemon
   - Test end-to-end
   - Ready for Moltbot integration

### Total Timeline
- **Option B (Gate A):** 1 hour
- **Option A (Repo):** 4 hours
- **Option 3 (Full MVP):** 6 hours
- **Total:** 11 hours

### By End of Day
You would have:
- ✅ Working Gate A (proof of concept)
- ✅ Standalone kernel repo (ready for community)
- ✅ Complete MVP (can integrate with Moltbot)

---

## Why This Sequence Works

### Gate A First
- **Builds confidence:** "Gates are real, not theoretical"
- **Discovers issues early:** Architecture questions emerge in code
- **Low risk:** 1 hour, small scope, easy to throw away
- **Credibility boost:** "We didn't just spec this, we coded it"

### Standalone Repo Second
- **Positions for adoption:** Clean separation from daily OS
- **Ecosystem framing:** "Safety kernel for all agent systems"
- **Enables community:** Others can integrate while you finish MVP

### Full MVP Third
- **Proven approach:** You know gates work, you know daemon structure
- **Integration ready:** Moltbot module can use complete system
- **Production capable:** All pieces present, tested, ready

---

## Decision Framework

**If you want:**
- **Maximum credibility fast** → Start with Option B (1 hour), proves gates work
- **Ecosystem readiness** → Option B → Option A (5 hours), clean repo
- **Full functionality** → All three (11 hours), end-to-end system

**My vote:** Option B first (1 hour) → immediate ROI on credibility
Then decide whether to do A + B or jump to full MVP based on how it goes.

---

## What You Have Now

✅ **Complete architecture** (CLAUDE.md)
✅ **Detailed specifications** (Claim, Receipt, Gates)
✅ **Critical invariants** (K15–K24)
✅ **Integration guide** (Moltbot layout)
✅ **Development scenarios** (K-1, K-2, K-3)
✅ **Audit review** (all issues resolved)

**What's missing:** Working code

The gap between "perfect spec" and "working code" is where most projects fail. Option B (1 hour) closes that gap.

---

## My Recommendation (Direct)

**Do Option B right now (1 hour):**

1. Create `oracle_town/kernel/gates.py`
2. Implement Gate A (fetch freeze + shell detection)
3. Write 10 adversarial test cases
4. Verify all tests pass

**Why:**
- Proves gates work in practice
- Takes 1 hour (low commitment)
- Generates real code to design around
- Builds immediate momentum
- Shows "we didn't just theorize, we coded"

**Then:**
- Option A (standalone repo) if you want ecosystem positioning
- Or jump to Option 3 (full MVP) if A feels premature

---

## Yes / No Decision Points

**Do Option A if:**
- You want to position kernel as independent product
- Other agent frameworks should be able to integrate
- You're thinking ecosystem-first

**Do Option 3 if:**
- You just want a working Moltbot safety layer
- Integration with daily OS matters
- End-to-end system is the goal

**My take:** Option B (required), Option A (good), Option 3 (best). Start with B.

---

**Ready when you are.** Let me know which direction you want to go.
