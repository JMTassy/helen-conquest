#!/usr/bin/env python3
"""
HELEN WUL Linter — canonical compile+validate gate.

Usage:
  python3 scripts/helen_wul_lint.py /path/to/slab.json

slab.json expected fields:
  - content: string (the WUL text)
Optional:
  - banners/tags/power (ignored by oracle_town validator; kept for UI rules elsewhere)

Exit codes:
  0 = PASS
  1 = FAIL
"""

import json
import sys
import inspect
from pathlib import Path
from pathlib import Path

# Ensure repo root is importable (oracle_town/)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from oracle_town.core.wul_compiler import WULCompiler
from oracle_town.core.wul_validator import WULValidator

def die(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)

def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"cannot read json: {p} ({e})")

def get_compiler_fn(c: WULCompiler):
    # Prefer known names
    for name in ("build_token_tree", "compile", "parse", "build", "from_text"):
        fn = getattr(c, name, None)
        if callable(fn):
            try:
                if len(inspect.signature(fn).parameters) == 1:
                    return name, fn
            except Exception:
                pass

    # Fallback: first public 1-arg callable
    for name, fn in inspect.getmembers(c, predicate=callable):
        if name.startswith("_"):
            continue
        try:
            sig = inspect.signature(fn)
        except Exception:
            continue
        if len(sig.parameters) == 1:
            return name, fn

    return None, None

def main():
    if len(sys.argv) != 2:
        print("Usage: helen_wul_lint.py <slab.json>", file=sys.stderr)
        sys.exit(1)

    slab_path = Path(sys.argv[1])
    slab = load_json(slab_path)

    if "content" not in slab or not isinstance(slab["content"], str):
        die("slab.json must contain a string field: content")

    text = slab["content"]

    c = WULCompiler()
    name, compile_fn = get_compiler_fn(c)
    if compile_fn is None:
        die("no usable compiler method found on WULCompiler")

    tree = compile_fn(text)

    v = WULValidator()
    res = v.validate(tree)

    # Print a HELEN-style receipt line
    print("[INFO] compiler =", name)
    print("[INFO] tree_type =", type(tree).__name__)
    print(f"[WUL] {'PASS' if res.ok else 'FAIL'} — {res.code.value}")
    print("  detail:", res.detail)
    print("  depth :", res.depth)
    print("  nodes :", res.nodes)

    sys.exit(0 if res.ok else 1)

if __name__ == "__main__":
    main()
