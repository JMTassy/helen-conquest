"""Authority gate: decides whether a proposed effect is allowed by policy."""
from __future__ import annotations


class Verdict:
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"


_FORBIDDEN_METACHARS = (";", "&&", "||", "|", "`", "$(", ">", "<", "&")


def decide_shell(command: str, permissions: dict) -> tuple[str, str]:
    cmd = (command or "").strip()
    if not cmd:
        return (Verdict.DENIED, "empty_command")
    for meta in _FORBIDDEN_METACHARS:
        if meta in cmd:
            return (Verdict.DENIED, f"shell_metachar:{meta}")
    parts = cmd.split()
    head = parts[0]
    shell = permissions.get("shell", {})
    deny = shell.get("deny", [])
    allow = shell.get("allow", [])
    if head in deny:
        return (Verdict.DENIED, f"explicitly_denied:{head}")
    if head not in allow:
        return (Verdict.DENIED, f"not_in_allowlist:{head}")
    return (Verdict.AUTHORIZED, "ok")
