#!/usr/bin/env python3
"""
K8 PreToolUse Hook — Non-Determinism Boundary at runtime.

Intercepts Write/Bash tool calls that target ND-scoped directories.
Runs K8 μ_NDWRAP check on the proposed content BEFORE the write happens.

Input (stdin): JSON with {event, tool, input, output}
Output: exit 0 (allow) or exit 2 + reason on stdout (block)

This converts K8 from a batch linter to a runtime gate.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

# Import K8's actual detection logic
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

ND_SCOPED_DIRS = [
    "oracle_town/skills/voice/",
    "oracle_town/skills/video/",
    "oracle_town/skills/feynman/",
]

ND_SURFACES = {
    "gemini": ["generativelanguage.googleapis.com", "google.generativeai", "genai.GenerativeModel"],
    "openai": ["openai.OpenAI", "openai.AsyncOpenAI", "ChatCompletion.create"],
    "anthropic": ["anthropic.Anthropic", "anthropic.AsyncAnthropic"],
    "tts": [".synthesize_speech", ".generate_speech", "tts."],
    "hyperframes": ["npx hyperframes", "hyperframes.render"],
    "heygen": ["heygen.com/api", "heygen.video"],
    "replicate": ["replicate.run("],
}

WRAP_TOKENS = {"payload_hash", "provenance", "k8_wrap", "audio_provenance"}


class _WrapFinder(ast.NodeVisitor):
    def __init__(self):
        self.found = False
    def visit_FunctionDef(self, node): pass
    def visit_AsyncFunctionDef(self, node): pass
    def visit_ClassDef(self, node): pass
    def visit_Name(self, node):
        if node.id in WRAP_TOKENS: self.found = True
        else: self.generic_visit(node)
    def visit_Attribute(self, node):
        if node.attr in WRAP_TOKENS: self.found = True
        else: self.generic_visit(node)


def check_content(file_path: str, content: str) -> tuple[bool, str]:
    """Check if content being written to an ND-scoped path has proper wrapping."""
    # Only check Python files in ND-scoped dirs
    if not any(file_path.startswith(d) for d in ND_SCOPED_DIRS):
        return True, "not in ND scope"
    if not file_path.endswith(".py"):
        return True, "not Python"

    # AST-based check (same as K8 v1.2 μ_NDWRAP)
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return True, "syntax error — skip (don't block on unparseable)"

    # Find ND surface calls
    surfaces_flat = [n for needles in ND_SURFACES.values() for n in needles]
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    nd_sites = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Call, ast.Attribute)):
            continue
        try:
            src = ast.unparse(node)
        except Exception:
            continue
        for needle in surfaces_flat:
            if needle in src:
                nd_sites.append((node, needle))
                break

    if not nd_sites:
        return True, "no ND surfaces found"

    # For each call site, check enclosing scope for wrap token
    def enclosing(node):
        cur = parents.get(node)
        while cur and not isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            cur = parents.get(cur)
        return cur or tree

    for node, needle in nd_sites:
        scope = enclosing(node)
        body = getattr(scope, "body", [])
        has_wrap = False
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            v = _WrapFinder()
            v.visit(stmt)
            if v.found:
                has_wrap = True
                break
        if not has_wrap:
            scope_name = getattr(scope, "name", "module")
            return False, f"ND surface '{needle}' in scope '{scope_name}' has no wrap token (payload_hash/provenance)"

    return True, "all ND surfaces wrapped"


def main():
    event = json.loads(sys.stdin.read())
    tool = event.get("tool", "")
    tool_input = event.get("input", {})

    # Only intercept Write and Edit tools
    if tool not in ("Write", "Edit", "write", "edit"):
        sys.exit(0)  # allow

    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    content = tool_input.get("content", tool_input.get("new_string", ""))

    if not file_path or not content:
        sys.exit(0)  # allow — can't check without content

    # Make path relative to repo root
    try:
        rel = str(Path(file_path).relative_to(ROOT))
    except ValueError:
        rel = file_path

    ok, reason = check_content(rel, content)
    if ok:
        sys.exit(0)
    else:
        print(f"K8 BLOCK: {reason}\nFile: {rel}")
        sys.exit(2)


if __name__ == "__main__":
    main()
