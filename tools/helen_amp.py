#!/usr/bin/env python3
"""
HELEN AMP — Autonomous Model Processor
=======================================

Model router + provider health + proposal bridge.

Responsibility:
  Accept an intent string.
  Route it to the best available provider.
  Return exactly 3 concrete, actionable proposals.

Provider priority (highest to lowest):
  1. Ollama (local, fast, no API key needed)
  2. Gemini Flash (cloud, requires GEMINI_API_KEY)
  3. Heuristic (deterministic, always available)

Usage as module:
  from tools.helen_amp import AMPRouter
  router = AMPRouter()
  proposals, provider = router.propose("Prepare my Q3 strategy")
  status = router.status()

Usage as CLI:
  python3 tools/helen_amp.py propose "Prepare my Q3 strategy"
  python3 tools/helen_amp.py status
  python3 tools/helen_amp.py health

Authority: NON_SOVEREIGN
All proposals are suggestions. The operator decides.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Constants ──────────────────────────────────────────────────────────────────

_DEFAULT_OLLAMA_URL   = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "gemma3:1b"
_TIMEOUT_HEALTH       = 2   # seconds
_TIMEOUT_GENERATE     = 30  # seconds

# ── ANSI (display only) ────────────────────────────────────────────────────────

RESET  = "\x1b[0m"
DIM    = "\x1b[2m"
CYAN   = "\x1b[36m"
GREEN  = "\x1b[32m"
YELLOW = "\x1b[33m"
RED    = "\x1b[31m"


# ── Provider interface ─────────────────────────────────────────────────────────

@dataclass
class ProviderStatus:
    name: str
    online: bool
    model: str = ""
    latency_ms: Optional[float] = None
    error: str = ""

    def display(self) -> str:
        state = GREEN + "ONLINE " + RESET if self.online else DIM + "OFFLINE" + RESET
        model_str = f"  {DIM}{self.model}{RESET}" if self.model else ""
        latency_str = (
            f"  {DIM}{self.latency_ms:.0f}ms{RESET}" if self.latency_ms is not None else ""
        )
        err_str = f"  {DIM}({self.error}){RESET}" if self.error else ""
        return f"  {self.name:<12} {state}{model_str}{latency_str}{err_str}"


# ── Heuristic templates ────────────────────────────────────────────────────────

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
    "write":   ("Outline the structure for {obj}", "Draft the core content for {obj}", "Review, refine, and finalise {obj}"),
    "draft":   ("Outline the structure for {obj}", "Draft the core content for {obj}", "Review, refine, and finalise {obj}"),
    "analyse": ("Map the problem space for {obj}", "Identify patterns and key signals in {obj}", "Formulate conclusions and recommendations for {obj}"),
    "analyze": ("Map the problem space for {obj}", "Identify patterns and key signals in {obj}", "Formulate conclusions and recommendations for {obj}"),
    "organise": ("List and prioritise all items in {obj}", "Clear blockers and resolve ambiguities", "Schedule or delegate remaining items from {obj}"),
    "organize": ("List and prioritise all items in {obj}", "Clear blockers and resolve ambiguities", "Schedule or delegate remaining items from {obj}"),
    "build":  ("Define scope and acceptance criteria for {obj}", "Implement the core functionality of {obj}", "Test, document, and ship {obj}"),
    "design": ("Gather requirements and constraints for {obj}", "Sketch the structure and key decisions for {obj}", "Produce the {obj} design with rationale"),
    "send":   ("Draft {obj} with a clear subject and call to action", "Review for tone, accuracy, and recipient alignment", "Send {obj} and log the follow-up"),
    "finish": ("Review current state of {obj} and identify open items", "Complete the remaining work on {obj}", "Close {obj} with a confirmation or receipt"),
    "complete": ("Review current state of {obj} and identify open items", "Complete the remaining work on {obj}", "Close {obj} with a confirmation or receipt"),
    "update": ("Pull the latest information for {obj}", "Identify what has changed and what matters", "Update {obj} and notify relevant parties"),
    "check":  ("Run a status check on {obj}", "Identify gaps, issues, or blockers in {obj}", "Produce a brief status report on {obj}"),
}

_DEFAULT_TEMPLATE: Tuple[str, str, str] = (
    "Clarify the goal and gather context for: {obj}",
    "Work through the core task: {obj}",
    "Produce a clear output or decision for: {obj}",
)


def _parse_intent(intent: str) -> Tuple[str, str]:
    intent = intent.strip().rstrip(".")
    intent_clean = re.sub(
        r"^(i want to|i need to|please|help me|can you|i'd like to)\s+",
        "", intent, flags=re.I,
    ).strip()
    tokens_lower = intent_clean.lower().split()
    tokens_orig  = intent_clean.split()
    verb = tokens_lower[0] if tokens_lower else "do"
    obj_raw = " ".join(tokens_orig[1:]) if len(tokens_orig) > 1 else intent_clean
    obj_clean = re.sub(r"^(my|our|the|a|an)\s+", "", obj_raw, flags=re.I).strip()
    if len(obj_clean) > 60:
        m = re.search(r"\s+(from|with|about|using|via|and|to|for|in|on|by)\s+",
                      obj_clean[:70], re.I)
        if m:
            obj_clean = obj_clean[:m.start()].strip()
        else:
            obj_clean = obj_clean[:55].strip() + "…"
    return verb, (obj_clean or intent_clean)


def _heuristic(intent: str) -> List[str]:
    verb, obj = _parse_intent(intent)
    template = _VERB_TEMPLATES.get(verb, _DEFAULT_TEMPLATE)
    return [t.format(obj=obj) for t in template]


# ── Ollama provider ────────────────────────────────────────────────────────────

class OllamaProvider:
    def __init__(self, base_url: str = "", model: str = "") -> None:
        self.base_url = (base_url or os.environ.get("OLLAMA_HOST", _DEFAULT_OLLAMA_URL)).rstrip("/")
        self.model    = model or os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)

    def health(self) -> ProviderStatus:
        import time
        t0 = time.monotonic()
        try:
            req = urllib.request.Request(self.base_url + "/", method="GET")
            with urllib.request.urlopen(req, timeout=_TIMEOUT_HEALTH) as resp:
                resp.read()
            latency = (time.monotonic() - t0) * 1000
            return ProviderStatus("ollama", True, self.model, latency)
        except Exception as e:
            return ProviderStatus("ollama", False, self.model, error=str(e)[:60])

    def propose(self, intent: str) -> Optional[List[str]]:
        prompt = (
            "You are HELEN, a calm non-sovereign AI assistant.\n"
            f"The operator wants to: {intent}\n\n"
            "Generate exactly 3 concrete, actionable next steps. "
            "Each step is a single sentence starting with a verb. "
            "Focus on real work — no philosophical framing.\n"
            'Return ONLY a JSON array of 3 strings. '
            'Example: ["Draft the outline", "Gather the sources", "Write the brief"]'
        )
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                self.base_url + "/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT_GENERATE) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            text = data.get("response", "").strip()
            # Strip markdown fences
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            # Find JSON array
            m = re.search(r"\[.*\]", text, re.DOTALL)
            if m:
                proposals = json.loads(m.group(0))
                if isinstance(proposals, list) and len(proposals) >= 3:
                    return [str(p).strip() for p in proposals[:3]]
        except Exception:
            pass
        return None


# ── Gemini provider ────────────────────────────────────────────────────────────

class GeminiProvider:
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    def health(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus("gemini", False, "gemini-2.0-flash", error="no API key")
        return ProviderStatus("gemini", True, "gemini-2.0-flash")

    def propose(self, intent: str) -> Optional[List[str]]:
        if not self.api_key:
            return None
        try:
            from google import genai  # type: ignore
            client = genai.Client(api_key=self.api_key)
            prompt = (
                "You are HELEN, a calm non-sovereign AI OS.\n"
                f"The operator stated this intent: {intent}\n\n"
                "Generate exactly 3 concrete, actionable next steps. "
                "Each step should be a single sentence starting with a verb. "
                "Focus on real work — no philosophical framing.\n"
                'Return ONLY a JSON array of 3 strings. '
                'Example: ["Draft the outline", "Gather the sources", "Write the brief"]'
            )
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            raw = resp.text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            proposals = json.loads(raw)
            if isinstance(proposals, list) and len(proposals) >= 3:
                return [str(p).strip() for p in proposals[:3]]
        except Exception:
            pass
        return None


# ── Heuristic provider ─────────────────────────────────────────────────────────

class HeuristicProvider:
    def health(self) -> ProviderStatus:
        return ProviderStatus("heuristic", True, "keyword-templates")

    def propose(self, intent: str) -> List[str]:
        return _heuristic(intent)


# ── AMP Router ─────────────────────────────────────────────────────────────────

class AMPRouter:
    """
    Routes proposal requests to the best available provider.
    Priority: Ollama → Gemini → Heuristic.
    Always returns exactly 3 proposals.
    """

    def __init__(self, ollama_url: str = "", ollama_model: str = "",
                 gemini_key: str = "") -> None:
        self._ollama    = OllamaProvider(ollama_url, ollama_model)
        self._gemini    = GeminiProvider(gemini_key)
        self._heuristic = HeuristicProvider()
        self._last_ollama_status: Optional[ProviderStatus] = None

    def propose(self, intent: str) -> Tuple[List[str], str]:
        """Return (proposals, provider_name)."""
        # Try Ollama first
        s = self._ollama.health()
        self._last_ollama_status = s
        if s.online:
            result = self._ollama.propose(intent)
            if result:
                return result, "ollama"

        # Try Gemini
        if self._gemini.api_key:
            result = self._gemini.propose(intent)
            if result:
                return result, "gemini"

        # Heuristic fallback
        return self._heuristic.propose(intent), "heuristic"

    def status(self) -> Dict:
        """Return provider health status dict."""
        ollama_s  = self._last_ollama_status or self._ollama.health()
        gemini_s  = self._gemini.health()
        heuristic = self._heuristic.health()

        active = "heuristic"
        if ollama_s.online:
            active = "ollama"
        elif gemini_s.online:
            active = "gemini"

        return {
            "providers": [
                ollama_s.__dict__,
                gemini_s.__dict__,
                heuristic.__dict__,
            ],
            "active": active,
        }

    def status_lines(self) -> List[str]:
        """Return formatted status lines for terminal display."""
        s = self.status()
        lines = [
            DIM + "── AMP ─────────────────────────────────────────" + RESET,
        ]
        for p in s["providers"]:
            ps = ProviderStatus(**p)
            lines.append(ps.display())
        lines.append(
            f"  {'active':<12} {CYAN}{s['active']}{RESET}"
        )
        lines.append(DIM + "────────────────────────────────────────────────" + RESET)
        return lines


# ── CLI ────────────────────────────────────────────────────────────────────────

def _cmd_propose(args: list) -> int:
    if not args:
        print("Usage: helen_amp.py propose <intent>", file=sys.stderr)
        return 1
    intent = " ".join(args)
    router = AMPRouter()
    proposals, provider = router.propose(intent)
    print(f"\n  {CYAN}HELEN proposes{RESET} {DIM}(via {provider}){RESET}\n")
    for i, p in enumerate(proposals, 1):
        print(f"  [{i}]  {p}")
    print()
    return 0


def _cmd_status() -> int:
    router = AMPRouter()
    s = router.status()
    print()
    for line in router.status_lines():
        print(line)
    print()
    return 0


def _cmd_health() -> int:
    router = AMPRouter()
    s = router.status()
    active = s["active"]
    providers_online = [p["name"] for p in s["providers"] if p["online"]]
    print(f"\n  {GREEN}◆{RESET}  AMP  ·  active={CYAN}{active}{RESET}  ·  online={providers_online}")
    print()
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = args[0]
    rest = args[1:]
    if cmd == "propose":
        return _cmd_propose(rest)
    if cmd == "status":
        return _cmd_status()
    if cmd == "health":
        return _cmd_health()
    print(f"Unknown command: {cmd}. Use propose|status|health", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
