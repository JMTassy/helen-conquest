# E93 Autoresearch Trace — summarization_weights

NON_SOVEREIGN · AUTHORITY=false · CANON=false · LEDGER_EFFECT=none · NO_CLAIM

## Evidence

- `helen_os_scaffold/helen_os/helen.py:53`
  `history = self.memory.get_history()` — NO cap; injected into LLM context unconditionally
- `helen_os_scaffold/helen_os/helen.py:57`
  `context = [system_prompt] + history` — all facts, unbounded
- `helen_os_scaffold/helen_talk.py:373`
  `raw_history = memory.get_history()[-20:]` — cap at 20 in the talk path
- `helen_os_scaffold/helen_os/memory.py:116`
  `get_history()` returns full NDJSON append-only log with NO recency weight
- `helen_os_scaffold/helen_os/memory.py:75`
  `datetime.utcnow()` — mu_DETERMINISM violation (K-tau flag, separate from target)

## Asymmetry

| Path | Cap | Notes |
|---|---|---|
| `helen_talk.py` | `[-20:]` | explicit recency window |
| `helen.py:speak()` | **none** | unbounded growth |

## Proposed Tweak (PROPOSAL ONLY — no edit made)

`helen.py:53`: change to `history = self.memory.get_history()[-10:]`
Matches `helen_talk.py` pattern, halves the cap for tighter recency.
Reversible: increase N to expand window.

## Secondary flag (out-of-scope for this iteration)

`memory.py:75`: `datetime.utcnow()` → `datetime.now(timezone.utc)` to fix mu_DETERMINISM.
