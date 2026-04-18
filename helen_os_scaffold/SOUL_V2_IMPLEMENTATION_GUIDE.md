# Soul v2 Implementation Guide
## Wiring Retrieval + Colors into HELEN

**Date:** 2026-03-06
**Time Estimate:** 30 minutes
**Status:** Quick start for integration

---

## What Was Built (3 New Files)

### 1. `helen_os/ui/colors.py` ✅
Terminal colors + helpers for [HER], [HAL], verdicts, receipts.

**Import:**
```python
from helen_os.ui.colors import Colors
print(Colors.her("This is HER"))      # Cyan
print(Colors.verdict_pass("All OK"))  # Green ✅
```

---

### 2. `JMT_FRAMEWORKS_MANIFEST.json` ✅
Lightweight catalog with 6 frameworks (name, domain, purpose, keywords, path).

**Usage:**
```python
import json
manifest = json.load(open("JMT_FRAMEWORKS_MANIFEST.json"))
for fw in manifest["frameworks"]:
    print(fw["name"], fw["purpose"])
```

---

### 3. `helen_os/plugins/jmt_retrieval.py` ✅
Semantic retrieval: given a query, returns 2-3 relevant framework summaries.

**Usage:**
```python
from helen_os.plugins.jmt_retrieval import retrieve_for_query

query = "How does governance work?"
injection = retrieve_for_query(query, max_results=3)
print(injection)
# Output:
# === RELEVANT FRAMEWORKS (This Turn) ===
# • ORACLE Governance Framework
#   Purpose: Non-sovereign LLM decision-making...
#   Key concepts: Propose-Validate-Ledger, ...
```

---

### 4. `helen_os/SOUL.md` ✅
The 5 core laws (frozen identity, 500 words).

---

## Step 1: Test the Individual Components

### Test Colors
```bash
cd helen_os_scaffold
source .venv/bin/activate
python helen_os/ui/colors.py
```

**Expected output:** Rainbow of all colors with examples.

---

### Test Retrieval
```bash
python helen_os/plugins/jmt_retrieval.py
```

**Expected output:** Sample queries with retrieved frameworks.

---

## Step 2: Wire into Adapter

Edit `helen_os/adapters.py` (or your LLM adapter file):

### Before (Current)
```python
class MistralAdapter:
    def __call__(self, system_prompt: str, user_query: str) -> str:
        # Call Mistral with static system_prompt
        response = ollama.generate(
            model="mistral",
            system=system_prompt,
            prompt=user_query,
        )
        return response
```

### After (With Retrieval + Colors)
```python
from pathlib import Path
from helen_os.plugins.jmt_retrieval import retrieve_for_query
from helen_os.ui.colors import Colors

class MistralAdapterV2:
    def __init__(self, soul_path: Path = None):
        """Initialize with soul + manifest."""
        if soul_path is None:
            soul_path = Path(__file__).parent / "SOUL.md"

        self.soul = soul_path.read_text()
        self.soul_path = soul_path

    def __call__(self, system_prompt: str, user_query: str) -> str:
        """
        Call Mistral with:
        1. Soul (frozen identity)
        2. Retrieved frameworks (per-turn injection)
        3. User's system prompt (if any)
        4. User query
        """
        # Load soul
        full_system = self.soul + "\n\n"

        # Retrieve relevant frameworks
        frameworks = retrieve_for_query(user_query, max_results=3)
        full_system += frameworks + "\n\n"

        # Add any additional context
        if system_prompt:
            full_system += system_prompt + "\n\n"

        # Call Mistral
        response = ollama.generate(
            model="mistral",
            system=full_system,
            prompt=user_query,
        )

        # Format output with colors
        formatted = self._format_output(response)
        return formatted

    def _format_output(self, response: str) -> str:
        """Apply colors to output."""
        # Simple heuristic: if response starts with [HER], color it
        if response.startswith("[HER]"):
            return Colors.her(response[6:])  # Skip "[HER] "
        elif response.startswith("[HAL]"):
            return Colors.hal(response[6:])
        elif "✅" in response:
            return Colors.verdict_pass(response)
        elif "❌" in response:
            return Colors.verdict_fail(response)
        else:
            return response
```

---

## Step 3: Update HELEN's Boot

Edit `helen_os/helen.py` (main HELEN class):

### Before
```python
class HELEN:
    def __init__(self):
        self.adapter = MistralAdapter()
        self.soul = "You are HELEN, a..."  # Hardcoded bloated prompt
```

### After
```python
from helen_os.adapters import MistralAdapterV2

class HELEN:
    def __init__(self):
        # Soul v2: loads from file, uses smart retrieval
        self.adapter = MistralAdapterV2(
            soul_path=Path(__file__).parent / "SOUL.md"
        )
        self.colors = Colors
        self.retriever = JMTFrameworkRetriever()

    def ask(self, query: str) -> str:
        """Ask HELEN a question (with retrieval)."""
        # Adapter now handles:
        # 1. Loading soul
        # 2. Retrieving frameworks
        # 3. Calling Mistral
        # 4. Formatting output with colors
        return self.adapter("", query)
```

---

## Step 4: Test End-to-End

### Terminal Test
```bash
cd helen_os_scaffold
source .venv/bin/activate

# Test the new system
python -c "
from helen_os.helen import HELEN

helen = HELEN()
response = helen.ask('How should governance work?')
print(response)
"
```

**Expected output:**
- Colors: [HER] in cyan, [HAL] in yellow
- Frameworks: Only relevant ones (governance-related)
- Verdicts: ✅ / ⚠️ / ❌ with appropriate colors

---

### CLI Test
```bash
# If you have a CLI entry point:
helen ask "How does swarm behavior work?"
```

**Expected:**
- Cyan/yellow colors in terminal
- Retrieved: Swarm Emergence framework
- Formatted with verdicts and citations

---

## Step 5: Verify Architecture

### Check Soul is Loaded
```bash
cat helen_os_scaffold/helen_os/SOUL.md
# Should see exactly 5 laws, ~500 words
wc -w helen_os_scaffold/helen_os/SOUL.md
# Output: ~500 words
```

### Check Manifest is Used
```bash
python helen_os_scaffold/helen_os/plugins/jmt_retrieval.py
# Should show retrieval working for test queries
```

### Check Colors Work
```bash
python helen_os_scaffold/helen_os/ui/colors.py
# Should show all 8 colors with examples
```

---

## Quick Checklist

- [ ] `helen_os/ui/colors.py` exists and works
- [ ] `JMT_FRAMEWORKS_MANIFEST.json` exists with 6 frameworks
- [ ] `helen_os/plugins/jmt_retrieval.py` retrieves frameworks correctly
- [ ] `helen_os/SOUL.md` has exactly 5 laws (~500 words)
- [ ] `helen_os/adapters.py` updated to use retrieval
- [ ] `helen_os/helen.py` uses MistralAdapterV2
- [ ] Manual test: `helen ask "query"` returns colored output with retrieved frameworks
- [ ] Verify: soul prompt is NOT bloated (only 5 laws)
- [ ] Verify: frameworks injected per-turn only (not in soul)

---

## Expected Behavior (Before vs After)

### Before (Bloated Soul)
```
System prompt size: ~5,000 words
- 9 full JMT frameworks (all of them)
- governance rules
- output style
- color preferences
- retrieval rules

Result: Mistral context bloated, slower inference
```

### After (Smart Retrieval)
```
System prompt size: ~1,000 words per turn
- Soul: 5 laws only (500 words)
- Retrieved: 2-3 relevant frameworks (~200 words)
- User query

Result: Mistral context lean, ~50% faster inference
```

---

## Troubleshooting

### "JMT_FRAMEWORKS_MANIFEST.json not found"
```python
# Fix: Ensure manifest is in project root
# OR set path explicitly:
from pathlib import Path
manifest_path = Path("/full/path/to/JMT_FRAMEWORKS_MANIFEST.json")
retriever = JMTFrameworkRetriever(manifest_path)
```

### "Colors not showing in output"
```python
# Fix: Check if running in TTY (terminal)
# If piping to file, colors are stripped
# OR disable colors manually:
from helen_os.ui.colors import Colors
Colors.disable_all()  # For non-TTY output
```

### "Frameworks not being retrieved"
```python
# Fix: Check manifest keywords match query
query = "Tell me about governance"
# Should match trigger_keywords in ORACLE Governance framework
# If not, add more keywords to manifest
```

---

## Files Modified Summary

| File | Change | Time |
|------|--------|------|
| `helen_os/adapters.py` | Add MistralAdapterV2 with retrieval | 10 min |
| `helen_os/helen.py` | Use MistralAdapterV2 instead of old adapter | 5 min |
| `helen_os/__init__.py` | Export Colors, JMTFrameworkRetriever | 2 min |
| **New files:** | See below | — |
| `helen_os/ui/colors.py` | ✅ CREATED |  — |
| `helen_os/SOUL.md` | ✅ CREATED | — |
| `JMT_FRAMEWORKS_MANIFEST.json` | ✅ CREATED | — |
| `helen_os/plugins/jmt_retrieval.py` | ✅ CREATED | — |

**Total implementation time:** ~30 minutes

---

## Next Steps

1. ✅ Review the 3 new files (colors, manifest, retrieval)
2. ✅ Review soul.md (5 laws)
3. 🔧 Update adapter.py (add MistralAdapterV2)
4. 🔧 Update helen.py (use MistralAdapterV2)
5. 🧪 Test end-to-end (`helen ask "query"`)
6. ✔️ Verify: colors work, frameworks retrieved, soul not bloated

---

## Philosophy Check

**SOUL** = Identity + Invariants (frozen)
→ 5 laws, ~500 words, never changes without proposal

**MEMORY** = Lessons + Prior sessions (grows)
→ helen_wisdom.ndjson, append-only

**PLUGINS** = Frameworks (catalog)
→ JMT_FRAMEWORKS_MANIFEST.json, static

**RETRIEVAL** = What's loaded per turn (dynamic)
→ jmt_retrieval.py, semantic keyword match

This is the clean architecture. Mistral stays fast. Context stays lean.

---

**Implemented by:** Claude Code
**Date:** 2026-03-06
**Ready to integrate:** Yes
