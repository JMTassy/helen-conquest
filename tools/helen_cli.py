#!/usr/bin/env python3
"""
HELEN Interactive CLI Mode
Persistent command-line dialogue with HELEN.

Memory-aware: carries observations and reflections across sessions.
Supports modes: companion (default), fetch, meteo, wulmoji, shell
"""
import os, sys, json, subprocess, readline, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# ANSI colors
CYAN = "\x1b[36m"
MAGENTA = "\x1b[35m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"

LEDGER_PATH = str(ROOT / "town" / "ledger_v1.ndjson")
HELEN_SAY_SCRIPT = str(ROOT / "tools" / "helen_say.py")

MODES = {
    "companion": "Memory-aware companion (default)",
    "fetch":     "Standard fetch (kernel-routed)",
    "meteo":     "Meteorological context mode",
    "wulmoji":   "WULMOJI symbol interpretation",
    "shell":     "Shell operation mode (gated)",
}


class HeldenCLI:
    def __init__(self):
        self.mode = "companion"
        self.message_count = 0
        self.session_id = ""
        self.highlights = []
        self._companion = None
        self._companion_error = None
        self._try_load_companion()
        self.print_welcome()

    def _try_load_companion(self):
        try:
            from helen_companion import HelenCompanion
            self._companion = HelenCompanion()
            self.session_id = self._companion.open_session(source="cli")
        except Exception as e:
            self._companion_error = str(e)

    def print_welcome(self):
        print(f"{CYAN}{BOLD}═══════════════════════════════════════════════════════════{RESET}")
        print(f"{CYAN}HELEN — Persistent Companion{RESET}")
        print(f"{CYAN}{BOLD}═══════════════════════════════════════════════════════════{RESET}")
        print()
        print(f"Modes:")
        for mode, desc in MODES.items():
            marker = "→" if mode == self.mode else " "
            print(f"  {marker} {YELLOW}{mode:12}{RESET} {desc}")
        print()
        print(f"Commands:")
        print(f"  {YELLOW}/mode <name>{RESET}       Switch mode")
        print(f"  {YELLOW}/memory{RESET}            Show Helen's memory")
        print(f"  {YELLOW}/observe <text>{RESET}    Record a manual observation")
        print(f"  {YELLOW}/reflect{RESET}           Helen writes a journal entry")
        print(f"  {YELLOW}/context{RESET}           Show current memory context block")
        print(f"  {YELLOW}/status{RESET}            Show system status")
        print(f"  {YELLOW}/exit{RESET}              Close session and exit")
        print()
        if self._companion_error:
            print(f"{YELLOW}[WARN]{RESET} Companion unavailable: {self._companion_error}")
            print(f"  Falling back to kernel-only mode (fetch).")
            self.mode = "fetch"
        elif not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            print(f"{YELLOW}[WARN]{RESET} No GEMINI_API_KEY — companion responses will fail.")
            print(f"  Set GEMINI_API_KEY in your environment for Helen to respond.")
        print()

    def show_status(self):
        print(f"{CYAN}System Status:{RESET}")
        print(f"  Mode:         {YELLOW}{self.mode}{RESET}")
        print(f"  Session:      {self.session_id or '(none)'}")
        print(f"  Messages:     {self.message_count}")
        print(f"  Ledger:       {LEDGER_PATH}")
        print(f"  Companion:    {'loaded' if self._companion else 'unavailable'}")
        if os.path.exists(LEDGER_PATH):
            with open(LEDGER_PATH) as f:
                lines = sum(1 for _ in f)
            print(f"  Ledger events: {lines}")
        print()

    def show_memory(self):
        if not self._companion:
            print(f"{YELLOW}Companion not loaded.{RESET}\n")
            return
        self._companion.show_memory()

    def show_context(self):
        if not self._companion:
            print(f"{YELLOW}Companion not loaded.{RESET}\n")
            return
        block = self._companion.context_block()
        print(block if block else f"{DIM}(no memory yet){RESET}")
        print()

    def cmd_observe(self, text: str):
        if not self._companion:
            print(f"{YELLOW}Companion not loaded.{RESET}\n")
            return
        if not text.strip():
            print(f"{RED}Usage: /observe <text>{RESET}\n")
            return
        self._companion.observe(text.strip(), session_id=self.session_id)
        print(f"{DIM}Noted.{RESET}\n")

    def cmd_reflect(self):
        if not self._companion:
            print(f"{YELLOW}Companion not loaded.{RESET}\n")
            return
        try:
            from helen_reflect import generate_and_save_reflection
            print(f"{DIM}Helen is writing...{RESET}")
            text = generate_and_save_reflection(
                self._companion.memory, session_id=self.session_id
            )
            if text:
                print(f"\n{CYAN}[journal]{RESET} {text}\n")
            else:
                print(f"{YELLOW}No reflection generated (check GEMINI_API_KEY).{RESET}\n")
        except Exception as e:
            print(f"{RED}Reflect error: {e}{RESET}\n")

    def add_meteo_context(self, msg):
        now = datetime.datetime.now()
        return f"[METEO: {now.strftime('%A %H:%M')}] {msg}"

    def send_message_companion(self, msg: str):
        response = self._companion.chat(msg, session_id=self.session_id)
        print(f"\n{CYAN}helen:{RESET} {response}\n")
        self.highlights.append(msg[:60])

    def send_message_kernel(self, msg: str):
        py = sys.executable
        try:
            result = subprocess.run(
                [py, HELEN_SAY_SCRIPT, msg, "--op", self.mode, "--ledger", LEDGER_PATH],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout + result.stderr
            lines = output.split("\n")
            her_text = ""
            hal_verdict = "?"
            in_her = False

            for line in lines:
                if "[HER]" in line:
                    in_her = True
                    continue
                if "[HAL]" in line:
                    in_her = False
                    if "PASS" in line:    hal_verdict = "PASS"
                    elif "WARN" in line:  hal_verdict = "WARN"
                    elif "BLOCK" in line: hal_verdict = "BLOCK"
                    continue
                if in_her and line.strip() and not line.startswith("\x1b"):
                    her_text += line + "\n"

            print(f"\n{CYAN}[HER]{RESET}")
            print(her_text.strip())
            print()
            vc = GREEN if hal_verdict == "PASS" else YELLOW if hal_verdict == "WARN" else RED
            print(f"{MAGENTA}[HAL]{RESET} {vc}{hal_verdict}{RESET}\n")
        except subprocess.TimeoutExpired:
            print(f"{RED}Error: request timeout{RESET}\n")
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}\n")

    def send_message(self, msg: str):
        if not msg.strip():
            return
        if self.mode == "meteo":
            msg = self.add_meteo_context(msg)
        self.message_count += 1
        if self.mode == "companion" and self._companion:
            self.send_message_companion(msg)
        else:
            self.send_message_kernel(msg)

    def _on_exit(self):
        if self._companion and self.session_id:
            self._companion.close_session(
                self.session_id,
                highlights=self.highlights[-6:] if self.highlights else [],
            )
        print(f"{CYAN}Session closed. Helen carries it forward.{RESET}")

    def run(self):
        while True:
            try:
                prompt = f"{CYAN}[{self.mode}]{RESET} "
                user_input = input(prompt).strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    parts = user_input.split(None, 1)
                    cmd = parts[0][1:]
                    arg = parts[1] if len(parts) > 1 else ""

                    if cmd == "mode":
                        if arg and arg in MODES:
                            self.mode = arg
                            print(f"Mode: {YELLOW}{arg}{RESET}\n")
                        elif arg:
                            print(f"{RED}Unknown mode: {arg}{RESET}\n")
                        else:
                            print(f"Available: {', '.join(MODES)}\n")
                    elif cmd == "memory":
                        self.show_memory()
                    elif cmd == "context":
                        self.show_context()
                    elif cmd == "observe":
                        self.cmd_observe(arg)
                    elif cmd == "reflect":
                        self.cmd_reflect()
                    elif cmd == "status":
                        self.show_status()
                    elif cmd in ("exit", "quit"):
                        self._on_exit()
                        break
                    elif cmd == "help":
                        self.print_welcome()
                    else:
                        print(f"{RED}Unknown command: /{cmd}{RESET}\n")
                else:
                    self.send_message(user_input)

            except KeyboardInterrupt:
                print()
                self._on_exit()
                break
            except EOFError:
                print()
                self._on_exit()
                break


if __name__ == "__main__":
    cli = HeldenCLI()
    cli.run()
