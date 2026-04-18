"""
tests/conftest_kernel.py

Shared helpers for kernel_cli contract tests (test_kernel_*.py).

Pinned hash scheme: HELEN_CUM_V1
  payload_hash = SHA256(raw_payload_bytes)
  cum_hash     = SHA256("HELEN_CUM_V1" || bytes.fromhex(prev) || bytes.fromhex(ph))

These tests start RED because kernel_cli is a stub (exits 1, returns ok=false).
They turn GREEN when kernel_cli is compiled and properly wired to:
  - structural_valid_b  (extracted from LedgerKernel.v)
  - policy_validb       (stub: allows all)
  - Sha256.digest_bytes
  - Hash_util.concat    (HELEN_CUM_V1 scheme)

Build command (once OCaml deps are available):
  cd kernel && ocamlfind ocamlopt -package digestif,yojson -linkpkg \
      sha256.ml hash_util.ml kernel_cli.ml -o kernel_cli
Or via dune:
  dune build kernel/kernel_cli.exe
"""

import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional, Tuple

# -----------------------------------------------------------------------
# Repository root (with path setup for kernel imports)
# -----------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kernel.canonical_json import canon_json_bytes

# -----------------------------------------------------------------------
# Binary location (override with KERNEL_CLI_PATH env var)
# -----------------------------------------------------------------------
KERNEL_CLI_BINARY = os.environ.get(
    "KERNEL_CLI_PATH",
    os.path.join(REPO_ROOT, "kernel", "kernel_cli"),
)

# -----------------------------------------------------------------------
# HELEN_CUM_V1 pinned hash scheme
# -----------------------------------------------------------------------
GENESIS_HASH = "0" * 64
HELEN_CUM_V1_PREFIX = b"HELEN_CUM_V1"


def sha256_hex(b: bytes) -> str:
    """SHA256 of bytes → 64-char lowercase hex."""
    return hashlib.sha256(b).hexdigest()


def compute_payload_hash(payload_dict: Dict[str, Any]) -> str:
    """payload_hash = SHA256(canon_json_bytes(payload))."""
    return sha256_hex(canon_json_bytes(payload_dict))


def chain_hash_v1(prev_hex: str, ph_hex: str) -> str:
    """
    HELEN_CUM_V1: SHA256("HELEN_CUM_V1" || bytes.fromhex(prev) || bytes.fromhex(ph))

    This is the single, domain-separated cumulative hash operation.
    Pinned forever. Must match kernel/hash_util.ml Hash_util.concat.
    """
    return sha256_hex(
        HELEN_CUM_V1_PREFIX + bytes.fromhex(prev_hex) + bytes.fromhex(ph_hex)
    )


def compute_expected(
    payload_dict: Dict[str, Any],
    prev_cum_hash: str,
) -> Tuple[str, str]:
    """
    Compute expected (payload_hash, cum_hash) for a payload dict.
    Uses HELEN_CUM_V1 scheme.

    Returns (payload_hash_hex, cum_hash_hex).
    """
    payload_hash = compute_payload_hash(payload_dict)
    cum_hash = chain_hash_v1(prev_cum_hash, payload_hash)
    return payload_hash, cum_hash


# -----------------------------------------------------------------------
# Binary invocation
# -----------------------------------------------------------------------

def kernel_cli_available() -> bool:
    """True if the kernel_cli binary exists and is executable."""
    return os.path.isfile(KERNEL_CLI_BINARY) and os.access(
        KERNEL_CLI_BINARY, os.X_OK
    )


def invoke_kernel_cli(
    ledger_path: str,
    actor: str,
    etype: str,
    payload_dict: Dict[str, Any],
    ctx: Optional[Dict[str, Any]] = None,
    require_binary: bool = True,
) -> Tuple[int, Dict[str, Any]]:
    """
    Invoke kernel_cli binary with a single-event request.

    Args:
        ledger_path: Path to NDJSON ledger file (created/extended by binary).
        actor:       "HELEN" | "MAYOR" | "CHRONOS"
        etype:       "VERDICT" | "TERMINATION" | "PROPOSAL" | ...
        payload_dict: Dict that gets canonicalized and hex-encoded as raw_hex.
        ctx:         Policy context (iteration_count, risk_tier, eval_receipt_count).
        require_binary: If True, call pytest.fail() when binary not found.
                        If False, return (2, {"ok": False, "error": "not found"}).

    Returns:
        (returncode, response_dict)
        On success:  (0, {"ok": True, "cum_hash": "...", "seq": N})
        On failure:  (1, {"ok": False, "error": "..."})

    NOTE: Tests start RED because the binary is a stub.
    """
    import pytest  # imported here so conftest_kernel can be imported without pytest

    if not kernel_cli_available():
        msg = (
            f"\n[RED] kernel_cli binary not found at {KERNEL_CLI_BINARY}\n"
            f"      Build with:\n"
            f"        cd {REPO_ROOT}/kernel && \\\n"
            f"        ocamlfind ocamlopt -package digestif,yojson \\\n"
            f"          -linkpkg sha256.ml hash_util.ml kernel_cli.ml \\\n"
            f"          -o kernel_cli\n"
            f"      Or: dune build kernel/kernel_cli.exe\n"
            f"      Tests are RED until this binary is wired."
        )
        if require_binary:
            pytest.fail(msg)
        return 2, {"ok": False, "error": "binary not found"}

    if ctx is None:
        ctx = {"iteration_count": 0, "risk_tier": 0, "eval_receipt_count": 0}

    # Canonicalize payload → bytes → hex (raw_hex is what the kernel hashes)
    raw_bytes = canon_json_bytes(payload_dict)
    raw_hex = raw_bytes.hex()

    request = {
        "actor": actor,
        "etype": etype,
        "raw_hex": raw_hex,
        "ctx": ctx,
    }

    proc = subprocess.run(
        [KERNEL_CLI_BINARY, ledger_path],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=10,
    )

    stdout = proc.stdout.strip()
    if not stdout:
        return proc.returncode, {
            "ok": False,
            "error": (
                f"No stdout (exitcode={proc.returncode}, "
                f"stderr={proc.stderr.strip()!r})"
            ),
        }

    try:
        return proc.returncode, json.loads(stdout)
    except json.JSONDecodeError as exc:
        return proc.returncode, {
            "ok": False,
            "error": f"Bad JSON in stdout: {exc} | stdout={stdout!r}",
        }
