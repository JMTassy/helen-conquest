"""
Tests for HELEN Hook System.

Validates:
  1. Hook runner executes registered hooks
  2. First BLOCK wins (fail-closed)
  3. Hook exceptions = BLOCK (fail-closed)
  4. K8 precheck blocks unwrapped ND writes
  5. K8 precheck allows wrapped ND writes
  6. K8 precheck skips non-ND paths
  7. Shell hook runner works
  8. Config loader registers hooks
"""
import json
import pytest
from pathlib import Path

from helen_os.hooks.hook_runner import (
    HookEvent, HookResult,
    register_hook, clear_hooks, run_hooks,
    run_shell_hook, load_hooks_from_config,
)
from helen_os.hooks.k8_precheck import check_content


# ─── Hook Runner Tests ────────────────────────────────────────────────────────

class TestHookRunner:

    def setup_method(self):
        clear_hooks()

    def test_no_hooks_allows(self):
        event = HookEvent(event_type="PreToolUse", tool="Write")
        result = run_hooks(event)
        assert result.decision == "allow"

    def test_allow_hook_passes(self):
        def allow_all(event):
            return HookResult(decision="allow", reason="ok")
        register_hook("PreToolUse", allow_all)
        result = run_hooks(HookEvent(event_type="PreToolUse", tool="Write"))
        assert result.decision == "allow"

    def test_block_hook_blocks(self):
        def block_all(event):
            return HookResult(decision="block", reason="nope")
        register_hook("PreToolUse", block_all)
        result = run_hooks(HookEvent(event_type="PreToolUse", tool="Write"))
        assert result.decision == "block"
        assert "nope" in result.reason

    def test_first_block_wins(self):
        def allow(event):
            return HookResult(decision="allow")
        def block(event):
            return HookResult(decision="block", reason="blocked")
        register_hook("PreToolUse", allow)
        register_hook("PreToolUse", block)
        result = run_hooks(HookEvent(event_type="PreToolUse", tool="Write"))
        assert result.decision == "block"

    def test_exception_is_block(self):
        def broken(event):
            raise RuntimeError("hook crashed")
        register_hook("PreToolUse", broken)
        result = run_hooks(HookEvent(event_type="PreToolUse", tool="Write"))
        assert result.decision == "block"
        assert "exception" in result.reason.lower()


# ─── K8 Precheck Tests ───────────────────────────────────────────────────────

class TestK8Precheck:

    def test_blocks_unwrapped_openai_in_nd_scope(self):
        code = '''
import openai
def call():
    openai.OpenAI().chat.completions.create(model="gpt-4", messages=[])
'''
        ok, reason = check_content("oracle_town/skills/voice/test.py", code)
        assert not ok
        assert "wrap token" in reason.lower()

    def test_allows_wrapped_openai_in_nd_scope(self):
        code = '''
import openai, hashlib
def call():
    out = openai.OpenAI().chat.completions.create(model="gpt-4", messages=[])
    payload_hash = hashlib.sha256(str(out).encode()).hexdigest()
    return payload_hash
'''
        ok, reason = check_content("oracle_town/skills/voice/test.py", code)
        assert ok

    def test_allows_anything_outside_nd_scope(self):
        code = '''
import openai
def call():
    openai.OpenAI().chat.completions.create(model="gpt-4", messages=[])
'''
        ok, reason = check_content("tools/some_tool.py", code)
        assert ok
        assert "not in ND scope" in reason

    def test_allows_non_python_in_nd_scope(self):
        ok, reason = check_content("oracle_town/skills/feynman/peer_review/SKILL.md", "# content")
        assert ok
        assert "not Python" in reason

    def test_allows_python_without_nd_surfaces(self):
        code = '''
def helper():
    return 42
'''
        ok, reason = check_content("oracle_town/skills/voice/utils.py", code)
        assert ok

    def test_blocks_string_literal_bypass(self):
        """payload_hash in a string literal should NOT satisfy the wrap check."""
        code = '''
import openai
def call():
    s = "payload_hash present for show"
    openai.OpenAI().chat.completions.create(model="gpt-4", messages=[])
'''
        ok, reason = check_content("oracle_town/skills/feynman/test.py", code)
        assert not ok

    def test_blocks_cross_function_bypass(self):
        """payload_hash in a different function should NOT satisfy the wrap check."""
        code = '''
import openai
def f_with_call():
    openai.OpenAI().chat.completions.create(model="gpt-4", messages=[])
def g_with_wrap():
    payload_hash = "deadbeef"
    return payload_hash
'''
        ok, reason = check_content("oracle_town/skills/voice/test.py", code)
        assert not ok


# ─── Shell Hook Runner Test ──────────────────────────────────────────────────

class TestShellHookRunner:

    def test_shell_hook_allow(self, tmp_path):
        script = tmp_path / "allow.sh"
        script.write_text("#!/bin/bash\nexit 0\n")
        script.chmod(0o755)
        result = run_shell_hook(script, HookEvent(event_type="PreToolUse"))
        assert result.decision == "allow"

    def test_shell_hook_block(self, tmp_path):
        script = tmp_path / "block.sh"
        script.write_text('#!/bin/bash\necho "blocked by test"\nexit 2\n')
        script.chmod(0o755)
        result = run_shell_hook(script, HookEvent(event_type="PreToolUse"))
        assert result.decision == "block"
        assert "blocked by test" in result.reason

    def test_shell_hook_timeout(self, tmp_path):
        script = tmp_path / "slow.sh"
        script.write_text("#!/bin/bash\nsleep 30\n")
        script.chmod(0o755)
        result = run_shell_hook(script, HookEvent(event_type="PreToolUse"), timeout=1)
        assert result.decision == "block"
        assert "timed out" in result.reason
