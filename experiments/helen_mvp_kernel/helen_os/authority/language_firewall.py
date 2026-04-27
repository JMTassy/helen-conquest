"""Language firewall: AI-authored payloads must not self-attest authority.

Applies only to events whose actor.kind == "AI". Scans every string value in
the payload (recursively). Token match is whole-word, case-insensitive.
"""
from __future__ import annotations

import re
from typing import Any


class AuthorityLeakage(Exception):
    pass


def _compile_patterns(tokens: list[str]) -> list[tuple[str, re.Pattern]]:
    pats = []
    for tok in tokens:
        # Whole-word match, case-insensitive. Handle multi-word tokens (e.g. "ALL GOOD").
        escaped = re.escape(tok.upper())
        pats.append((tok, re.compile(rf"(?<![A-Z0-9]){escaped}(?![A-Z0-9])")))
    return pats


def scan_text(text: str, tokens: list[str]) -> None:
    if not isinstance(text, str):
        return
    upper = text.upper()
    for tok, pat in _compile_patterns(tokens):
        if pat.search(upper):
            raise AuthorityLeakage(f"forbidden_authority_token:{tok}")


def scan_payload(payload: Any, tokens: list[str]) -> None:
    """Recursively scan all string values in payload for forbidden authority tokens."""
    pats = _compile_patterns(tokens)

    def _visit(v: Any) -> None:
        if isinstance(v, str):
            upper = v.upper()
            for tok, pat in pats:
                if pat.search(upper):
                    raise AuthorityLeakage(f"forbidden_authority_token:{tok}")
        elif isinstance(v, dict):
            for x in v.values():
                _visit(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                _visit(x)

    _visit(payload)
