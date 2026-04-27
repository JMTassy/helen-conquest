#!/usr/bin/env python3
"""
HELEN Symbolic Classifier
==========================

Bridges cognition (Ollama/model) and governance (ledger/gate).

Input:  raw intent string from the operator
Output: {mode, confidence, reason, surface}

  mode:       focus | witness | oracle | temple
  confidence: 0.0–1.0
  reason:     one-line explanation
  surface:    the constitutional surface this intent belongs to

Mode definitions:
  focus   — working intent: prepare, build, write, review, send, check
  witness — proof/inspection intent: audit, verify, check ledger, show receipts
  oracle  — symbolic/research intent: explore, understand, what is, why
  temple  — creative/reflective intent: write a poem, journal, imagine, compose

Two-tier classification:
  1. Keyword rules (fast, deterministic, no model needed)
  2. Ollama model (when rules are uncertain — confidence < THRESHOLD)

The classifier is the bridge layer. It takes the model's understanding of
intent and routes it to the correct constitutional surface. The routing
decision is the moment where cognition becomes governance.

Usage as module:
  from tools.helen_symbolic_classifier import SymbolicClassifier
  clf = SymbolicClassifier()
  result = clf.classify("Prepare my Q3 strategy")
  # → {"mode": "focus", "confidence": 0.92, "reason": "...", "surface": "Focus Mode"}

Usage as CLI:
  python3 tools/helen_symbolic_classifier.py "Prepare my Q3 strategy"
  python3 tools/helen_symbolic_classifier.py --batch  # interactive batch mode
  python3 tools/helen_symbolic_classifier.py --observe <n>  # observe n intents, emit patterns

Authority: NON_SOVEREIGN
Classification is a proposal. The operator's confirmation is the authority.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Thresholds ─────────────────────────────────────────────────────────────────

_KEYWORD_CONFIDENCE_THRESHOLD = 0.75   # below this → escalate to model
_MODEL_TIMEOUT = 20                     # seconds

# ── ANSI ───────────────────────────────────────────────────────────────────────

RESET  = "\x1b[0m"
DIM    = "\x1b[2m"
CYAN   = "\x1b[36m"
GREEN  = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE   = "\x1b[34m"
MAGENTA = "\x1b[35m"

_MODE_COLOR = {
    "focus":   GREEN,
    "witness": YELLOW,
    "oracle":  CYAN,
    "temple":  MAGENTA,
}


# ── Classification result ──────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    mode: str               # focus | witness | oracle | temple
    confidence: float       # 0.0–1.0
    reason: str             # one-line explanation
    surface: str            # human label: "Focus Mode" | etc.
    provider: str           # "keyword" | "ollama" | "heuristic-fallback"
    raw_intent: str

    @property
    def color(self) -> str:
        return _MODE_COLOR.get(self.mode, DIM)

    def display(self) -> str:
        bar = "█" * int(self.confidence * 10) + "░" * (10 - int(self.confidence * 10))
        return (
            f"  {self.color}{self.surface:<14}{RESET}"
            f"  {DIM}{bar}{RESET}  {self.confidence:.0%}"
            f"  {DIM}{self.provider}{RESET}"
            f"\n  {DIM}{self.reason}{RESET}"
        )

    def to_dict(self) -> Dict:
        return asdict(self)


_SURFACE_LABELS = {
    "focus":   "Focus Mode",
    "witness": "Witness Mode",
    "oracle":  "Oracle Mode",
    "temple":  "Temple Mode",
}


# ── Keyword rules ──────────────────────────────────────────────────────────────
#
# Each rule is: (pattern, mode, confidence, reason_template)
# Patterns are checked in order. First match wins if confidence >= threshold.

_KEYWORD_RULES: List[Tuple[str, str, float, str]] = [
    # ── Witness / proof / inspection ─────────────────────────────────────────
    (r"\b(audit|verify|ledger|receipt|receipts|inspect|trace|prove|"
     r"replay|validation|gate\s+verdict|legoracle|cum_hash|seq\s*=|constitution|"
     r"k8|k-tau|k-rho|witness|proof|governance|schema|sovereign|"
     r"show\s+receipt|show\s+ledger|check\s+ledger)\b",
     "witness", 0.92,
     "intent contains inspection/governance vocabulary"),

    # ── Temple / creative / reflective ───────────────────────────────────────
    (r"\b(poem|poetry|journal|imagine|dream|compose|ritual|sacred|story|"
     r"creative|meditate|reflect\s+on|write\s+a\s+story|write\s+a\s+poem|"
     r"contemplat|manifesto|vision)\b",
     "temple", 0.90,
     "intent contains creative or reflective vocabulary"),

    # ── Oracle / symbolic / research ─────────────────────────────────────────
    (r"\b(what\s+is|why\s+is|how\s+does|explain|understand|meaning\s+of|"
     r"explore|research\s+the\s+concept|philosophy|pattern\s+of|"
     r"insight|symbolic|metaphor|theory|thesis)\b",
     "oracle", 0.82,
     "intent is a conceptual or explanatory inquiry"),

    # ── Focus / work ─────────────────────────────────────────────────────────
    (r"\b(prepare|draft|write|build|send|review|check|update|organise|organize|"
     r"plan|schedule|finish|complete|compile|deploy|ship|test|fix|debug|"
     r"create|design|analyse|analyze|research\s+competitor|brief|summarise|"
     r"summarize|meeting|email|task|project|sprint|roadmap|strategy|report)\b",
     "focus", 0.85,
     "intent is a concrete work action"),
]


def _keyword_classify(intent: str) -> Optional[ClassificationResult]:
    """Fast keyword match. Returns None if no rule reaches confidence threshold."""
    text = intent.lower().strip()
    best: Optional[ClassificationResult] = None
    best_conf = 0.0

    for pattern, mode, base_conf, reason in _KEYWORD_RULES:
        matches = re.findall(pattern, text, re.I)
        if not matches:
            continue
        # Boost confidence for multiple distinct matches
        conf = min(base_conf + 0.02 * (len(matches) - 1), 0.99)
        if conf > best_conf:
            best_conf = conf
            best = ClassificationResult(
                mode=mode,
                confidence=conf,
                reason=reason + f" ({', '.join(set(matches[:3]))})",
                surface=_SURFACE_LABELS[mode],
                provider="keyword",
                raw_intent=intent,
            )

    if best and best.confidence >= _KEYWORD_CONFIDENCE_THRESHOLD:
        return best
    return None


# ── Ollama classifier ──────────────────────────────────────────────────────────

def _ollama_classify(intent: str, base_url: str, model: str) -> Optional[ClassificationResult]:
    """Ask Ollama to classify the intent. Returns None on failure."""
    prompt = (
        "You are a routing classifier for HELEN OS.\n"
        "Classify this user intent into exactly one of four modes:\n\n"
        "  focus   — a concrete work task (prepare, write, review, build, send, check, plan)\n"
        "  witness — an inspection or proof request (audit, verify, show receipts, check ledger)\n"
        "  oracle  — a conceptual inquiry (what is, why, explain, explore an idea)\n"
        "  temple  — a creative or reflective intent (poem, journal, imagine, compose)\n\n"
        f"Intent: \"{intent}\"\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        '{"mode": "focus", "confidence": 0.9, "reason": "one sentence"}\n'
        "No other text."
    )
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            base_url.rstrip("/") + "/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_MODEL_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        text = data.get("response", "").strip()
        # Extract JSON from response
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        m = re.search(r"\{[^}]+\}", text, re.DOTALL)
        if not m:
            return None
        result = json.loads(m.group(0))
        mode = str(result.get("mode", "focus")).lower().strip()
        if mode not in _SURFACE_LABELS:
            mode = "focus"
        conf = float(result.get("confidence", 0.7))
        conf = max(0.0, min(1.0, conf))
        reason = str(result.get("reason", "model classification"))
        return ClassificationResult(
            mode=mode,
            confidence=conf,
            reason=reason,
            surface=_SURFACE_LABELS[mode],
            provider="ollama",
            raw_intent=intent,
        )
    except Exception:
        return None


# ── Heuristic fallback ─────────────────────────────────────────────────────────

def _heuristic_fallback(intent: str) -> ClassificationResult:
    """Always returns a result. Default = focus."""
    # Short intents with questions → oracle
    text = intent.lower().strip()
    if text.startswith(("what", "why", "how", "who", "where", "when", "explain")):
        return ClassificationResult(
            mode="oracle", confidence=0.60,
            reason="intent begins with a question word",
            surface=_SURFACE_LABELS["oracle"],
            provider="heuristic-fallback", raw_intent=intent,
        )
    return ClassificationResult(
        mode="focus", confidence=0.55,
        reason="default: no clear signal, assuming work intent",
        surface=_SURFACE_LABELS["focus"],
        provider="heuristic-fallback", raw_intent=intent,
    )


# ── Symbolic Classifier ────────────────────────────────────────────────────────

class SymbolicClassifier:
    """
    Two-tier intent classifier.
    Tier 1: fast keyword rules (deterministic)
    Tier 2: Ollama model (when keyword confidence is insufficient)
    Fallback: heuristic default
    """

    def __init__(self, ollama_url: str = "", ollama_model: str = "") -> None:
        self.ollama_url   = ollama_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = ollama_model or os.environ.get("OLLAMA_MODEL", "gemma3:1b")
        self._ollama_available: Optional[bool] = None  # lazy health check

    def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            req = urllib.request.Request(self.ollama_url.rstrip("/") + "/", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                resp.read()
            self._ollama_available = True
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def classify(self, intent: str) -> ClassificationResult:
        """Classify an intent. Always returns a result."""
        intent = intent.strip()
        if not intent:
            return _heuristic_fallback(intent)

        # Tier 1: keyword rules
        result = _keyword_classify(intent)
        if result is not None:
            return result

        # Tier 2: Ollama model (when keyword confidence insufficient)
        if self._check_ollama():
            result = _ollama_classify(intent, self.ollama_url, self.ollama_model)
            if result is not None:
                return result

        # Fallback
        return _heuristic_fallback(intent)

    def classify_batch(self, intents: List[str]) -> List[ClassificationResult]:
        return [self.classify(i) for i in intents]

    def observe(self, intents: List[str]) -> Dict:
        """
        Classify a list of intents and emit an observation report.
        Used for PULL-mode pattern discovery: observe what the model proposes,
        then write rules from what you see.
        """
        results = self.classify_batch(intents)
        from collections import Counter
        mode_counts = Counter(r.mode for r in results)
        provider_counts = Counter(r.provider for r in results)
        avg_conf = sum(r.confidence for r in results) / len(results) if results else 0.0
        patterns = {}
        for r in results:
            if r.mode not in patterns:
                patterns[r.mode] = []
            patterns[r.mode].append(r.raw_intent)
        return {
            "total": len(results),
            "mode_distribution": dict(mode_counts),
            "provider_distribution": dict(provider_counts),
            "avg_confidence": round(avg_conf, 3),
            "patterns": patterns,
        }


# ── CLI ────────────────────────────────────────────────────────────────────────

def _cmd_classify(intent: str) -> int:
    clf = SymbolicClassifier()
    result = clf.classify(intent)
    print()
    print(f"  Intent:  {DIM}{result.raw_intent}{RESET}")
    print(result.display())
    print()
    return 0


def _cmd_batch() -> int:
    clf = SymbolicClassifier()
    print(f"\n  {DIM}Enter intents one per line. Empty line to finish.{RESET}\n")
    intents = []
    while True:
        try:
            line = input(f"  {CYAN}›{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            break
        intents.append(line)

    if not intents:
        return 0

    results = clf.classify_batch(intents)
    print()
    for r in results:
        print(f"  {DIM}{r.raw_intent[:50]:<52}{RESET}")
        print(r.display())
        print()
    return 0


def _cmd_observe(n: int) -> int:
    clf = SymbolicClassifier()
    print(f"\n  {DIM}Enter {n} intents. HELEN will observe and report patterns.{RESET}\n")
    intents = []
    for i in range(n):
        try:
            line = input(f"  {CYAN}[{i+1}/{n}]{RESET} › ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line:
            intents.append(line)

    if not intents:
        return 0

    report = clf.observe(intents)
    print()
    print(f"  {DIM}── OBSERVATION REPORT ──────────────────────────────{RESET}")
    print(f"  Intents observed:    {report['total']}")
    print(f"  Avg confidence:      {report['avg_confidence']:.0%}")
    print()
    print(f"  Mode distribution:")
    for mode, count in sorted(report["mode_distribution"].items(),
                              key=lambda x: -x[1]):
        color = _MODE_COLOR.get(mode, DIM)
        bar = "█" * count
        print(f"    {color}{mode:<10}{RESET}  {bar}  ({count})")
    print()
    print(f"  Provider distribution:")
    for provider, count in sorted(report["provider_distribution"].items(),
                                   key=lambda x: -x[1]):
        print(f"    {DIM}{provider:<20}{RESET}  {count}")
    print()
    # Emit patterns as JSON — these are the raw material for rule refinement
    print(f"  {DIM}Patterns (raw material for rule refinement):{RESET}")
    print(f"  {DIM}{json.dumps(report['patterns'], indent=2, ensure_ascii=False)}{RESET}")
    print()
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    if args[0] == "--batch":
        return _cmd_batch()

    if args[0] == "--observe":
        n = int(args[1]) if len(args) > 1 else 10
        return _cmd_observe(n)

    # Single intent
    intent = " ".join(args)
    return _cmd_classify(intent)


if __name__ == "__main__":
    sys.exit(main())
