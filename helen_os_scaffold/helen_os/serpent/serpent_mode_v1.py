# helen_os/serpent/serpent_mode_v1.py
#
# SERPENT_MODE_V1 parser + normalizer + renderer (sanitised)
# Input:  raw run text (CWL/EMOGLYPH page)
# Output: AST dict conforming to SERPENT_MODE_V1 schema
#
# IMPORTANT: run_trace ONLY (non-sovereign telemetry / UI).
#            Never write this AST to memory.ndjson or the sovereign ledger.

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional

# ── Station extraction ─────────────────────────────────────────────────────
SID_RE = re.compile(r"🔗#(S[0-9][A-Z0-9]{2})\b")

MAJOR_TOKENS = [
    "🌍", "🌟", "🔥", "⚖️", "🪄", "🌙", "☀️", "🗼", "🎺", "👑",
    "🦁", "⭐", "🃏", "🔒", "📜",
]

OPERATORS = ["🜃", "🜄", "🜁", "🜂", "🜍", "🜔", "🜉"]

NAME_BY_TOKEN: Dict[str, str] = {
    "🌍": "World",
    "🌟": "Star",
    "🔥": "Strength",
    "⚖️": "Justice",
    "🪄": "Magician",
    "🌙": "Priestess",
    "☀️": "Sun",
    "🗼": "Tower",
    "🎺": "Judgement",
    "👑": "Crown",
}

DEFAULT_OPERATORS: Dict[str, str] = {
    "🜃": "anchor",
    "🜄": "dissolve",
    "🜁": "elevate",
    "🜂": "cut",
    "🜍": "impetus",
    "🜔": "corpus",
    "🜉": "unknown",
}

# ── Domain state extraction ────────────────────────────────────────────────
COLOR_TO_STATE: Dict[str, str] = {
    "🟢": "stable",
    "🟡": "rising",
    "🔴": "critical",
}

# ── Sanitization policy (run_trace rewrite — keeps style, neutralises authority) ──
RUNTRACE_REWRITE = [
    ("Sovereign decree", "User intent"),
    ("SEAL",             "MARK"),
    ("VERDICT",          "OBSERVED"),
    ("GATE: PASSED",     "CHECK: OK"),
    ("CERTIFICATE",      "METRIC"),
    ("IRREVERSIBLE",     "NON_REVERSIBLE_STYLE"),
    ("LEDGER",           "TRACE"),
]


def sanitize_run_trace_text(text: str) -> str:
    """Rewrite authority lexemes to run_trace-safe equivalents."""
    out = text
    for src, dst in RUNTRACE_REWRITE:
        out = out.replace(src, dst)
    return out


# ── Helpers ────────────────────────────────────────────────────────────────

def _first_present(haystack: str, needles: List[str]) -> Optional[str]:
    for n in needles:
        if n in haystack:
            return n
    return None


# ── Station parser ─────────────────────────────────────────────────────────

def parse_stations(raw: str) -> List[Dict[str, Any]]:
    """
    Extract ordered station list from raw EMOGLYPH text.
    A station line must contain a 🔗#Sx?? anchor.
    Deterministic: same raw => same output.
    """
    stations: List[Dict[str, Any]] = []
    for line in raw.splitlines():
        m = SID_RE.search(line)
        if not m:
            continue
        sid = m.group(1)

        token = _first_present(line, MAJOR_TOKENS) or "?"
        name  = NAME_BY_TOKEN.get(token, "World")
        op    = _first_present(line, OPERATORS) or "🜃"  # deterministic fallback

        stations.append({
            "i":        len(stations) + 1,   # appearance order = canonical index
            "token":    token,
            "name":     name,
            "operator": op,
            "tags":     [],
            "sid":      sid,
        })

    if not stations:
        raise ValueError(
            "SERPENT_MODE_V1 parse: no stations found "
            "(expected lines with 🔗#S<digit><2 alphanum>)."
        )
    return stations


# ── Domain state parser ────────────────────────────────────────────────────

def _extract_domain_state(raw: str) -> Dict[str, str]:
    """
    Scan lines for domain labels + colour indicators.
    Conservative defaults: stable for all.
    """
    state = {
        "alchemical":     "stable",
        "ai_art":         "stable",
        "infrastructure": "stable",
        "chaos":          "stable",
    }
    for line in raw.splitlines():
        lower = line.lower()
        col   = _first_present(line, ["🟢", "🟡", "🔴"])
        if not col:
            continue
        mapped = COLOR_TO_STATE[col]

        if "alchemical" in lower:
            state["alchemical"] = mapped
        elif "ai art" in lower or "ai_art" in lower or "art pipeline" in lower:
            state["ai_art"] = mapped
        elif "infrastructure" in lower:
            state["infrastructure"] = mapped
        elif "chaos" in lower:
            state["chaos"] = mapped

    return state


# ── Public API ─────────────────────────────────────────────────────────────

def build_serpent_ast(raw_text: str, epoch: int = 0) -> Dict[str, Any]:
    """
    Parse raw EMOGLYPH feuillet into SERPENT_MODE_V1 AST.
    Deterministic: same raw_text + epoch => identical dict.
    Output channel: run_trace (non-sovereign).
    """
    stations     = parse_stations(raw_text)
    domain_state = _extract_domain_state(raw_text)
    operators    = dict(DEFAULT_OPERATORS)  # fixed mapping; extend via config if needed

    return {
        "schema_version": "SERPENT_MODE_V1",
        "epoch":          int(epoch),
        "mode":           "SERPENT_ASCENT",
        "stations":       stations,
        "domain_state":   domain_state,
        "operators":      operators,
        "notes":          {"channel": "run_trace", "authority": False},
    }


def render_serpent_panel(ast: Dict[str, Any]) -> str:
    """
    Pretty CLI display of the SERPENT_MODE_V1 AST.
    NON-SOVEREIGN — display only.
    """
    lines = []
    lines.append("🟡 SERPENT_MODE_V1  (run_trace · non-sovereign)")
    lines.append(f"   epoch={ast.get('epoch')}  mode={ast.get('mode')}")
    lines.append("")
    lines.append("   stations:")
    for st in ast["stations"]:
        lines.append(
            f"     {st['i']:02d}. {st['token']}  {st['name']:<12} "
            f"op={st['operator']}  sid={st['sid']}"
        )
    ds = ast["domain_state"]
    lines.append("")
    lines.append("   domain_state:")
    lines.append(
        f"     alchemical={ds['alchemical']}  ai_art={ds['ai_art']}  "
        f"infrastructure={ds['infrastructure']}  chaos={ds['chaos']}"
    )
    lines.append("")
    lines.append("   notes: channel=run_trace  authority=false")
    return "\n".join(lines)
