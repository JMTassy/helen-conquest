"""
tests/test_import_firewall.py — Sovereignty boundary enforcement.

Enforces the import contract from TEMPLE_MODE_POLICY_V1 and the
write-gate architecture. This test turns the sovereignty boundary
into a failing CI gate.

Forbidden dependency directions (hard rule):
  dialogue/    -X-> adapters/, storage/
  memory/      -X-> adapters/, storage/
  trace/       -X-> adapters/, storage/
  eval/        -X-> adapters/, storage/
  seeds/       -X-> adapters/, storage/
  missions/    -X-> storage/ (missions may use write_gate only through adapters)
  temple/      -X-> adapters/, storage/
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # helen_os_scaffold/
HELEN_OS_ROOT = REPO_ROOT / "helen_os_scaffold" / "helen_os"

CHECK_DIRS = [
    "dialogue",
    "memory",
    "trace",
    "eval",
    "seeds",
    "temple",
    "missions",  # missions may not directly write storage
]

FORBIDDEN: dict[str, list[str]] = {
    "dialogue":  ["adapters", "storage"],
    "memory":    ["adapters", "storage"],
    "trace":     ["adapters", "storage"],
    "eval":      ["adapters", "storage"],
    "seeds":     ["adapters", "storage"],
    "temple":    ["adapters", "storage"],
    "missions":  ["storage"],            # may use adapters only through write_gate
}


def _iter_python_files(root: Path):
    for rel_dir in CHECK_DIRS:
        d = root / rel_dir
        if not d.exists():
            continue
        for path in d.rglob("*.py"):
            if path.name.startswith("."):
                continue
            yield path


def _extract_imports(pyfile: Path) -> list[str]:
    try:
        text = pyfile.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(pyfile))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _module_group(pyfile: Path, root: Path) -> str:
    rel = pyfile.relative_to(root)
    return rel.parts[0]


def test_import_firewall():
    violations: list[str] = []
    for pyfile in _iter_python_files(HELEN_OS_ROOT):
        group = _module_group(pyfile, HELEN_OS_ROOT)
        forbidden_prefixes = FORBIDDEN.get(group, [])
        imports = _extract_imports(pyfile)
        for imp in imports:
            for prefix in forbidden_prefixes:
                if imp == prefix or imp.startswith(prefix + "."):
                    violations.append(
                        f"{pyfile.relative_to(HELEN_OS_ROOT)} imports forbidden "
                        f"module '{imp}' (group: {group})"
                    )
    assert not violations, (
        "Import firewall violations:\n" + "\n".join(violations)
    )
