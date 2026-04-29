"""Artifact Immune — hardened cross-repo transfer gate (ARTIFACT_RECEIPT_V1).

10-point enforcement. Rejects fabricated counts, padding, import phantoms,
subprocess-shielded results, and non-deterministic suites before they
enter the receipt layer.

Checks (in order):
  1.  File exists, is a regular file, ends in .py
  2.  Valid Python (AST parse)
  3.  Imports resolve via importlib.util.find_spec — never executes modules
  4.  Test function count > 0
  5.  Noop/weak ratio ≤ NO_OP_RATIO_MAX (0.30)
  6.  No duplicate test names
  7.  claimed_pass_status must be True (False → REJECT immediately)
  8.  No subprocess masking in test bodies (→ QUARANTINE)
  9.  pytest --collect-only passes; collected == claimed_test_count
  10. Two independent pytest runs: both exit 0, same passed count

Receipt schema: ARTIFACT_RECEIPT_V1

lifecycle: EXPERIMENTAL_GATE
canon: NO_SHIP
authority: NON_SOVEREIGN
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

NO_OP_RATIO_MAX = 0.30
VERDICT = Literal["ACCEPT", "QUARANTINE", "REJECT"]
SCHEMA = "ARTIFACT_RECEIPT_V1"

_WEAK_NAME_KEYWORDS = frozenset(
    {"placeholder", "dummy", "noop", "trivial", "stub", "todo", "skip_me"}
)
_SUBPROCESS_ATTRS = frozenset({"run", "call", "Popen", "check_output", "check_call"})
_MASKING_CALLS = frozenset({"system"})          # os.system
_MASKING_FUNCS = frozenset({"main"})            # pytest.main


@dataclass(frozen=True)
class ArtifactReceipt:
    schema: str
    verdict: VERDICT
    path: str
    artifact_hash: str | None
    exists: bool
    claimed_test_count: int
    claimed_pass_status: bool
    actual_collected: int | None
    actual_passed: int | None
    collect_exit_code: int | None
    run1_exit_code: int | None
    run2_exit_code: int | None
    run1_output_hash: str | None
    run2_output_hash: str | None
    deterministic: bool | None
    imports_checked: tuple[str, ...]
    unresolved_imports: tuple[str, ...]
    test_function_count: int
    noop_count: int
    noop_ratio: float
    weak_assertion_count: int
    weak_assertion_ratio: float
    duplicate_names: tuple[str, ...]
    subprocess_masking_detected: bool
    subprocess_masked_tests: tuple[str, ...]
    reasons: tuple[str, ...]
    timestamp: str


# ── AST analysis ──────────────────────────────────────────────────────────────

def _test_funcs(tree: ast.AST) -> list[ast.FunctionDef]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            out.append(node)
    return out


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        return body[1:]
    return body


def _is_noop(func: ast.FunctionDef) -> bool:
    body = _strip_docstring(list(func.body))
    if not body:
        return True
    if len(body) == 1:
        s = body[0]
        if isinstance(s, ast.Pass):
            return True
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is ...:
            return True
        if isinstance(s, ast.Assert):
            t = s.test
            if isinstance(t, ast.Constant) and t.value in (True, 1):
                return True
    return False


def _is_weak(func: ast.FunctionDef) -> bool:
    if _is_noop(func):
        return True
    if any(kw in func.name.lower() for kw in _WEAK_NAME_KEYWORDS):
        return True
    params = {a.arg for a in func.args.args if a.arg not in ("self", "cls")}
    body = _strip_docstring(list(func.body))
    if len(body) == 1 and isinstance(body[0], ast.Assert):
        t = body[0].test
        # assert x is not None (where x is a fixture param)
        if (isinstance(t, ast.Compare) and len(t.ops) == 1
                and isinstance(t.ops[0], ast.IsNot)
                and len(t.comparators) == 1
                and isinstance(t.comparators[0], ast.Constant)
                and t.comparators[0].value is None
                and isinstance(t.left, ast.Name) and t.left.id in params):
            return True
        # assert isinstance(x, object)
        if (isinstance(t, ast.Call) and isinstance(t.func, ast.Name)
                and t.func.id == "isinstance" and len(t.args) == 2
                and isinstance(t.args[1], ast.Name) and t.args[1].id == "object"):
            return True
    return False


def _duplicate_names(funcs: list[ast.FunctionDef]) -> tuple[str, ...]:
    seen: set[str] = set()
    dupes: list[str] = []
    for f in funcs:
        if f.name in seen and f.name not in dupes:
            dupes.append(f.name)
        seen.add(f.name)
    return tuple(dupes)


def _subprocess_masked(funcs: list[ast.FunctionDef]) -> tuple[str, ...]:
    flagged: list[str] = []
    for func in funcs:
        for node in ast.walk(func):
            hit = False
            if isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name)
                        and node.value.id == "subprocess"
                        and node.attr in _SUBPROCESS_ATTRS):
                    hit = True
                if (isinstance(node.value, ast.Name)
                        and node.value.id == "os"
                        and node.attr in _MASKING_CALLS):
                    hit = True
                if (isinstance(node.value, ast.Name)
                        and node.value.id == "pytest"
                        and node.attr in _MASKING_FUNCS):
                    hit = True
            if hit:
                flagged.append(func.name)
                break
    return tuple(flagged)


def _extract_imports(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                names.append(node.module.split(".")[0])
    return names


def _has_sys_path_mutation(tree: ast.AST) -> bool:
    """True if the file mutates sys.path (dynamic path injection at runtime)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            v = node.func.value
            if (isinstance(v, ast.Attribute) and v.attr == "path"
                    and isinstance(v.value, ast.Name) and v.value.id == "sys"
                    and node.func.attr in ("insert", "append")):
                return True
    return False


def _unresolved(import_names: list[str]) -> tuple[str, ...]:
    bad: list[str] = []
    for name in dict.fromkeys(import_names):  # deduplicate, preserve order
        try:
            spec = importlib.util.find_spec(name)
        except (ModuleNotFoundError, ValueError):
            spec = None
        if spec is None:
            bad.append(name)
    return tuple(bad)


# ── pytest runners ────────────────────────────────────────────────────────────

def _run_pytest(path: Path, extra: list[str], python: str) -> tuple[int, str]:
    r = subprocess.run(
        [python, "-m", "pytest"] + extra + [str(path)],
        capture_output=True, text=True, timeout=60,
    )
    return r.returncode, r.stdout + r.stderr


def _output_hash(text: str) -> str:
    # Strip timing digits so "0.04s" doesn't differ between runs
    normalized = re.sub(r"\d+\.\d+s", "Xs", text)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _collect_count(out: str) -> int | None:
    m = re.search(r"(\d+)\s+test", out)
    return int(m.group(1)) if m else 0


def _passed_count(out: str) -> int | None:
    m = re.search(r"(\d+)\s+passed", out)
    return int(m.group(1)) if m else None


# ── public API ────────────────────────────────────────────────────────────────

def verify_artifact(
    path: str | Path,
    claimed_test_count: int,
    claimed_pass_status: bool = True,
    python: str = sys.executable,
) -> ArtifactReceipt:
    """Verify a test artifact before cross-repo adoption.

    Args:
        path:                Filesystem path to the test file.
        claimed_test_count:  Number of tests the source claims.
        claimed_pass_status: Whether the source claims all tests pass.
        python:              Python interpreter for pytest invocations.

    Returns:
        ArtifactReceipt — ACCEPT, QUARANTINE, or REJECT.
    """
    p = Path(path)
    ts = datetime.now(timezone.utc).isoformat()
    reasons: list[str] = []

    def _r(verdict: VERDICT, **kw) -> ArtifactReceipt:
        defaults = dict(
            schema=SCHEMA, verdict=verdict, path=str(p), artifact_hash=None,
            exists=False, claimed_test_count=claimed_test_count,
            claimed_pass_status=claimed_pass_status,
            actual_collected=None, actual_passed=None,
            collect_exit_code=None, run1_exit_code=None, run2_exit_code=None,
            run1_output_hash=None, run2_output_hash=None,
            deterministic=None, imports_checked=(), unresolved_imports=(),
            test_function_count=0, noop_count=0, noop_ratio=0.0,
            weak_assertion_count=0, weak_assertion_ratio=0.0,
            duplicate_names=(), subprocess_masking_detected=False,
            subprocess_masked_tests=(), reasons=tuple(reasons), timestamp=ts,
        )
        defaults.update(kw)
        return ArtifactReceipt(**defaults)

    # 1a. exists
    if not p.exists():
        reasons.append(f"FILE_NOT_FOUND: {p}")
        return _r("REJECT", exists=False)

    # 1b. is a regular file
    if not p.is_file():
        reasons.append(f"NOT_A_FILE: {p}")
        return _r("REJECT", exists=True)

    # 1c. must be Python
    if p.suffix.lower() != ".py":
        reasons.append(f"NON_PYTHON_ARTIFACT: suffix={p.suffix!r}")
        return _r("REJECT", exists=True)

    # 2. AST parse
    try:
        source = p.read_text()
        tree = ast.parse(source)
    except SyntaxError as exc:
        reasons.append(f"AST_PARSE_FAIL: {exc}")
        return _r("REJECT", exists=True)

    artifact_hash = hashlib.sha256(source.encode()).hexdigest()

    # 3. imports (skipped when file injects sys.path — deferred to --collect-only)
    import_names = _extract_imports(tree)
    if _has_sys_path_mutation(tree):
        unresolved = ()
        reasons.append("IMPORT_CHECK_DEFERRED: sys.path mutation detected — delegating to collection")
    else:
        unresolved = _unresolved(import_names)
        if unresolved:
            reasons.append(f"IMPORT_FAIL: {unresolved}")
            return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                      imports_checked=tuple(dict.fromkeys(import_names)),
                      unresolved_imports=unresolved)

    # 4. test count
    funcs = _test_funcs(tree)
    if not funcs:
        reasons.append("NO_TESTS: no test_ functions found")
        return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)))

    # 5. noop/weak ratio
    weak_count = sum(1 for f in funcs if _is_weak(f))
    noop_count = sum(1 for f in funcs if _is_noop(f))
    weak_ratio = weak_count / len(funcs)
    if weak_ratio > NO_OP_RATIO_MAX:
        reasons.append(
            f"NOOP_WEAK_RATIO_{weak_ratio:.0%}: {weak_count}/{len(funcs)} weak/noop bodies"
        )
        return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)

    # 6. duplicate names
    dupes = _duplicate_names(funcs)
    if dupes:
        reasons.append(f"DUPLICATE_TEST_NAMES: {dupes}")
        return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio,
                  duplicate_names=dupes)

    # 7. claimed_pass_status must be True
    if not claimed_pass_status:
        reasons.append("CLAIMED_FAIL_STATUS: artifact is claimed to not be passing")
        return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)

    # 8. subprocess masking
    sp_tests = _subprocess_masked(funcs)
    if sp_tests:
        reasons.append(f"SUBPROCESS_MASKING_RISK: {sp_tests}")
        return _r("QUARANTINE", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio,
                  subprocess_masking_detected=True, subprocess_masked_tests=sp_tests)

    # 9. --collect-only
    crc, cout = _run_pytest(p, ["--collect-only", "-q"], python)
    collected = _collect_count(cout)
    import_ok = "ImportError" not in cout and "ModuleNotFoundError" not in cout
    if crc not in (0, 5) or collected is None:
        reasons.append("COLLECTION_FAILED: " + cout[:300].replace("\n", " "))
        return _r("QUARANTINE", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  collect_exit_code=crc, test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)

    if collected != claimed_test_count:
        reasons.append(
            f"COUNT_MISMATCH: claimed {claimed_test_count}, collected {collected}"
        )
        return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  actual_collected=collected, collect_exit_code=crc,
                  test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)

    # 10. two runs
    rc1, out1 = _run_pytest(p, ["-q"], python)
    passed1 = _passed_count(out1)
    h1 = _output_hash(out1)

    if rc1 != 0 or passed1 != claimed_test_count:
        reasons.append(
            f"FALSE_PASS_CLAIM: claimed {claimed_test_count} passing, "
            f"run1 got {passed1} (exit={rc1})"
        )
        return _r("REJECT", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  actual_collected=collected, actual_passed=passed1,
                  collect_exit_code=crc, run1_exit_code=rc1,
                  run1_output_hash=h1, test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)

    rc2, out2 = _run_pytest(p, ["-q"], python)
    passed2 = _passed_count(out2)
    h2 = _output_hash(out2)

    if rc1 != rc2 or passed1 != passed2:
        reasons.append(
            f"NON_DETERMINISTIC_EXECUTION: run1={passed1} passing, run2={passed2} passing"
        )
        return _r("QUARANTINE", exists=True, artifact_hash=artifact_hash,
                  imports_checked=tuple(dict.fromkeys(import_names)),
                  actual_collected=collected, actual_passed=passed1,
                  collect_exit_code=crc, run1_exit_code=rc1, run2_exit_code=rc2,
                  run1_output_hash=h1, run2_output_hash=h2, deterministic=False,
                  test_function_count=len(funcs),
                  noop_count=noop_count, noop_ratio=noop_count / len(funcs),
                  weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)

    reasons.append(f"ALL_CHECKS_PASSED: {claimed_test_count} tests, deterministic")
    return _r("ACCEPT", exists=True, artifact_hash=artifact_hash,
              imports_checked=tuple(dict.fromkeys(import_names)),
              actual_collected=collected, actual_passed=passed1,
              collect_exit_code=crc, run1_exit_code=rc1, run2_exit_code=rc2,
              run1_output_hash=h1, run2_output_hash=h2, deterministic=True,
              test_function_count=len(funcs),
              noop_count=noop_count, noop_ratio=noop_count / len(funcs),
              weak_assertion_count=weak_count, weak_assertion_ratio=weak_ratio)
