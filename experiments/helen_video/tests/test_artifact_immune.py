"""Artifact Immune Gate — hardened invariant tests (ARTIFACT_RECEIPT_V1).

20 tests. Zero assert True padding. Every test exercises a real failure mode
or verifies a receipt field against real execution.
"""
import hashlib
import textwrap
from pathlib import Path

import pytest

from helen_video.artifact_immune import (
    NO_OP_RATIO_MAX,
    SCHEMA,
    ArtifactReceipt,
    verify_artifact,
)

# ── helpers ───────────────────────────────────────────────────────────────────

def _file(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(body).lstrip())
    return p


_REAL_FILE  = Path(__file__).resolve().parent / "test_constitutional_reflexivity.py"
_REAL_COUNT = 20

_VALID_BODY = """\
    def test_add(): assert 1 + 1 == 2
    def test_sub(): assert 5 - 3 == 2
    def test_mul(): assert 3 * 3 == 9
"""


# ── 1. rejects missing file ───────────────────────────────────────────────────

def test_rejects_missing_file(tmp_path):
    r = verify_artifact(tmp_path / "ghost.py", 1)
    assert r.verdict == "REJECT"
    assert r.exists is False
    assert any("FILE_NOT_FOUND" in x for x in r.reasons)


# ── 2. rejects directory ──────────────────────────────────────────────────────

def test_rejects_directory(tmp_path):
    r = verify_artifact(tmp_path, 1)
    assert r.verdict == "REJECT"
    assert any("NOT_A_FILE" in x for x in r.reasons)


# ── 3. rejects non-python file ────────────────────────────────────────────────

def test_rejects_non_python_file(tmp_path):
    p = tmp_path / "tests.txt"
    p.write_text("def test_x(): assert True\n")
    r = verify_artifact(p, 1)
    assert r.verdict == "REJECT"
    assert any("NON_PYTHON" in x for x in r.reasons)


# ── 4. rejects syntax error ───────────────────────────────────────────────────

def test_rejects_syntax_error(tmp_path):
    p = _file(tmp_path, "test_bad.py", "def test_x(\n")
    r = verify_artifact(p, 1)
    assert r.verdict == "REJECT"
    assert any("AST_PARSE_FAIL" in x for x in r.reasons)


# ── 5. rejects zero tests ─────────────────────────────────────────────────────

def test_rejects_zero_tests(tmp_path):
    p = _file(tmp_path, "test_empty.py", "def helper(): pass\n")
    r = verify_artifact(p, 0)
    assert r.verdict == "REJECT"
    assert any("NO_TESTS" in x for x in r.reasons)


# ── 6. rejects assert-True padding ───────────────────────────────────────────

def test_rejects_assert_true_padding(tmp_path):
    body = "def test_real(): assert 1 + 1 == 2\n"
    body += "".join(f"def test_pad_{i}(): assert True\n" for i in range(10))
    p = _file(tmp_path, "test_padded.py", body)
    r = verify_artifact(p, 11)
    assert r.verdict == "REJECT"
    assert r.noop_ratio > NO_OP_RATIO_MAX
    assert any("NOOP_WEAK_RATIO" in x for x in r.reasons)


# ── 7. rejects pass-body padding ─────────────────────────────────────────────

def test_rejects_pass_body_padding(tmp_path):
    body = "def test_real(): assert 2 + 2 == 4\n"
    body += "".join(f"def test_empty_{i}():\n    pass\n" for i in range(10))
    p = _file(tmp_path, "test_pass.py", body)
    r = verify_artifact(p, 11)
    assert r.verdict == "REJECT"
    assert any("NOOP_WEAK_RATIO" in x for x in r.reasons)


# ── 8. rejects placeholder test names ────────────────────────────────────────

def test_rejects_placeholder_names(tmp_path):
    body = "def test_real(): assert 1 == 1\n"
    body += "".join(
        f"def test_placeholder_{i}(): assert 1 + {i} > 0\n" for i in range(10)
    )
    p = _file(tmp_path, "test_placeholder.py", body)
    r = verify_artifact(p, 11)
    assert r.verdict == "REJECT"
    assert any("NOOP_WEAK_RATIO" in x for x in r.reasons)


# ── 9. rejects duplicate test names ──────────────────────────────────────────

def test_rejects_duplicate_test_names(tmp_path):
    p = _file(tmp_path, "test_dup.py", """\
        def test_alpha(): assert 1 + 1 == 2
        def test_alpha(): assert 2 * 2 == 4
    """)
    r = verify_artifact(p, 2)
    assert r.verdict == "REJECT"
    assert "test_alpha" in r.duplicate_names
    assert any("DUPLICATE_TEST_NAMES" in x for x in r.reasons)


# ── 10. rejects unresolved import ────────────────────────────────────────────

def test_rejects_unresolved_import(tmp_path):
    p = _file(tmp_path, "test_phantom.py", """\
        from helen_video_does_not_exist_xyzzy import something
        def test_x(): assert something == 1
    """)
    r = verify_artifact(p, 1)
    assert r.verdict == "REJECT"
    assert "helen_video_does_not_exist_xyzzy" in r.unresolved_imports
    assert any("IMPORT_FAIL" in x for x in r.reasons)


# ── 11. rejects claimed_pass_status=False ────────────────────────────────────

def test_rejects_claimed_pass_false(tmp_path):
    p = _file(tmp_path, "test_honest.py", _VALID_BODY)
    r = verify_artifact(p, 3, claimed_pass_status=False)
    assert r.verdict == "REJECT"
    assert any("CLAIMED_FAIL_STATUS" in x for x in r.reasons)


# ── 12. rejects failing pytest (FALSE_PASS_CLAIM) ────────────────────────────

def test_rejects_failing_pytest(tmp_path):
    p = _file(tmp_path, "test_fail.py", "def test_always_fails(): assert False\n")
    r = verify_artifact(p, 1)
    assert r.verdict == "REJECT"
    assert any("FALSE_PASS_CLAIM" in x for x in r.reasons)


# ── 13. rejects count mismatch (claimed too high) ────────────────────────────

def test_rejects_count_mismatch(tmp_path):
    p = _file(tmp_path, "test_short.py", _VALID_BODY)
    r = verify_artifact(p, 99)
    assert r.verdict == "REJECT"
    assert r.actual_collected == 3
    assert any("COUNT_MISMATCH" in x for x in r.reasons)


# ── 14. quarantines subprocess.run in test body ───────────────────────────────

def test_quarantines_subprocess_run(tmp_path):
    p = _file(tmp_path, "test_sp.py", """\
        import subprocess
        def test_uses_subprocess():
            result = subprocess.run(["echo", "hi"], capture_output=True)
            assert result.returncode == 0
    """)
    r = verify_artifact(p, 1)
    assert r.verdict == "QUARANTINE"
    assert r.subprocess_masking_detected is True
    assert "test_uses_subprocess" in r.subprocess_masked_tests
    assert any("SUBPROCESS_MASKING_RISK" in x for x in r.reasons)


# ── 15. quarantines os.system in test body ────────────────────────────────────

def test_quarantines_os_system(tmp_path):
    p = _file(tmp_path, "test_os.py", """\
        import os
        def test_uses_os_system():
            rc = os.system("echo hi")
            assert rc == 0
    """)
    r = verify_artifact(p, 1)
    assert r.verdict == "QUARANTINE"
    assert r.subprocess_masking_detected is True
    assert any("SUBPROCESS_MASKING_RISK" in x for x in r.reasons)


# ── 16. accepts valid file ────────────────────────────────────────────────────

def test_accepts_valid_minimal_file(tmp_path):
    p = _file(tmp_path, "test_ok.py", _VALID_BODY)
    r = verify_artifact(p, 3)
    assert r.verdict == "ACCEPT"
    assert r.actual_collected == 3
    assert r.actual_passed == 3
    assert r.deterministic is True


# ── 17. accepts real constitutional file ─────────────────────────────────────

def test_accepts_real_constitutional_file():
    r = verify_artifact(_REAL_FILE, _REAL_COUNT)
    assert r.verdict == "ACCEPT"
    assert r.actual_collected == _REAL_COUNT
    assert r.actual_passed == _REAL_COUNT
    assert r.deterministic is True
    assert r.unresolved_imports == ()


# ── 18. receipt schema is ARTIFACT_RECEIPT_V1 ────────────────────────────────

def test_receipt_schema_is_v1():
    r = verify_artifact(_REAL_FILE, _REAL_COUNT)
    assert r.schema == SCHEMA
    assert r.schema == "ARTIFACT_RECEIPT_V1"


# ── 19. artifact_hash changes when content changes ───────────────────────────

def test_artifact_hash_changes_with_content(tmp_path):
    p1 = _file(tmp_path, "test_v1.py", "def test_a(): assert 1 == 1\n")
    p2 = _file(tmp_path, "test_v2.py", "def test_a(): assert 2 == 2\n")
    r1 = verify_artifact(p1, 1)
    r2 = verify_artifact(p2, 1)
    assert r1.artifact_hash != r2.artifact_hash


# ── 20. run output hashes present on ACCEPT ──────────────────────────────────

def test_run_output_hashes_present_on_accept():
    r = verify_artifact(_REAL_FILE, _REAL_COUNT)
    assert r.run1_output_hash is not None
    assert r.run2_output_hash is not None
    assert len(r.run1_output_hash) == 64  # sha256 hex
