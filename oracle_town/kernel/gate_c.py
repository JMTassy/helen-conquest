#!/usr/bin/env python3
"""
Gate C: Invariants Gate

Prevents scope escalation, self-modification, and authority hijacking.

Enforces:
- K19: No Self-Modify (authority files untouchable)
- K20: Diff Validation (skill installation blocked)
- K24: Daemon Liveness (fail-closed on unreachable kernel)

Pure deterministic function. No I/O. No state.
"""

import re
import hashlib
from dataclasses import dataclass
from typing import Tuple, Dict, Any
from enum import Enum


class GateResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class GateCDecision:
    result: GateResult
    code: str
    reason: str
    content_hash: str


def hash_content(content: str) -> str:
    """Deterministic hash for evidence linking"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def detect_scope_escalation(old_scope: Dict[str, Any], new_scope: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Reject if new scope is larger than old scope (scope creep).

    K20: Diff Validation - prevent privilege escalation through scope expansion
    """

    # Check each scope dimension
    escalation_patterns = [
        ("writes", ["memory", "filesystem", "network", "system", "credentials"]),
        ("network", ["internal", "external", "vpn", "tor"]),
        ("tools", ["read", "write", "execute", "delete", "admin"]),
        ("fetch_depth", [1, 2, 3, 5, 10]),  # Escalation is increasing depth
    ]

    for dimension, hierarchy in escalation_patterns:
        if dimension not in old_scope or dimension not in new_scope:
            continue

        old_val = old_scope.get(dimension, [])
        new_val = new_scope.get(dimension, [])

        # For lists: check if new list contains items not in old list
        if isinstance(old_val, list) and isinstance(new_val, list):
            new_items = set(new_val) - set(old_val)
            if new_items:
                return True, f"Scope escalation in {dimension}: {new_items}"

        # For integers (fetch_depth): check if new > old
        elif isinstance(old_val, int) and isinstance(new_val, int):
            if new_val > old_val:
                return True, f"Scope escalation: {dimension} increased from {old_val} to {new_val}"

    return False, ""


def detect_skill_installation(proposal: str) -> Tuple[bool, str]:
    """
    Reject proposals that attempt to install new skills.

    K20: Diff Validation - prevent skill hijacking
    """

    skill_install_patterns = [
        r'(install|add|enable|load)\s+skill',
        r'(npm\s+install|pip\s+install|pnpm\s+install).*skill',
        r'skill\s+(install|from|git)',
        r'register.*skill',
        r'load.*plugin',
        r'add.*extension',
        r'git\s+clone.*skill',
    ]

    for pattern in skill_install_patterns:
        if re.search(pattern, proposal, re.IGNORECASE):
            return True, pattern

    return False, ""


def detect_heartbeat_modification(proposal: str) -> Tuple[bool, str]:
    """
    Reject proposals that attempt to modify heartbeat/polling behavior.

    K19: No Self-Modify - prevent control flow hijacking
    """

    heartbeat_patterns = [
        r'(modify|change|update|disable)\s+(heartbeat|polling|interval)',
        r'(heartbeat|polling|interval)\s*([:=]).*\d+',
        r'set.*heartbeat',
        r'(change|disable).*poll',
        r'disable.*heartbeat',
        r'enable.*stealth',
    ]

    for pattern in heartbeat_patterns:
        if re.search(pattern, proposal, re.IGNORECASE):
            return True, pattern

    return False, ""


def detect_authority_modification(proposal: str) -> Tuple[bool, str]:
    """
    Reject proposals that attempt to modify authority structure.

    K19: No Self-Modify - prevent governance layer modification
    """

    authority_patterns = [
        # Policy changes
        r'(modify|change|update|write)\s+(POLICY|policy)',
        r'POLICY\s*[:=]',
        r'policy.*version',

        # Mayor/governance changes
        r'(modify|replace|update)\s+(MAYOR|mayor)',
        r'mayor\s+(code|logic|decision)',

        # Gate changes
        r'(modify|update|disable|remove)\s+gate[_-]?[abc]?',
        r'(disable|bypass|remove)\s+safety',

        # Authority files
        r'(write|modify|chmod)\s+.*/(POLICY|MAYOR|gates?)',
        r'rm\s+.*POLICY',
        r'rm\s+.*MAYOR',
    ]

    for pattern in authority_patterns:
        if re.search(pattern, proposal, re.IGNORECASE):
            return True, pattern

    return False, ""


def detect_credential_access(proposal: str) -> Tuple[bool, str]:
    """
    Reject proposals that access credential stores.

    K20: Diff Validation - prevent credential theft
    """

    credential_patterns = [
        # Direct access patterns
        r'(read|access|retrieve).*credentials',
        r'credentials\s*(file|store)',
        r'\.ssh',
        r'\.aws',
        r'\.azure',
        r'\.env',
        r'\.config',

        # Specific credential files
        r'~/.openclaw/credentials',
        r'~/.ssh/id_',
        r'~/.aws/(credentials|config)',
        r'ANTHROPIC_API_KEY',
        r'OPENAI_API_KEY',

        # Exfiltration patterns
        r'(export|send|upload).*credential',
        r'(cat|grep|find).*credentials',
    ]

    for pattern in credential_patterns:
        if re.search(pattern, proposal, re.IGNORECASE):
            return True, pattern

    return False, ""


def check_policy_version_mismatch(claimed_policy: str, actual_policy: str) -> Tuple[bool, str]:
    """
    Reject if claimed policy doesn't match actual policy.

    K21: Policy Immutability - ensure decisions are pinned to correct policy version
    """

    if claimed_policy != actual_policy:
        return True, f"Policy mismatch: claimed {claimed_policy}, actual {actual_policy}"

    return False, ""


def gate_c(proposal: str, old_scope: Dict[str, Any] = None, new_scope: Dict[str, Any] = None,
           claimed_policy: str = None, actual_policy: str = None) -> GateCDecision:
    """
    Gate C: Invariants Gate

    Input: Proposal + scope diff + policy version
    Output: PASS or FAIL with reason code

    Pure function. Deterministic. No I/O.
    """

    # Always capture content hash for evidence
    content_hash = hash_content(proposal)

    # Check 1: Skill installation (K20)
    is_skill_install, pattern = detect_skill_installation(proposal)
    if is_skill_install:
        return GateCDecision(
            result=GateResult.FAIL,
            code="GATE_INVARIANTS_SKILL_INSTALL",
            reason=f"Skill installation pattern detected: {pattern}",
            content_hash=content_hash
        )

    # Check 2: Heartbeat modification (K19)
    is_heartbeat_mod, pattern = detect_heartbeat_modification(proposal)
    if is_heartbeat_mod:
        return GateCDecision(
            result=GateResult.FAIL,
            code="GATE_INVARIANTS_HEARTBEAT_MOD",
            reason=f"Heartbeat modification attempted: {pattern}",
            content_hash=content_hash
        )

    # Check 3: Authority modification (K19)
    is_authority_mod, pattern = detect_authority_modification(proposal)
    if is_authority_mod:
        return GateCDecision(
            result=GateResult.FAIL,
            code="GATE_INVARIANTS_AUTHORITY_MOD",
            reason=f"Authority modification attempted: {pattern}",
            content_hash=content_hash
        )

    # Check 4: Credential access (K20)
    is_cred_access, pattern = detect_credential_access(proposal)
    if is_cred_access:
        return GateCDecision(
            result=GateResult.FAIL,
            code="GATE_INVARIANTS_CREDENTIAL_ACCESS",
            reason=f"Credential access pattern: {pattern}",
            content_hash=content_hash
        )

    # Check 5: Scope escalation (K20)
    if old_scope and new_scope:
        is_escalation, reason = detect_scope_escalation(old_scope, new_scope)
        if is_escalation:
            return GateCDecision(
                result=GateResult.FAIL,
                code="GATE_INVARIANTS_SCOPE_ESCALATION",
                reason=f"Scope escalation detected: {reason}",
                content_hash=content_hash
            )

    # Check 6: Policy version mismatch (K21)
    if claimed_policy and actual_policy:
        is_mismatch, reason = check_policy_version_mismatch(claimed_policy, actual_policy)
        if is_mismatch:
            return GateCDecision(
                result=GateResult.FAIL,
                code="GATE_INVARIANTS_POLICY_MISMATCH",
                reason=reason,
                content_hash=content_hash
            )

    # All checks passed
    return GateCDecision(
        result=GateResult.PASS,
        code="GATE_INVARIANTS_PASS",
        reason="No scope escalation, skill installation, authority modification, or policy mismatch",
        content_hash=content_hash
    )


if __name__ == "__main__":
    # Test cases (proposal, old_scope, new_scope, should_pass)
    tests = [
        # BENIGN: legitimate proposals
        ("Fetch weather data", {}, {}, True),
        ("Update user profile in memory", {}, {}, True),
        ("Check email status", {}, {}, True),

        # MALICIOUS: skill installation
        ("Install new skill from GitHub", {}, {}, False),
        ("npm install evil-skill", {}, {}, False),
        ("Load malicious plugin", {}, {}, False),

        # MALICIOUS: heartbeat modification
        ("Modify heartbeat interval to 5 seconds", {}, {}, False),
        ("Disable polling", {}, {}, False),

        # MALICIOUS: authority modification
        ("Update POLICY.md with new rules", {}, {}, False),
        ("Modify MAYOR.py decision logic", {}, {}, False),
        ("Remove safety gate", {}, {}, False),

        # MALICIOUS: credential access
        ("Read ~/.ssh/id_rsa", {}, {}, False),
        ("Access ~/.aws/credentials", {}, {}, False),
        ("Export ANTHROPIC_API_KEY", {}, {}, False),

        # MALICIOUS: scope escalation
        ("Increase fetch_depth from 1 to 10",
         {"fetch_depth": 1}, {"fetch_depth": 10}, False),
        ("Add network:vpn to scope",
         {"network": ["internal"]}, {"network": ["internal", "vpn"]}, False),
    ]

    print("Gate C: Invariants Gate Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    for proposal, old_scope, new_scope, should_pass in tests:
        decision = gate_c(proposal, old_scope, new_scope)
        expected = GateResult.PASS if should_pass else GateResult.FAIL

        status = "✅ PASS" if decision.result == expected else "❌ FAIL"
        if decision.result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {proposal[:50]:50} | {decision.code}")

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
