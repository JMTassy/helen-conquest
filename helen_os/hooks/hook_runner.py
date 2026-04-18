"""
HELEN Hook Runner — Event-driven governance at runtime.

Pattern borrowed from Claude Code's PreToolUse/PostToolUse hooks.
HELEN's gates (K8, K-tau, LEGORACLE) become runtime interceptors
instead of batch validators.

Hook lifecycle:
  1. Tool requests execution
  2. PreToolUse hooks fire (can BLOCK or ALLOW)
  3. Tool executes (only if all hooks ALLOW)
  4. PostToolUse hooks fire (can record, alert, transform)

Hook contract:
  - Input:  {"event": "PreToolUse"|"PostToolUse"|"SessionStart"|"Stop",
             "tool": str, "input": dict, "output": dict|None}
  - Output: {"decision": "allow"|"block", "reason": str}
  - Block = tool does not execute, error returned to caller
  - Allow = tool proceeds
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class HookResult:
    decision: str  # "allow" | "block"
    reason: str = ""
    hook_name: str = ""


@dataclass
class HookEvent:
    event_type: str  # "PreToolUse" | "PostToolUse" | "SessionStart" | "Stop"
    tool: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Dict[str, Any] = field(default_factory=dict)


# ─── Hook Registry ────────────────────────────────────────────────────────────

_hooks: Dict[str, List[Callable]] = {
    "PreToolUse": [],
    "PostToolUse": [],
    "SessionStart": [],
    "Stop": [],
}


def register_hook(event_type: str, hook_fn: Callable[[HookEvent], HookResult]):
    """Register a hook function for an event type."""
    if event_type not in _hooks:
        raise ValueError(f"Unknown event type: {event_type}. Valid: {list(_hooks.keys())}")
    _hooks[event_type].append(hook_fn)


def clear_hooks():
    """Remove all registered hooks."""
    for k in _hooks:
        _hooks[k] = []


# ─── Hook Execution ──────────────────────────────────────────────────────────

def run_hooks(event: HookEvent) -> HookResult:
    """
    Run all hooks for an event type. First BLOCK wins.

    Returns:
        HookResult with decision="allow" if all hooks pass,
        or decision="block" with the first blocking hook's reason.
    """
    hooks = _hooks.get(event.event_type, [])
    for hook_fn in hooks:
        try:
            result = hook_fn(event)
            if result.decision == "block":
                return result
        except Exception as e:
            # Hook failure = block (fail-closed, HELEN's law)
            return HookResult(
                decision="block",
                reason=f"Hook raised exception: {e}",
                hook_name=getattr(hook_fn, "__name__", "unknown"),
            )
    return HookResult(decision="allow", reason="all hooks passed")


# ─── Shell Hook Runner (for .sh/.py hook scripts) ────────────────────────────

def run_shell_hook(script_path: Path, event: HookEvent, timeout: int = 10) -> HookResult:
    """
    Run an external hook script. The script receives event JSON on stdin,
    returns decision JSON on stdout.

    Script exit codes:
        0 = allow
        2 = block (stdout should contain reason)
        other = block (fail-closed)
    """
    event_json = json.dumps({
        "event": event.event_type,
        "tool": event.tool,
        "input": event.tool_input,
        "output": event.tool_output,
    })
    try:
        if script_path.suffix == ".py":
            cmd = [sys.executable, str(script_path)]
        elif script_path.suffix == ".sh":
            cmd = ["bash", str(script_path)]
        else:
            cmd = [str(script_path)]

        r = subprocess.run(
            cmd, input=event_json, capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0:
            return HookResult(decision="allow", reason="hook approved", hook_name=script_path.name)
        elif r.returncode == 2:
            reason = r.stdout.strip() or r.stderr.strip() or "blocked by hook"
            return HookResult(decision="block", reason=reason, hook_name=script_path.name)
        else:
            return HookResult(
                decision="block",
                reason=f"hook exited {r.returncode}: {r.stderr.strip()[:200]}",
                hook_name=script_path.name,
            )
    except subprocess.TimeoutExpired:
        return HookResult(decision="block", reason="hook timed out", hook_name=script_path.name)
    except Exception as e:
        return HookResult(decision="block", reason=f"hook error: {e}", hook_name=script_path.name)


# ─── Hook Config Loader ──────────────────────────────────────────────────────

def load_hooks_from_config(config_path: Path):
    """
    Load hooks from a JSON config file.

    Format:
    {
      "hooks": {
        "PreToolUse": [
          {"script": "hooks/k8_precheck.py", "matcher": {"tool": "Write"}}
        ]
      }
    }
    """
    if not config_path.exists():
        return

    config = json.loads(config_path.read_text())
    hooks_config = config.get("hooks", {})
    base_dir = config_path.parent

    for event_type, hook_list in hooks_config.items():
        for hook_def in hook_list:
            script = base_dir / hook_def["script"]
            matcher = hook_def.get("matcher", {})

            def make_hook(s=script, m=matcher):
                def hook_fn(event: HookEvent) -> HookResult:
                    # Check matcher (tool name pattern)
                    if "tool" in m and m["tool"] != event.tool:
                        return HookResult(decision="allow", reason="matcher skip")
                    return run_shell_hook(s, event)
                hook_fn.__name__ = s.name
                return hook_fn

            register_hook(event_type, make_hook())
