#!/usr/bin/env python3
"""
HELEN Receipt Observer
=======================

Non-sovereign observation layer. Reads the ledger. Never writes to it.

Folds ledger entries into behavioral signals:
  - What intents the operator expressed
  - Which modes were used
  - Which providers generated proposals
  - What patterns emerge over time

Connects the three layers:
  ledger (memory) → observer (observation) → classifier → knowledge compiler → wiki

The observer does not decide. It does not claim authority.
It reconstructs what happened from what was recorded.

Commands:
  python3 tools/helen_receipt_observer.py stats
  python3 tools/helen_receipt_observer.py intents [--last N]
  python3 tools/helen_receipt_observer.py patterns [--classify]
  python3 tools/helen_receipt_observer.py export [--out <path>]

Authority: NON_SOVEREIGN
This tool reads sovereign records and emits non-sovereign observations.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Paths ──────────────────────────────────────────────────────────────────────

_REPO_ROOT  = Path(__file__).parent.parent
_LEDGER     = _REPO_ROOT / "town" / "ledger_v1.ndjson"

# ── ANSI ───────────────────────────────────────────────────────────────────────

RESET   = "\x1b[0m"
DIM     = "\x1b[2m"
CYAN    = "\x1b[36m"
GREEN   = "\x1b[32m"
YELLOW  = "\x1b[33m"
MAGENTA = "\x1b[35m"
RED     = "\x1b[31m"
BOLD    = "\x1b[1m"


# ── Ledger entry models ────────────────────────────────────────────────────────

@dataclass
class LedgerEntry:
    seq: int
    schema: str
    text: str
    timestamp: str
    cum_hash: str
    raw: Dict[str, Any]


@dataclass
class FocusModeEntry:
    """Parsed from USER_MSG_V1 entries with FOCUS_MODE prefix."""
    seq: int
    intent: str
    confirmed: str
    proposed_by: str          # ollama | gemini | heuristic
    mode: str                 # focus | witness
    timestamp: str
    cum_hash: str

    @classmethod
    def parse(cls, entry: LedgerEntry) -> Optional["FocusModeEntry"]:
        text = entry.text
        if "[FOCUS_MODE]" not in text:
            return None
        def _extract(key: str) -> str:
            m = re.search(r"\|\s*" + key + r":\s*(.+?)(?:\s*\||$)", text, re.I)
            if m:
                return m.group(1).strip()
            # Also check at start of string for INTENT
            m2 = re.search(r"\[FOCUS_MODE\]\s*" + key + r":\s*(.+?)(?:\s*\||$)", text, re.I)
            return m2.group(1).strip() if m2 else ""
        return cls(
            seq=entry.seq,
            intent=_extract("INTENT"),
            confirmed=_extract("CONFIRMED"),
            proposed_by=_extract("PROPOSED_BY") or "unknown",
            mode=_extract("MODE") or "focus",
            timestamp=entry.timestamp,
            cum_hash=entry.cum_hash,
        )


# ── Ledger reader ──────────────────────────────────────────────────────────────

class LedgerReader:
    """Read-only access to town/ledger_v1.ndjson."""

    def __init__(self, ledger_path: Optional[Path] = None) -> None:
        self.path = ledger_path or _LEDGER

    def entries(self) -> List[LedgerEntry]:
        if not self.path.exists():
            return []
        result = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    payload = ev.get("payload", {})
                    schema = payload.get("schema", ev.get("type", "?"))
                    text = (
                        payload.get("text")
                        or payload.get("content")
                        or ""
                    )
                    meta = ev.get("meta", {})
                    timestamp = meta.get("timestamp_utc", "")
                    result.append(LedgerEntry(
                        seq=ev.get("seq", 0),
                        schema=schema,
                        text=str(text),
                        timestamp=timestamp,
                        cum_hash=ev.get("cum_hash", ""),
                        raw=ev,
                    ))
                except Exception:
                    continue
        return result

    def user_messages(self) -> List[LedgerEntry]:
        return [e for e in self.entries() if e.schema == "USER_MSG_V1"]

    def focus_mode_entries(self) -> List[FocusModeEntry]:
        results = []
        for entry in self.user_messages():
            fm = FocusModeEntry.parse(entry)
            if fm:
                results.append(fm)
        return results

    def stats(self) -> Dict:
        entries = self.entries()
        schema_counts: Dict[str, int] = {}
        for e in entries:
            schema_counts[e.schema] = schema_counts.get(e.schema, 0) + 1
        fm = self.focus_mode_entries()
        provider_counts: Dict[str, int] = {}
        mode_counts: Dict[str, int] = {}
        for f in fm:
            provider_counts[f.proposed_by] = provider_counts.get(f.proposed_by, 0) + 1
            mode_counts[f.mode] = mode_counts.get(f.mode, 0) + 1
        last_seq = max((e.seq for e in entries), default=0)
        last_cum = entries[-1].cum_hash[:12] if entries else "?"
        return {
            "total_entries": len(entries),
            "last_seq": last_seq,
            "last_cum_hash": last_cum,
            "schema_distribution": schema_counts,
            "focus_mode_receipts": len(fm),
            "provider_distribution": provider_counts,
            "mode_distribution": mode_counts,
        }


# ── Receipt Observer ───────────────────────────────────────────────────────────

class ReceiptObserver:
    """
    Non-sovereign observation layer.
    Reads, classifies, and reports on ledger contents.
    Never writes to the ledger.
    """

    def __init__(self) -> None:
        self._reader = LedgerReader()
        self._clf = None  # lazy load

    def _get_classifier(self):
        if self._clf is None:
            try:
                _tools = Path(__file__).parent
                if str(_tools) not in sys.path:
                    sys.path.insert(0, str(_tools))
                from helen_symbolic_classifier import SymbolicClassifier  # type: ignore
                self._clf = SymbolicClassifier()
            except ImportError:
                pass
        return self._clf

    # ── Stats ──────────────────────────────────────────────────────────────────

    def print_stats(self) -> None:
        s = self._reader.stats()
        print()
        print(f"  {DIM}── LEDGER OBSERVATION ───────────────────────────{RESET}")
        print(f"  Total entries:        {s['total_entries']}")
        print(f"  Last seq:             {s['last_seq']}")
        print(f"  Last cum_hash:        {s['last_cum_hash']}…")
        print()
        print(f"  Schema distribution:")
        for schema, count in sorted(s["schema_distribution"].items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"    {DIM}{schema:<20}{RESET}  {bar}  {count}")
        print()
        fm_count = s["focus_mode_receipts"]
        if fm_count:
            print(f"  {GREEN}Focus Mode receipts:  {fm_count}{RESET}")
            if s["provider_distribution"]:
                print(f"  Provider distribution:")
                for p, c in sorted(s["provider_distribution"].items(), key=lambda x: -x[1]):
                    print(f"    {DIM}{p:<20}{RESET}  {c}")
        else:
            print(f"  {DIM}Focus Mode receipts:  0 (run CLI without --no-receipt to populate){RESET}")
        print()

    # ── Intents ────────────────────────────────────────────────────────────────

    def print_intents(self, last: int = 20) -> None:
        messages = self._reader.user_messages()
        if last:
            messages = messages[-last:]
        print()
        print(f"  {DIM}── RECENT OPERATOR MESSAGES (last {len(messages)}) ─────{RESET}")
        print()
        for m in messages:
            text = m.text[:80].replace("\n", " ")
            fm = FocusModeEntry.parse(m)
            if fm:
                print(f"  {GREEN}[{m.seq:>4}]{RESET}  {DIM}FOCUS:{RESET} {fm.intent[:60]}")
                print(f"         {DIM}→ confirmed: {fm.confirmed[:60]}{RESET}")
                print(f"         {DIM}  proposed_by: {fm.proposed_by}{RESET}")
            else:
                print(f"  {DIM}[{m.seq:>4}]  {text}{RESET}")
        print()

    # ── Patterns ───────────────────────────────────────────────────────────────

    def print_patterns(self, classify: bool = True) -> None:
        messages = self._reader.user_messages()
        texts = [m.text for m in messages if m.text.strip() and not m.text.startswith("--")]

        print()
        print(f"  {DIM}── PATTERN OBSERVATION ─────────────────────────{RESET}")
        print(f"  Observing {len(texts)} operator messages\n")

        # Length distribution
        lengths = [len(t) for t in texts]
        short  = sum(1 for l in lengths if l < 20)
        medium = sum(1 for l in lengths if 20 <= l < 80)
        long_  = sum(1 for l in lengths if l >= 80)
        print(f"  Message length:  short (<20)={short}  medium={medium}  long={long_}")

        # Emoji presence
        emoji_count = sum(1 for t in texts if re.search(r"[^\x00-\x7F]", t))
        print(f"  Contains emoji:  {emoji_count} / {len(texts)}")
        print()

        # Focus Mode analysis
        fm_entries = self._reader.focus_mode_entries()
        if fm_entries:
            print(f"  {GREEN}Focus Mode receipts:{RESET}")
            for fm in fm_entries[-10:]:
                print(f"    {DIM}[{fm.seq}]{RESET} {fm.intent[:50]} → {fm.confirmed[:40]}")
            print()

        if not classify:
            return

        clf = self._get_classifier()
        if not clf:
            print(f"  {DIM}(Symbolic classifier not available — install helen_symbolic_classifier.py){RESET}")
            return

        # Sample: classify last 15 non-trivial messages
        sample = [t for t in texts if len(t) > 5 and not t.startswith("[")][-15:]
        if not sample:
            print(f"  {DIM}No messages available for classification.{RESET}")
            return

        print(f"  Classifying {len(sample)} recent messages …\n")
        results = clf.classify_batch(sample)

        from collections import Counter
        mode_counts = Counter(r.mode for r in results)
        provider_counts = Counter(r.provider for r in results)
        avg_conf = sum(r.confidence for r in results) / len(results)

        mode_colors = {"focus": GREEN, "witness": YELLOW, "oracle": CYAN, "temple": MAGENTA}
        print(f"  Mode distribution:")
        for mode, count in mode_counts.most_common():
            color = mode_colors.get(mode, DIM)
            bar = "█" * count
            print(f"    {color}{mode:<10}{RESET}  {bar}  ({count})")
        print()
        print(f"  Avg confidence:    {avg_conf:.0%}")
        print(f"  Provider:          {dict(provider_counts)}")
        print()
        print(f"  Classified messages:")
        for r in results:
            color = mode_colors.get(r.mode, DIM)
            print(f"    {color}{r.surface:<14}{RESET}  {DIM}{r.raw_intent[:55]}{RESET}")
        print()

    # ── Export ─────────────────────────────────────────────────────────────────

    def export_markdown(self, out_path: Optional[Path] = None) -> Path:
        """
        Export observation report as markdown.
        Suitable for ingestion into the knowledge compiler wiki.
        Authority: NON_SOVEREIGN — this is an observation, not a governance record.
        """
        if out_path is None:
            out_path = _REPO_ROOT / "artifacts" / "receipt_observation_report.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        s = self._reader.stats()
        messages = self._reader.user_messages()
        fm_entries = self._reader.focus_mode_entries()
        texts = [m.text for m in messages if m.text.strip() and not m.text.startswith("--")]

        # Classify sample
        clf = self._get_classifier()
        classification_block = ""
        if clf and texts:
            sample = [t for t in texts if len(t) > 5 and not t.startswith("[")][-20:]
            results = clf.classify_batch(sample)
            from collections import Counter
            mode_counts = Counter(r.mode for r in results)
            classification_block = "\n## Intent mode distribution\n\n"
            for mode, count in mode_counts.most_common():
                pct = int(count / len(results) * 100)
                classification_block += f"- **{mode}**: {count} ({pct}%)\n"
            classification_block += "\n## Classified sample\n\n"
            for r in results:
                classification_block += f"- `{r.mode}` ({r.confidence:.0%}) — {r.raw_intent[:70]}\n"

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        content = f"""# HELEN Receipt Observer — Observation Report

**Generated:** {now}
**Authority:** NON_SOVEREIGN
**Source:** `town/ledger_v1.ndjson` (read-only)
**Note:** This is an observation, not a governance record. It does not amend the ledger.

---

## Ledger summary

- Total entries: {s['total_entries']}
- Last seq: {s['last_seq']}
- Last cum_hash: {s['last_cum_hash']}…

## Schema distribution

{chr(10).join(f'- `{k}`: {v}' for k, v in sorted(s['schema_distribution'].items(), key=lambda x: -x[1]))}

## Focus Mode receipts

{len(fm_entries)} receipts recorded via Focus Mode CLI.

{chr(10).join(f'- seq={f.seq}  intent={f.intent}  confirmed={f.confirmed}  provider={f.proposed_by}' for f in fm_entries) if fm_entries else '_None yet — run helen_focus_cli.py without --no-receipt to record._'}

{classification_block}

---

_This report is suitable for ingestion into the HELEN Knowledge Compiler._
_Run: `python -m helen_os.knowledge.compiler.cli ingest {out_path} --type document`_
"""
        out_path.write_text(content, encoding="utf-8")
        return out_path


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    observer = ReceiptObserver()
    cmd = args[0]

    if cmd == "stats":
        observer.print_stats()
        return 0

    if cmd == "intents":
        last = 20
        if "--last" in args:
            try:
                last = int(args[args.index("--last") + 1])
            except (IndexError, ValueError):
                pass
        observer.print_intents(last=last)
        return 0

    if cmd == "patterns":
        classify = "--classify" in args or "--no-classify" not in args
        observer.print_patterns(classify=classify)
        return 0

    if cmd == "export":
        out = None
        if "--out" in args:
            try:
                out = Path(args[args.index("--out") + 1])
            except (IndexError, ValueError):
                pass
        path = observer.export_markdown(out)
        print(f"\n  {GREEN}◆{RESET}  Exported → {path}")
        print(f"  {DIM}Ingest: python -m helen_os.knowledge.compiler.cli ingest {path} --type document{RESET}\n")
        return 0

    print(f"Unknown command: {cmd}. Use stats|intents|patterns|export", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
