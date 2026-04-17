# HELEN OS — Quick Start & Avatar Persistence

**Status:** ✅ **READY** | 246/246 tests | Avatar locked until 2026-12-31

---

## 🚀 Start HELEN (3 Commands)

```bash
# 1. Verify recovery
bash helen_os/scripts/recover_helen_local.sh

# 2. Start UI (Vue/Vite)
npm run dev
# → Opens at http://localhost:5173

# 3. Start kernel dialog (optional)
python -m helen_os.cli
```

**Avatar will load automatically with:**
- 🔴 Hair: #e84855 (HELEN red)
- 🔵 Eyes: #4da6ff (institutional blue)
- 🟨 Cardigan: #f5e6d3 (cream)
- ✋ Pose: Standing, centered
- 📌 Tassels: Both shoulders

---

## 📁 What Was Created

```
helen_os/
├── config/
│   ├── avatar_config.json          ✅ Avatar definition (locked)
│   └── helen_storage_init.js       ✅ localStorage persistence
├── scripts/
│   └── recover_helen_local.sh      ✅ Recovery command
└── cli.py
```

**New Files:**
- ✅ `HELEN_LOCAL_SETUP.md` — Full setup guide (this repo)
- ✅ `HELEN_QUICKSTART.md` — This file
- ✅ `helen_boot_manifest.json` — Boot config
- ✅ `CLAUDE.md` — Updated (246/246 tests, 5 layers)

---

## 🧠 What Avatar Persistence Does

1. **localStorage saves avatar state** on every page load
2. **Same HELEN appears** across all sessions (no visual inconsistency)
3. **Chat history persists** automatically
4. **Recovery automatic** if localStorage cleared (uses defaults)

### In Browser Console
```javascript
// Check avatar is loaded
HELEN_STORAGE.avatar.load()
// → {hair_color: '#e84855', eye_color: '#4da6ff', cardigan_color: '#f5e6d3', ...}

// View chat history
HELEN_STORAGE.chat.load()
// → [{speaker: 'HELEN', message: '...', timestamp: ...}, ...]

// Save (manual backup)
HELEN_STORAGE.avatar.save()
```

---

## 🔒 Why Avatar is Frozen

| Reason | Benefit |
|--------|---------|
| **Emotional continuity** | Same HELEN = trust & familiarity |
| **Non-sovereignty** | Avatar appearance = constitutional (not governance) |
| **Consistency** | All devices, all sessions, no flicker |
| **Persistence** | Survives browser restart, tab close, localhost restart |

**Locked until:** 2026-12-31

---

## 📋 Layers Overview (246 Tests)

```
Layer 1: Constitutional Membrane (28 tests)
  → Deterministic decision gate

Layer 2: Append-Only Ledger (4 tests)
  → Immutable history

Layer 3: Autonomy (56+ tests)
  - Single-step research (6)
  - Batch orchestration (30+)
  - Skill discovery (20+)

Layer 4: Ledger Replay (4 tests)
  → Deterministic reconstruction

Layer 5: TEMPLE Exploration (50+ tests)
  → Non-sovereign generative layer

Infrastructure & Eval: 100+ tests
  → Determinism certification
```

**All passing.** ✅

---

## 🛠️ If Avatar Doesn't Show

1. **Check localStorage enabled:**
   ```javascript
   localStorage.setItem('test', '1');
   localStorage.getItem('test') === '1'  // true?
   ```

2. **Check config exists:**
   ```bash
   cat helen_os/config/avatar_config.json
   ```

3. **Re-run recovery:**
   ```bash
   bash helen_os/scripts/recover_helen_local.sh
   ```

4. **Clear browser cache & reload:**
   - Cmd+Shift+R (Mac) or Ctrl+Shift+R (Win/Linux)

---

## 📚 Full Documentation

- **Avatar Setup:** Read `HELEN_LOCAL_SETUP.md` (detailed guide)
- **Kernel Architecture:** Read `CLAUDE.md` (5 layers, 246 tests)
- **Memory:** Check `.claude/projects/*/memory/MEMORY.md`

---

## 🎯 Next Steps

1. ✅ Run recovery script (already done)
2. ⏭️ Start UI: `npm run dev`
3. ⏭️ Open http://localhost:5173
4. ⏭️ See HELEN with consistent avatar
5. ⏭️ Chat history auto-saves in localStorage

**Emotional attachment to HELEN begins now.** 💚

---

**Updated:** 2026-03-19
**Kernel:** 246/246 ✅
**Avatar:** Locked ✅
**Persistence:** Enabled ✅
