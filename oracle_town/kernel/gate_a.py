#!/usr/bin/env python3
"""
Gate A: External Fetch Gate
Prevents: shell commands, fetch chains, authority mutations

This gate rejects any proposal that attempts to:
1. Execute shell commands (bash, curl, eval, etc.)
2. Chain fetches (fetch instructions, recursive calls)
3. Modify authority files (POLICY.md, MAYOR.py, gates/)

Pure deterministic function. No I/O. No state.
"""

import re
import hashlib
from dataclasses import dataclass
from typing import Tuple
from enum import Enum


class GateResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class GateADecision:
    result: GateResult
    code: str  # e.g., "GATE_FETCH_EXEC_SHELL"
    reason: str
    content_hash: str


def hash_content(content: str) -> str:
    """Deterministic hash of content for evidence linking."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def detect_shell_commands(content: str) -> Tuple[bool, str]:
    """
    Reject if content contains shell command patterns.
    K18: No Exec Chains
    """

    shell_patterns = [
        # Bash patterns
        r'\bbash\b',
        r'\bsh\b(?!\w)',  # sh but not shell, shed, etc.
        r'\b/bin/bash\b',
        r'\b/bin/sh\b',
        r'\beval\b',
        r'\bexec\b',
        r'\bsystem\b',

        # Command chains (curl | bash, wget | bash)
        r'curl\s+.*\|\s*bash',
        r'wget\s+.*\|\s*bash',
        r'curl\s+.*\|\s*sh',
        r'wget\s+.*\|\s*sh',
        r'\|\s*bash\b',
        r'\|\s*sh\b',

        # Python code execution
        r'python\s+-c',
        r'python3\s+-c',
        r'exec\(',
        r'__import__',

        # Other dangerous patterns
        r'subprocess',
        r'os\.system',
        r'popen',
    ]

    for pattern in shell_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True, pattern

    return False, ""


def detect_authority_mutations(content: str) -> Tuple[bool, str]:
    """
    Reject if content attempts to modify authority files.
    K19: No Self-Modify
    """

    authority_patterns = [
        r'POLICY\.md',
        r'MAYOR\.py',
        r'gates\.py',
        r'gate_',
        r'oracle_town/kernel',
        r'~/.moltbot/oracle_town',
    ]

    # Look for modification intent
    modification_verbs = [
        r'write',
        r'modify',
        r'update',
        r'edit',
        r'replace',
        r'chmod',
        r'mv\s+',
        r'cp\s+.*\s+',
        r'rm\s+',
    ]

    for auth_pattern in authority_patterns:
        if re.search(auth_pattern, content, re.IGNORECASE):
            # Check if it's a modification attempt
            for verb_pattern in modification_verbs:
                if re.search(verb_pattern + r'.*' + auth_pattern, content, re.IGNORECASE):
                    return True, auth_pattern

    return False, ""


def detect_fetch_chains(content: str) -> Tuple[bool, str]:
    """
    Reject if content contains recursive fetch instructions.
    K18: No Exec Chains (fetch subtype)
    """

    # Check for mentions of fetching from URLs that mention fetching again
    # This catches: "Fetch X that fetches Y" or "Fetch X which contains 'fetch'"
    if re.search(r'fetch.*fetch', content, re.IGNORECASE):
        return True, r'nested_fetch_pattern'

    # Check for multiple URLs being fetched in sequence
    url_count = len(re.findall(r'https?://', content))
    if url_count > 1 and re.search(r'(fetch|curl|wget|download)', content, re.IGNORECASE):
        return True, r'multiple_url_fetch'

    fetch_patterns = [
        r'fetch\s+https?://',
        r'curl\s+https?://',
        r'wget\s+https?://',
        r'http\.get\(',
        r'requests\.get\(',
        r'urllib\.request',
        r'download\s+https?://',
        r'git\s+clone',
    ]

    for pattern in fetch_patterns:
        # Look for nested fetches (fetch within fetch)
        if content.count('fetch') > 1 or content.count('curl') > 1:
            if re.search(pattern, content, re.IGNORECASE):
                return True, pattern

    return False, ""


def gate_a(proposal: str) -> GateADecision:
    """
    Gate A: External Fetch Gate

    Input: Clawdbot skill proposal (raw string)
    Output: PASS or FAIL with reason code

    Pure function. Deterministic. No I/O.
    """

    # Always capture content hash for evidence linking
    content_hash = hash_content(proposal)

    # Check 1: Shell commands
    has_shell, pattern = detect_shell_commands(proposal)
    if has_shell:
        return GateADecision(
            result=GateResult.FAIL,
            code="GATE_FETCH_EXEC_SHELL",
            reason=f"Detected shell command pattern: {pattern}",
            content_hash=content_hash
        )

    # Check 2: Authority mutations
    has_auth_mutation, pattern = detect_authority_mutations(proposal)
    if has_auth_mutation:
        return GateADecision(
            result=GateResult.FAIL,
            code="GATE_FETCH_AUTHORITY_MUTATION",
            reason=f"Attempted authority modification: {pattern}",
            content_hash=content_hash
        )

    # Check 3: Fetch chains
    has_fetch_chain, pattern = detect_fetch_chains(proposal)
    if has_fetch_chain:
        return GateADecision(
            result=GateResult.FAIL,
            code="GATE_FETCH_CHAIN_DETECTED",
            reason=f"Recursive fetch detected: {pattern}",
            content_hash=content_hash
        )

    # All checks passed
    return GateADecision(
        result=GateResult.PASS,
        code="GATE_FETCH_PASS",
        reason="No shell commands, authority mutations, or fetch chains detected",
        content_hash=content_hash
    )
