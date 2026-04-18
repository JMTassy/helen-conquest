# Claude Code Keybindings: Foundry Town Enhanced

**File Location:** `~/.claude/keybindings.json`
**Status:** Configured
**Last Updated:** 2026-02-13

---

## What's Been Configured

The system keybindings have been set to optimized shortcuts for Foundry Town workflows.

### Fast Execution Keys

```json
{
  "context": "Chat",
  "bindings": {
    "ctrl+shift+n": "chat:submit",      // SUBMIT CLAIM or message
    "ctrl+shift+f": "chat:externalEditor",  // Edit in external editor (for long claims)
    "ctrl+shift+s": "chat:stash",       // Stash current work (safety)
    "ctrl+shift+h": "history:search"    // Search command history
  }
}
```

### Global Actions

```json
{
  "context": "Global",
  "bindings": {
    "ctrl+shift+t": "app:toggleTodos",      // Show/hide todo list (for session tracking)
    "ctrl+shift+m": "app:toggleTranscript"  // View full transcript (see all claims)
  }
}
```

---

## Recommended Additional Bindings (Optional)

If you want to customize further, add these to `~/.claude/keybindings.json`:

### For Deep Work (Expansion Phase)

```json
{
  "context": "Chat",
  "bindings": {
    "ctrl+k ctrl+e": "chat:externalEditor",  // CHORD: Open external editor (deep claims)
    "ctrl+k ctrl+s": "chat:stash"            // CHORD: Stash and pause
  }
}
```

This allows you to use **chords** (two-keystroke combos) for less-common actions, preserving single keys for frequent ones.

### For Quick Navigation

```json
{
  "context": "Global",
  "bindings": {
    "ctrl+k ctrl+c": "app:toggleTodos",      // CHORD: Show todos (track session)
    "ctrl+k ctrl+l": "app:toggleTranscript"  // CHORD: Show claims log
  }
}
```

---

## How to Modify

To add or change a binding:

1. **Edit the file:**
   ```bash
   open ~/.claude/keybindings.json
   ```

2. **Add a new binding** (keep existing ones):
   ```json
   {
     "context": "Chat",
     "bindings": {
       "ctrl+shift+n": "chat:submit",        // existing
       "YOUR_KEY": "YOUR_ACTION"             // new
     }
   }
   ```

3. **Unbind a default key** (if it conflicts):
   ```json
   {
     "context": "Chat",
     "bindings": {
       "ctrl+e": null   // Remove default external editor binding
     }
   }
   ```

4. **Save and restart Claude Code** (changes take effect immediately)

---

## Chord Binding Tutorial

**What is a chord?**

A chord is two keystrokes in sequence (1-second timeout between them).

**Example:**
- Press `ctrl+k`, release
- Then press `ctrl+s`, release
- Result: Stash action triggered

**Syntax:**
```json
"ctrl+k ctrl+s": "chat:stash"
```

**Why use chords?**
- Preserves single-key bindings for frequent actions (submit, undo)
- Allows more complex shortcuts without conflicts
- Reduces accidental triggering

**Common Chords:**
```
ctrl+k ctrl+s   →  Stash
ctrl+k ctrl+e   →  External editor
ctrl+k ctrl+c   →  Toggle todos
ctrl+k ctrl+l   →  Toggle transcript
```

---

## Avoiding Conflicts

**Reserved keys** (cannot rebind):
- `ctrl+c` — Interrupt/exit (system level)
- `ctrl+d` — Exit (system level)
- `ctrl+m` — Identical to Enter (terminal)

**Terminal reserved** (may not work):
- `ctrl+z` — Process suspend (SIGTSTP)
- `ctrl+\` — Terminal quit (SIGQUIT)

**macOS reserved** (will not work):
- `cmd+c`, `cmd+v`, `cmd+x` — System copy/paste
- `cmd+q`, `cmd+w` — System quit/close
- `cmd+tab`, `cmd+space` — System switcher/Spotlight

---

## Foundry Town-Specific Suggestions

If you want to add **skill shortcuts** (once skills are available), consider:

```json
{
  "context": "Chat",
  "bindings": {
    "ctrl+shift+n": "chat:submit",      // Already mapped (keep)
    "alt+f": "chat:submit",             // Alt+F for "Foundry"
    "alt+c": "chat:submit",             // Alt+C for "Claim"
    "alt+r": "chat:submit"              // Alt+R for "Rhythm-check"
  }
}
```

These act as **prefix keys** — when you press them, you get a prompt:
> "What skill? [foundry-new | claim | phase-next | ...]"

---

## Current Configuration (Live)

Your `~/.claude/keybindings.json` currently has:

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "$docs": "https://code.claude.com/docs/en/keybindings",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+shift+n": "chat:submit",
        "ctrl+shift+f": "chat:externalEditor",
        "ctrl+shift+s": "chat:stash",
        "ctrl+shift+h": "history:search"
      }
    },
    {
      "context": "Global",
      "bindings": {
        "ctrl+shift+t": "app:toggleTodos",
        "ctrl+shift+m": "app:toggleTranscript"
      }
    }
  ]
}
```

---

## Testing Your Bindings

To verify bindings are working:

1. Open Claude Code
2. Try: `ctrl+shift+n` (should submit message)
3. Try: `ctrl+shift+t` (should show/hide todos)
4. Try: `ctrl+shift+m` (should show transcript)

If any don't work:
- Run `/doctor` in Claude Code
- Check "Keybinding Configuration Issues"
- Fix any errors reported

---

## Quick Reference: Most Useful Bindings

| Key | Action | Use Case |
|-----|--------|----------|
| `ctrl+shift+n` | Submit | Send claim or message |
| `ctrl+shift+f` | External Editor | Write long/complex claims |
| `ctrl+shift+s` | Stash | Save work in progress |
| `ctrl+shift+t` | Toggle Todos | Check session tracking |
| `ctrl+shift+m` | Toggle Transcript | Review all claims in run |
| `ctrl+shift+h` | History | Find previous commands |

---

**Next Step:** Go use `/foundry-new` to create your first run, then reference SKILLS_QUICK_START.md for the workflow.
