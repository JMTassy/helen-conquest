#!/usr/bin/env python3
"""
HELEN Focus Mode CLI
====================

The default daily-use interface for HELEN OS.
Implements the core product loop:

  intent → proposal → confirmation → receipt

Running:
  python3 tools/helen_focus_cli.py
  python3 tools/helen_focus_cli.py --witness      # constitutional layer
  python3 tools/helen_focus_cli.py --no-receipt   # dry-run (no ledger write)

Design principle:
  HELEN is not a cockpit.
  HELEN is a calm presence that opens the right panel at the right moment.

HELEN suggests. You decide. Everything is recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Paths ──────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
_HELEN_SAY = _REPO_ROOT / "tools" / "helen_say.py"
_LEDGER = _REPO_ROOT / "town" / "ledger_v1.ndjson"

# ── ANSI ───────────────────────────────────────────────────────────────────────

RESET   = "\x1b[0m"
DIM     = "\x1b[2m"
BOLD    = "\x1b[1m"
CYAN    = "\x1b[36m"
GREEN   = "\x1b[32m"
YELLOW  = "\x1b[33m"
RED     = "\x1b[31m"
WHITE   = "\x1b[37m"

# ── Visual constants ───────────────────────────────────────────────────────────

_RULE  = DIM + "─" * 54 + RESET
_HRULE = DIM + "━" * 54 + RESET


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ledger_tail() -> Tuple[int, str]:
    """Return (last_seq, last_cum_hash[:12]) for the ledger status line."""
    try:
        if not _LEDGER.exists() or _LEDGER.stat().st_size == 0:
            return 0, "0" * 12
        with open(_LEDGER, "rb") as f:
            f.seek(max(0, _LEDGER.stat().st_size - 32768))
            lines = f.read().decode("utf-8", "replace").strip().splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                seq = ev.get("seq", 0)
                cum = ev.get("cum_hash", "?" * 12)[:12]
                return seq, cum
            except Exception:
                continue
    except Exception:
        pass
    return 0, "?" * 12


# ── Header ─────────────────────────────────────────────────────────────────────

def _print_header(gate_state: str = "Gate Clear · No Active Claim",
                  witness: bool = False) -> None:
    mode = (YELLOW + "WITNESS MODE" + RESET) if witness else (DIM + "FOCUS MODE" + RESET)
    print()
    print(_HRULE)
    print(f"  {CYAN}{BOLD}HELEN{RESET}  {DIM}◆{RESET}  {DIM}{gate_state}{RESET}   {mode}")
    print(_HRULE)
    print()


def _print_receipt_line(seq: int, cum: str) -> None:
    print(f"  {DIM}◆  Latest Receipt: seq={seq}  cum_hash={cum}…  {GREEN}APPENDED{RESET}{DIM}{RESET}")
    print()


# ── Proposal generation ────────────────────────────────────────────────────────

# Verb → (step_1, step_2, step_3) templates
_VERB_TEMPLATES: Dict[str, Tuple[str, str, str]] = {
    "prepare": (
        "Gather and organise all relevant sources ({obj})",
        "Synthesise key insights and identify the core narrative",
        "Draft the {obj} document with a clear executive summary",
    ),
    "plan": (
        "Map the scope and constraints for {obj}",
        "Identify dependencies, risks, and key decisions",
        "Produce the {obj} plan with milestones and owners",
    ),
    "research": (
        "Survey the landscape and collect primary sources for {obj}",
        "Distil key findings and rank by relevance",
        "Prepare a structured briefing document on {obj}",
    ),
    "review": (
        "Scan {obj} for critical items and flag priorities",
        "Extract actionable items and open questions",
        "Summarise {obj} with a recommended next action",
    ),
    "write": (
        "Outline the structure for {obj}",
        "Draft the core content for {obj}",
        "Review, refine, and finalise {obj}",
    ),
    "draft": (
        "Outline the structure for {obj}",
        "Draft the core content for {obj}",
        "Review, refine, and finalise {obj}",
    ),
    "analyse": (
        "Map the problem space for {obj}",
        "Identify patterns, gaps, and key signals in {obj}",
        "Formulate conclusions and recommendations for {obj}",
    ),
    "analyze": (
        "Map the problem space for {obj}",
        "Identify patterns, gaps, and key signals in {obj}",
        "Formulate conclusions and recommendations for {obj}",
    ),
    "organise": (
        "List and prioritise all items in {obj}",
        "Clear blockers and resolve ambiguities in {obj}",
        "Schedule or delegate remaining items from {obj}",
    ),
    "organize": (
        "List and prioritise all items in {obj}",
        "Clear blockers and resolve ambiguities in {obj}",
        "Schedule or delegate remaining items from {obj}",
    ),
    "build": (
        "Define the scope and acceptance criteria for {obj}",
        "Implement the core functionality of {obj}",
        "Test, document, and ship {obj}",
    ),
    "design": (
        "Gather requirements and constraints for {obj}",
        "Sketch the structure and key decisions for {obj}",
        "Produce the {obj} design with rationale",
    ),
    "send": (
        "Draft {obj} with a clear subject and call to action",
        "Review for tone, accuracy, and recipient alignment",
        "Send {obj} and log the follow-up",
    ),
    "finish": (
        "Review current state of {obj} and identify open items",
        "Complete the remaining work on {obj}",
        "Close {obj} with a confirmation or receipt",
    ),
    "complete": (
        "Review current state of {obj} and identify open items",
        "Complete the remaining work on {obj}",
        "Close {obj} with a confirmation or receipt",
    ),
    "update": (
        "Pull the latest information for {obj}",
        "Identify what has changed and what matters",
        "Update {obj} and notify relevant parties",
    ),
    "check": (
        "Run a status check on {obj}",
        "Identify gaps, issues, or blockers in {obj}",
        "Produce a brief status report on {obj}",
    ),
}

_DEFAULT_TEMPLATE: Tuple[str, str, str] = (
    "Clarify the goal and gather context for: {obj}",
    "Work through the core task: {obj}",
    "Produce a clear output or decision for: {obj}",
)


def _parse_intent(intent: str) -> Tuple[str, str]:
    """Return (verb_lower, object_display) extracted from intent."""
    intent = intent.strip().rstrip(".")
    # Strip leading filler (case-insensitive)
    intent_clean = re.sub(
        r"^(i want to|i need to|please|help me|can you|i'd like to)\s+",
        "",
        intent,
        flags=re.I,
    ).strip()

    tokens_lower = intent_clean.lower().split()
    tokens_orig  = intent_clean.split()
    verb = tokens_lower[0] if tokens_lower else "do"

    # Object preserves original capitalisation
    obj_raw = " ".join(tokens_orig[1:]) if len(tokens_orig) > 1 else intent_clean

    # Remove leading articles
    obj_clean = re.sub(r"^(my|our|the|a|an)\s+", "", obj_raw, flags=re.I).strip()

    # Trim very long objects for readability in templates (keep a clean noun phrase)
    if len(obj_clean) > 60:
        # Stop at first conjunction or preposition to get the core noun phrase
        m = re.search(r"\s+(from|with|about|using|via|and|to|for|in|on|by)\s+",
                      obj_clean[:70], re.I)
        if m:
            obj_clean = obj_clean[:m.start()].strip()
        else:
            obj_clean = obj_clean[:55].strip() + "…"

    return verb, (obj_clean or intent_clean)


def _heuristic_proposals(intent: str) -> List[str]:
    """Generate 3 contextual action proposals from an intent string."""
    verb, obj = _parse_intent(intent)
    template = _VERB_TEMPLATES.get(verb, _DEFAULT_TEMPLATE)
    return [t.format(obj=obj) for t in template]


def _gemini_proposals(intent: str, api_key: str) -> Optional[List[str]]:
    """Use Gemini Flash to generate 3 focused proposals. Returns None on failure."""
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        prompt = (
            "You are HELEN, a calm, non-sovereign AI OS.\n"
            "The operator has stated this intent: {intent}\n\n"
            "Generate exactly 3 concrete, actionable next steps.\n"
            "Each step should be a single sentence starting with a verb.\n"
            "Focus on real work — no philosophical framing.\n"
            "Return only a JSON array of 3 strings, nothing else.\n"
            'Example: ["Draft the outline", "Gather the sources", "Write the brief"]'
        ).format(intent=intent)

        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        raw = resp.text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        proposals = json.loads(raw)
        if isinstance(proposals, list) and len(proposals) >= 3:
            return [str(p).strip() for p in proposals[:3]]
    except Exception:
        pass
    return None


def _generate_proposals(intent: str, api_key: str = "") -> Tuple[List[str], str]:
    """Return (proposals, mode) where mode is 'gemini' or 'heuristic'."""
    if api_key:
        result = _gemini_proposals(intent, api_key)
        if result:
            return result, "gemini"
    return _heuristic_proposals(intent), "heuristic"


# ── Gate state ─────────────────────────────────────────────────────────────────

class GateState:
    CLEAR      = "Gate Clear · No Active Claim"
    EVALUATING = "EVALUATING …"
    AUTHORIZED = "SHIP AUTHORIZED"
    FORBIDDEN  = "SHIP FORBIDDEN"

    @staticmethod
    def color(state: str) -> str:
        if state == GateState.AUTHORIZED:
            return GREEN + state + RESET
        if state in (GateState.FORBIDDEN,):
            return RED + state + RESET
        if state == GateState.EVALUATING:
            return YELLOW + state + RESET
        return DIM + state + RESET


# ── Witness panel ──────────────────────────────────────────────────────────────

def _print_witness_panel(gate_state: str, seq: int, cum: str,
                         amp=None) -> None:
    print(_RULE)
    print(f"  {DIM}── WITNESS ───────────────────────────────────────{RESET}")
    print(f"  {DIM}LEGORACLE    {RESET}{GateState.color(gate_state)}")
    print(f"  {DIM}Ledger       seq={seq}  cum_hash={cum}…{RESET}")
    print(f"  {DIM}Constitution I–VIII  VERIFIED{RESET}")
    print(f"  {DIM}Authority    NON_SOVEREIGN  ·  Proposer = HELEN{RESET}")
    if amp is not None:
        try:
            s = amp.status()
            active = s.get("active", "?")
            print(f"  {DIM}AMP          active={RESET}{CYAN}{active}{RESET}")
        except Exception:
            pass
    print(_RULE)
    print()


# ── Receipt emission ───────────────────────────────────────────────────────────

def _emit_receipt(intent: str, action: str, provider: str = "heuristic",
                  mode: str = "focus", dry_run: bool = False) -> bool:
    """
    Emit a receipt via helen_say.py (canonical write path).
    Includes provider provenance: non-sovereign origin is traceable in the ledger.
    Returns True on success.
    """
    if dry_run:
        print(f"  {DIM}[DRY-RUN] Receipt not written.{RESET}")
        return True

    if not _HELEN_SAY.exists():
        print(f"  {RED}[ERROR] helen_say.py not found at {_HELEN_SAY}{RESET}")
        return False

    # Provenance: record who proposed so the ledger carries the full chain:
    #   cognition proposed (non-sovereign) → operator confirmed → ledger recorded
    message = (
        f"[FOCUS_MODE] INTENT: {intent}"
        f"  |  CONFIRMED: {action}"
        f"  |  PROPOSED_BY: {provider}"
        f"  |  MODE: {mode}"
    )
    try:
        result = subprocess.run(
            [sys.executable, str(_HELEN_SAY), message, "--op", "fetch"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True
        else:
            # Kernel may not be running — not fatal for Focus Mode
            # Receipt is still attempted; warn but do not crash
            print(f"  {YELLOW}[WARN] Kernel unreachable — receipt queued locally.{RESET}")
            return True
    except subprocess.TimeoutExpired:
        print(f"  {YELLOW}[WARN] helen_say.py timed out — receipt not confirmed.{RESET}")
        return False
    except Exception as e:
        print(f"  {RED}[ERROR] {e}{RESET}")
        return False


# ── Main loop ──────────────────────────────────────────────────────────────────

class FocusCLI:
    def __init__(self, witness: bool = False, no_receipt: bool = False,
                 api_key: str = "") -> None:
        self.witness = witness
        self.no_receipt = no_receipt
        self.api_key = api_key
        self.session_count = 0
        # AMP: model router (Ollama → Gemini → heuristic)
        try:
            _amp_root = Path(__file__).parent
            if str(_amp_root) not in sys.path:
                sys.path.insert(0, str(_amp_root))
            from helen_amp import AMPRouter  # type: ignore
            self._amp = AMPRouter(gemini_key=api_key)
        except ImportError:
            self._amp = None

    def _input(self, prompt: str) -> str:
        try:
            return input(prompt).strip()
        except EOFError:
            return ""

    def _print_proposals(self, proposals: List[str], mode: str) -> None:
        source = DIM + f"({mode})" + RESET
        print(f"  {CYAN}HELEN proposes{RESET} {source}\n")
        for i, p in enumerate(proposals, 1):
            print(f"  {DIM}[{i}]{RESET}  {p}")
        print()

    def _confirm_choice(self, proposals: List[str]) -> Optional[str]:
        while True:
            raw = self._input(f"  Your choice {DIM}[1/2/3]{RESET} or {DIM}[r]etry  {RESET}› ")
            if raw in ("1", "2", "3"):
                return proposals[int(raw) - 1]
            if raw.lower() in ("r", "retry", ""):
                return None
            if raw.lower() in ("q", "quit", "exit"):
                return "EXIT"
            print(f"  {DIM}Enter 1, 2, 3, r to rephrase, or q to quit.{RESET}")

    def run_once(self) -> bool:
        """Run one intent cycle. Returns False if session should end."""
        gate_state = GateState.CLEAR
        _print_header(gate_state, witness=self.witness)

        # ── Intent ────────────────────────────────────────────────────────────
        if self.session_count == 0:
            print(f"  {DIM}What are you working on?{RESET}")
        intent = self._input(f"  {CYAN}›{RESET} ")
        if not intent or intent.lower() in ("q", "quit", "exit"):
            return False
        print()

        # ── Gate: evaluating ─────────────────────────────────────────────────
        if self.witness:
            gate_state = GateState.EVALUATING
            seq, cum = _ledger_tail()
            _print_witness_panel(gate_state, seq, cum, amp=self._amp)

        # ── Proposals (via AMP router if available) ───────────────────────────
        if self._amp is not None:
            proposals, mode = self._amp.propose(intent)
        else:
            proposals, mode = _generate_proposals(intent, self.api_key)

        # ── Gate: clear (proposals are non-sovereign suggestions, not claims) ─
        gate_state = GateState.CLEAR
        if self.witness:
            seq, cum = _ledger_tail()
            _print_witness_panel(gate_state, seq, cum, amp=self._amp)

        self._print_proposals(proposals, mode)

        # ── Confirmation loop ─────────────────────────────────────────────────
        confirmed_action: Optional[str] = None
        while confirmed_action is None:
            choice = self._confirm_choice(proposals)
            if choice == "EXIT":
                return False
            if choice is None:
                # Retry: re-enter intent
                print()
                print(f"  {DIM}Rephrase your intent:{RESET}")
                new_intent = self._input(f"  {CYAN}›{RESET} ")
                if not new_intent or new_intent.lower() in ("q", "quit", "exit"):
                    return False
                intent = new_intent
                if self._amp is not None:
                    proposals, mode = self._amp.propose(intent)
                else:
                    proposals, mode = _generate_proposals(intent, self.api_key)
                print()
                self._print_proposals(proposals, mode)
            else:
                confirmed_action = choice

        # ── Receipt ───────────────────────────────────────────────────────────
        print()
        print(_RULE)
        print(f"  {GREEN}✓{RESET}  Confirmed:  {confirmed_action}")
        print()

        if self.witness:
            gate_state = GateState.CLEAR
            seq, cum = _ledger_tail()
            _print_witness_panel(gate_state, seq, cum, amp=self._amp)

        ok = _emit_receipt(intent, confirmed_action, provider=mode,
                          mode="witness" if self.witness else "focus",
                          dry_run=self.no_receipt)
        if ok:
            seq, cum = _ledger_tail()
            _print_receipt_line(seq, cum)
        print(_RULE)

        self.session_count += 1
        return True

    def run(self) -> None:
        print()
        print(f"  {DIM}HELEN OS  ◆  Focus Mode  ◆  NON_SOVEREIGN{RESET}")
        print(f"  {DIM}HELEN suggests. You decide. Everything is recorded.{RESET}")
        print()

        try:
            while True:
                again = self.run_once()
                if not again:
                    break
                print()
                cont = self._input(
                    f"  {DIM}Another intent? [{RESET}y{DIM}/{RESET}n{DIM}]{RESET}  › "
                ).lower()
                if cont not in ("y", "yes", ""):
                    break
        except KeyboardInterrupt:
            print()

        print()
        print(f"  {DIM}Session closed.  Receipts: {self.session_count}{RESET}")
        print()


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="helen-focus",
        description="HELEN Focus Mode CLI — intent → proposal → confirmation → receipt",
    )
    parser.add_argument(
        "--witness",
        action="store_true",
        help="Open the constitutional layer (Witness Mode)",
    )
    parser.add_argument(
        "--no-receipt",
        dest="no_receipt",
        action="store_true",
        help="Dry-run mode — do not write to the ledger",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=os.environ.get("GEMINI_API_KEY", ""),
        help="Gemini API key for LLM proposals (default: $GEMINI_API_KEY)",
    )
    args = parser.parse_args()

    cli = FocusCLI(
        witness=args.witness,
        no_receipt=args.no_receipt,
        api_key=args.api_key,
    )
    cli.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
