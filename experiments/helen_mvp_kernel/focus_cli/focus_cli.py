"""HELEN OS — Focus Mode CLI.

Authority:    NON_SOVEREIGN
Canon:        NO_SHIP
Lifecycle:    EXPERIMENTAL_MVP
Scope:        experiments/helen_mvp_kernel/focus_cli/
Parent spec:  docs/proposals/FOCUS_MODE_TERMINAL_SPEC.md (commit 442f5ee)

The loop:
    intent → propose (max 3) → confirm (single key) → receipt → calm.

Discipline (per HELEN OS doctrine):
    HELEN proposes.
    Operator decides.
    Ledger records.
    Reducer decides KEEP/REJECT — never this CLI.

Hard rules baked in:
- AI may only propose. The CLI never decides KEEP/REJECT.
- No automatic deciders, no Ralph loop.
- No execution of shell commands. Focus actions are *intent commitments*,
  not shell effects.
- LEGORACLE pill stays idle ("Gate Clear · No Active Claim") unless the
  kernel reports an active claim. Verdicts (SHIP_AUTHORIZED /
  SHIP_FORBIDDEN / DENIED / PENDING_RECEIPT) appear only in WITNESS mode
  during active claim evaluation — out of scope for this MVP.
- Sacred / 8D / mystical labels never appear as system text. The
  language firewall (Session-level) scans AI-authored payloads on write.

Run:
    cd experiments/helen_mvp_kernel
    PYTHONPATH=. python -m focus_cli.focus_cli
    PYTHONPATH=. python -m focus_cli.focus_cli --witness   # MVP stub
"""
from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from helen_os.authority.desire_firewall import scan_payload as scan_desires
from helen_os.authority.language_firewall import scan_payload as scan_authority
from helen_os.authority.policy import (
    load_forbidden_desires,
    load_forbidden_tokens,
    policy_hash,
)
from helen_os.ledger.event_log import append_event, read_events
from helen_os.ledger.hash_chain import GENESIS_HASH
from helen_os.ledger.schemas import make_actor, make_envelope


# ---------------------------------------------------------------------------
# Defaults — relative to experiments/helen_mvp_kernel/ (the scope sandbox)
# ---------------------------------------------------------------------------

KERNEL_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = KERNEL_ROOT / "ledger" / "events.ndjson"
PERMISSIONS = KERNEL_ROOT / "policy" / "permissions.json"
TOKENS = KERNEL_ROOT / "policy" / "forbidden_tokens.json"
DESIRES = KERNEL_ROOT / "policy" / "forbidden_desires.json"

PRODUCT_TAGLINE = "HELEN suggests. You decide. Everything is recorded."
LEGORACLE_IDLE = "Gate Clear · No Active Claim"
HELEN_GLYPH = "◉"


# ---------------------------------------------------------------------------
# FocusKernel: focus-specific event writer.
# Reuses the same ledger file and hash-chain primitives as Session, without
# the shell-execution path. Defense-in-depth scans AI-authored payloads.
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class FocusKernel:
    def __init__(
        self,
        ledger_path: Path = LEDGER_PATH,
        permissions_path: Path = PERMISSIONS,
        tokens_path: Path = TOKENS,
        desires_path: Path = DESIRES,
    ) -> None:
        self.ledger_path = ledger_path
        self.policy_hash = policy_hash(permissions_path)
        self.forbidden_tokens = load_forbidden_tokens(tokens_path)
        self.forbidden_desires = load_forbidden_desires(desires_path)
        self.session_id: str | None = None
        self.last_event_hash = self._read_last_hash()

    def _read_last_hash(self) -> str:
        events = read_events(self.ledger_path)
        if not events:
            return GENESIS_HASH
        return events[-1]["event_hash"]

    def _actor(self, kind: str, actor_id: str) -> dict:
        return make_actor(kind, actor_id, self.policy_hash)

    def _emit(self, event: dict) -> dict:
        if event["actor"]["kind"] == "AI":
            scan_authority(event["payload"], self.forbidden_tokens)
            scan_desires(event["payload"], self.forbidden_desires)
        append_event(self.ledger_path, event)
        self.last_event_hash = event["event_hash"]
        return event

    def start_session(self) -> str:
        sid = "F-" + uuid.uuid4().hex[:12]
        ev = make_envelope(
            event_type="COGNITION_STARTED",
            session_id=sid,
            timestamp=_now_iso(),
            actor=self._actor("RUNTIME", "focus_cli"),
            payload={"reason": "focus_mode_session_start"},
            input_hash="",
            output_hash="",
            prev_event_hash=self.last_event_hash,
        )
        self._emit(ev)
        self.session_id = sid
        return sid

    def declare_intent(self, intent: str) -> dict:
        if not self.session_id:
            raise RuntimeError("no active session; call start_session() first")
        ev = make_envelope(
            event_type="EFFECT_PROPOSED",
            session_id=self.session_id,
            timestamp=_now_iso(),
            actor=self._actor("OPERATOR", "operator"),
            payload={"effect_kind": "focus_intent_declared", "intent": intent},
            input_hash="",
            output_hash="",
            prev_event_hash=self.last_event_hash,
        )
        return self._emit(ev)

    def propose_action(self, idx: int, label: str, description: str) -> dict:
        if not self.session_id:
            raise RuntimeError("no active session")
        ev = make_envelope(
            event_type="EFFECT_PROPOSED",
            session_id=self.session_id,
            timestamp=_now_iso(),
            actor=self._actor("AI", "focus_planner_stub"),
            payload={
                "effect_kind": "focus_action_proposed",
                "proposal_index": idx,
                "label": label,
                "description": description,
            },
            input_hash="",
            output_hash="",
            prev_event_hash=self.last_event_hash,
        )
        return self._emit(ev)

    def confirm_action(self, chosen_idx: int, label: str) -> dict:
        if not self.session_id:
            raise RuntimeError("no active session")
        ev = make_envelope(
            event_type="OPERATOR_DECISION",
            session_id=self.session_id,
            timestamp=_now_iso(),
            actor=self._actor("OPERATOR", "operator"),
            payload={
                "effect_kind": "focus_action_confirmed",
                "chosen_index": chosen_idx,
                "label": label,
            },
            input_hash="",
            output_hash="",
            prev_event_hash=self.last_event_hash,
        )
        return self._emit(ev)

    def cancel(self) -> dict:
        if not self.session_id:
            raise RuntimeError("no active session")
        ev = make_envelope(
            event_type="OPERATOR_DECISION",
            session_id=self.session_id,
            timestamp=_now_iso(),
            actor=self._actor("OPERATOR", "operator"),
            payload={"effect_kind": "focus_action_cancelled"},
            input_hash="",
            output_hash="",
            prev_event_hash=self.last_event_hash,
        )
        return self._emit(ev)

    def terminate(self, verdict: str = "ABORT") -> dict:
        if not self.session_id:
            return {}
        ev = make_envelope(
            event_type="COGNITION_TERMINATED",
            session_id=self.session_id,
            timestamp=_now_iso(),
            actor=self._actor("RUNTIME", "focus_cli"),
            payload={"verdict": verdict},
            input_hash="",
            output_hash="",
            prev_event_hash=self.last_event_hash,
        )
        out = self._emit(ev)
        self.session_id = None
        return out


# ---------------------------------------------------------------------------
# Stub planner. Generates 3 generic, observably non-AI proposals from an
# intent. This is a placeholder for a real planner; it is intentionally
# obvious and deterministic so it cannot be mistaken for cognition.
# ---------------------------------------------------------------------------

PROPOSAL_TEMPLATES = [
    ("Inventory inputs", "List the sources, notes, and emails that feed this intent."),
    ("Draft the deliverable shape", "Write a one-page outline of what 'done' looks like."),
    ("Identify the first concrete step", "Name the smallest action that moves the intent forward."),
]


def stub_plan(intent: str) -> list[tuple[str, str]]:
    # NOTE: stub planner. Returns three generic next steps, untouched by intent
    # except in the CLI rendering. When a real planner is wired, swap this
    # function — the CLI contract (3 tuples of (label, description)) is stable.
    return list(PROPOSAL_TEMPLATES)


# ---------------------------------------------------------------------------
# Renderer — Focus Mode terminal layout per
# docs/proposals/FOCUS_MODE_TERMINAL_SPEC.md
# ---------------------------------------------------------------------------


def hr(width: int = 70) -> str:
    return "─" * width


def render_focus_screen(intent: str, proposals: list[tuple[str, str]], last_receipt: str) -> str:
    lines: list[str] = []
    lines.append(hr())
    lines.append(" kernel ●  ledger ●  safety ●          [ FOCUS ] | witness ")
    lines.append(hr())
    lines.append("")
    lines.append(f"  {HELEN_GLYPH} HELEN")
    lines.append("")
    lines.append("  intent:")
    for chunk in _wrap(intent, 60):
        lines.append(f"    {chunk}")
    lines.append("")
    lines.append("  proposals:")
    for i, (label, _desc) in enumerate(proposals, start=1):
        lines.append(f"    {i}  {label}")
    lines.append("")
    lines.append(f"  {PRODUCT_TAGLINE}")
    lines.append("")
    lines.append(hr())
    lines.append(f" ⏚ {last_receipt}")
    lines.append(f" {LEGORACLE_IDLE}")
    lines.append(" AMP  Files  Net  Notes  Cal  Mail  Oracle  Settings    :help")
    lines.append(hr())
    return "\n".join(lines)


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    out: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + 1 + len(w) <= width:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [""]


def render_confirmation(idx: int, label: str, description: str, receipt_class: str) -> str:
    lines = [
        "",
        "  HELEN proposes:",
        f"  {description}",
        "",
        f"  → kernel route   : focus_action_confirmed (index {idx})",
        f"  → expected event : {receipt_class}",
        "",
        "  [ y ]es   [ n ]o   [ i ]nputs",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------


def read_line(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ":quit"


def help_text() -> str:
    return (
        "\n"
        "  Focus Mode commands:\n"
        "    1, 2, 3      select a proposal (then y/n to confirm)\n"
        "    :intent <s>  declare a new intent\n"
        "    :refresh     regenerate proposals from the current intent\n"
        "    :cancel      drop current proposals, return to calm\n"
        "    :ledger      print recent receipt hashes from this session\n"
        "    :witness     (MVP stub — see Witness Mode spec)\n"
        "    :help        show this list\n"
        "    :quit        terminate session and exit\n"
    )


def run_loop(kernel: FocusKernel, witness: bool) -> int:
    if witness:
        print(
            "Witness Mode is in a separate spec "
            "(docs/proposals/HELEN_OS_V2_USER_CENTRIC_UX.md §10). "
            "Not implemented in this MVP. Exiting."
        )
        return 0

    sid = kernel.start_session()
    print(f"\n[FOCUS] session {sid} started — receipt {kernel.last_event_hash[:12]}\n")

    intent: str | None = None
    proposals: list[tuple[str, str]] = []
    last_receipt = f"COGNITION_STARTED · APPENDED · {kernel.last_event_hash[:12]}"

    while True:
        if intent is None:
            print(render_focus_screen("(no intent declared yet — type :intent <text>)", [], last_receipt))
            cmd = read_line("\n> ").strip()
        elif not proposals:
            ev = kernel.declare_intent(intent)
            last_receipt = f"focus_intent_declared · APPENDED · {ev['event_hash'][:12]}"
            proposals = stub_plan(intent)
            for i, (label, desc) in enumerate(proposals, start=1):
                ev = kernel.propose_action(i, label, desc)
                last_receipt = f"focus_action_proposed · APPENDED · {ev['event_hash'][:12]}"
            print(render_focus_screen(intent, proposals, last_receipt))
            cmd = read_line("\n> ").strip()
        else:
            print(render_focus_screen(intent, proposals, last_receipt))
            cmd = read_line("\n> ").strip()

        if not cmd:
            continue
        if cmd in {":quit", ":q"}:
            kernel.terminate("ABORT")
            print("\n[FOCUS] session terminated (ABORT). Calm.")
            return 0
        if cmd == ":help":
            print(help_text())
            continue
        if cmd == ":witness":
            print("[Witness Mode is in a separate spec; not implemented in this MVP.]")
            continue
        if cmd == ":cancel":
            if proposals:
                kernel.cancel()
                last_receipt = f"focus_action_cancelled · APPENDED · {kernel.last_event_hash[:12]}"
                proposals = []
            continue
        if cmd == ":refresh":
            if intent is None:
                print("(no intent yet — :intent <text> first)")
                continue
            proposals = []
            continue
        if cmd.startswith(":intent "):
            intent = cmd[len(":intent "):].strip() or None
            proposals = []
            continue
        if cmd == ":ledger":
            print(f"\n  last event_hash: {kernel.last_event_hash}\n")
            continue
        if cmd in {"1", "2", "3"}:
            if not proposals:
                print("(no proposals to choose from — :intent <text> first)")
                continue
            idx = int(cmd)
            if idx > len(proposals):
                print(f"(only {len(proposals)} proposals available)")
                continue
            label, description = proposals[idx - 1]
            print(render_confirmation(idx, label, description, "OPERATOR_DECISION"))
            ans = read_line("> ").lower().strip()
            if ans in {"y", "yes"}:
                ev = kernel.confirm_action(idx, label)
                last_receipt = f"focus_action_confirmed · APPENDED · {ev['event_hash'][:12]}"
                proposals = []
                print(f"\n[FOCUS] confirmed #{idx} '{label}' — receipt {ev['event_hash'][:12]}\n")
                continue
            if ans in {"n", "no"}:
                print("(cancelled — return to calm)")
                continue
            if ans in {"i", "inputs"}:
                print(f"\n  description: {description}\n")
                continue
            print("(unrecognised — y / n / i)")
            continue
        print("(unrecognised command — :help for the list)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="focus_cli", description="HELEN OS Focus Mode CLI (MVP)")
    p.add_argument("--witness", action="store_true", help="MVP stub for Witness Mode (prints note and exits)")
    p.add_argument("--ledger", default=str(LEDGER_PATH), help="Path to NDJSON event ledger")
    args = p.parse_args(argv)

    kernel = FocusKernel(ledger_path=Path(args.ledger))
    return run_loop(kernel, witness=args.witness)


if __name__ == "__main__":
    sys.exit(main())
