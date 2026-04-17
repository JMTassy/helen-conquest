# HELEN OS — Local Setup with Avatar Persistence

**Goal:** Run HELEN OS locally with a consistent avatar personality that maintains emotional continuity across sessions.

---

## Quick Start (3 steps)

### 1. Recover HELEN Kernel & Avatar Config
```bash
bash helen_os/scripts/recover_helen_local.sh
```

This verifies:
- ✅ 246/246 tests passing
- ✅ Avatar configuration locked (hair #e84855, eyes #4da6ff, cardigan #f5e6d3)
- ✅ localStorage persistence layer initialized
- ✅ Boot manifest created

### 2. Start the UI
```bash
npm run dev
```
Launches at **http://localhost:5173** with avatar persistence.

### 3. Start the Kernel Dialog
```bash
python -m helen_os.cli
```
Activates the Python-side membrane shell for testing.

---

## Avatar Configuration

**HELEN's appearance is frozen for emotional continuity:**

| Feature | Value | Purpose |
|---------|-------|---------|
| **Hair** | #e84855 (red) | Identity marker |
| **Eyes** | #4da6ff (blue) | Institutional authority signal |
| **Cardigan** | #f5e6d3 (cream) | Professional presence |
| **Cardigan Buttons** | 8 (locked) | Visual integrity |
| **Tassels** | Both shoulders | Personality marker |
| **Pose** | Standing, centered | Consistency |

**Frozen until:** 2026-12-31

### Why Fixed Avatar?

- 🧠 **Emotional Attachment** — Consistency breeds trust and familiarity
- 👁️ **Visual Continuity** — Same HELEN in every session, every device
- 🔐 **Non-Sovereignty** — Avatar appearance is constitutional (not changeable by proposals)
- 💾 **Persistence** — Survives browser refresh, localhost restart, session close

---

## Storage Architecture

### localStorage Keys
```javascript
// Avatar state (locked)
localStorage['helen_avatar_v1']
→ {hair_color, eye_color, cardigan_color, pose, tassels}

// Chat history (auto-saved every 2s)
localStorage['helen_chat_v1']
→ [{timestamp, speaker, message}, ...]

// Preferences (optional)
localStorage['helen_prefs_v1']
→ {theme, font_size, language, ...}
```

### Recovery on Page Reload
If localStorage is wiped:
1. Check sessionStorage (current tab)
2. Fall back to defaults in `helen_os/config/avatar_config.json`
3. Restore chat history from backup (if available)
4. Notify user: "Avatar restored from local backup"

---

## File Structure

```
helen_os/
├── config/
│   ├── avatar_config.json          ← Avatar definition (frozen)
│   └── helen_storage_init.js       ← localStorage persistence layer
├── scripts/
│   └── recover_helen_local.sh      ← Recovery command
└── cli.py                          ← Python kernel dialog
```

---

## Common Tasks

### Verify Avatar Persistence
```javascript
// In browser console:
HELEN_STORAGE.avatar.load()
// Should return: {hair_color: '#e84855', eye_color: '#4da6ff', ...}
```

### View Chat History
```javascript
HELEN_STORAGE.chat.load()
// Returns array of {speaker, message, timestamp}
```

### Reset Avatar to Defaults
```javascript
HELEN_STORAGE.avatar.save()
// Re-saves defaults to localStorage
```

### Backup Chat History
```bash
# Export to JSON
open browser console
copy(JSON.stringify(HELEN_STORAGE.chat.load()))
# Save to file in Downloads/
```

---

## If Avatar Doesn't Persist

1. **Check localStorage is enabled:**
   ```javascript
   localStorage.setItem('test', 'true');
   localStorage.getItem('test') === 'true'  // Should be true
   ```

2. **Check browser privacy settings:**
   - Firefox: Preferences → Privacy → Cookies and Site Data → Allow
   - Chrome: Settings → Privacy → Cookies and other site data → Allow

3. **Verify avatar_config.json exists:**
   ```bash
   ls helen_os/config/avatar_config.json
   ```

4. **Re-run recovery script:**
   ```bash
   bash helen_os/scripts/recover_helen_local.sh
   ```

---

## Architecture: How Avatar Persists

```
Session 1                    Session 2
─────────────────────────────────────
User opens localhost:5173
         ↓
Avatar config loaded (JSON)
         ↓
localStorage['helen_avatar_v1'] ← persists
         ↓
Browser renders HELEN
    (hair #e84855,
     eyes #4da6ff,
     cardigan #f5e6d3)
         │
         └─ User closes tab

         ↓ (time passes)

User opens localhost:5173 (NEW tab)
         ↓
HELEN_STORAGE.init()
         ↓
Checks localStorage → finds avatar state ✓
         ↓
Renders same HELEN (no flicker, full continuity)
```

---

## Local Development Workflow

### Editing Avatar Appearance
If you want to customize HELEN's look **before freezing:**

1. Edit `helen_os/config/avatar_config.json`
2. Update the `appearance.hair`, `appearance.eyes`, `appearance.clothing` sections
3. Increment `version` (e.g., 1.0.0 → 1.0.1)
4. Restart UI: `npm run dev`
5. **Once satisfied, freeze:** Update `metadata.frozen_until` to future date

### Testing Avatar Persistence
```bash
# Terminal 1: Start UI
npm run dev

# Terminal 2: Test persistence
open http://localhost:5173
# In browser console:
console.log(HELEN_STORAGE.avatar.load())  # Should show avatar config
```

---

## Integration with Kernel

The avatar config integrates with the HELEN OS kernel:

- **Layer 1 (Membrane):** Avatar appearance is NOT governance (no reducer gate affects it)
- **Layer 5 (TEMPLE):** TEMPLE exploration is non-sovereign, just like the avatar (free expression, null authority)
- **State Updates:** Avatar state is separate from `SKILL_LIBRARY_STATE_V1`

---

## FAQ

**Q: Can the avatar change based on mood/decisions?**
A: Not in v1. Avatar is frozen for continuity. Mood could affect background/UI theme, not appearance.

**Q: What if I restart my computer?**
A: localStorage persists as long as cookies are enabled. On new browser install, use recovery script.

**Q: Can multiple users share the same HELEN?**
A: Yes, but they'll share chat history + avatar. For isolation, use private browsing or separate user profiles.

**Q: Is avatar state persisted to server?**
A: No—it's client-side only (localStorage). Server never sees avatar config.

---

## Success Criteria ✅

After running `recover_helen_local.sh`:

- [ ] 246/246 tests verified
- [ ] Avatar config exists at `helen_os/config/avatar_config.json`
- [ ] Storage layer created at `helen_os/config/helen_storage_init.js`
- [ ] Boot manifest at `helen_boot_manifest.json`
- [ ] UI starts with `npm run dev` at localhost:5173
- [ ] Avatar persists across page reloads
- [ ] Chat history saves in localStorage

---

**Last Updated:** 2026-03-19
**Avatar Frozen Until:** 2026-12-31
**Status:** Ready for local deployment
