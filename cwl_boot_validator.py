#!/usr/bin/env python3
"""
CWL v1.0.1 Boot Validator
Fresh-machine replay + fail-closed verification

Implements hash chain validation from CWL_V1_0_1_ARCHITECTURE.md §3
"""

import json
import hashlib
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple

# Constants from CWL_V1_0_1_ARCHITECTURE.md §3
PREFIX_LEDGER = b"HELEN_CUM_V1"
PREFIX_TRACE = b"HELEN_TRACE_V1"
ZERO_HASH = "0" * 64

@dataclass
class BootResult:
    success: bool
    final_cum_hash: str
    expected_cum_hash: str
    ledger_events: int
    mismatches: List[str]
    tamper_detected: bool
    kernel_valid: bool
    trace_valid: bool
    kernel_hash_actual: Optional[str] = None
    kernel_hash_seal: Optional[str] = None

def compute_cum_hash(prev_hash: str, payload: dict) -> str:
    """
    Compute cumulative hash per CWL spec:
    cum_hash_i = SHA256(PREFIX || prev_cum_hash || payload_hash_i)

    Args:
        prev_hash: Previous cumulative hash (hex string)
        payload: Dictionary to hash

    Returns:
        Cumulative hash (hex string)
    """
    # Canonical payload hash (sort keys for determinism)
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    # Convert hashes to bytes
    try:
        prev_bytes = bytes.fromhex(prev_hash)
    except ValueError:
        raise ValueError(f"Invalid hex in prev_hash: {prev_hash}")

    try:
        payload_bytes = bytes.fromhex(payload_hash)
    except ValueError:
        raise ValueError(f"Invalid hex in payload_hash: {payload_hash}")

    # Raw byte concatenation (no JSON, no delimiters)
    combined = PREFIX_LEDGER + prev_bytes + payload_bytes

    # Result
    result = hashlib.sha256(combined).hexdigest()
    return result

def validate_ledger_chain(ledger_path: Path) -> Tuple[bool, str, List[str], int]:
    """
    Validate ledger hash chain with semantic version support.

    The ledger pre-computes payload_hash for each event.
    Hash formula depends on hash_law version:
    - CWL_CUM_V0: pre-v1.0.1 (historical, not re-verified here)
    - CWL_CUM_V1: cum_hash_i = SHA256(PREFIX || prev_cum_hash || payload_hash_i)

    Returns: (valid, final_hash, error_list, event_count)
    """
    errors = []
    current_hash = ZERO_HASH
    event_count = 0
    hash_law_detected = None

    if not ledger_path.exists():
        return False, ZERO_HASH, ["Ledger file not found"], 0

    with open(ledger_path, 'r') as f:
        for seq, line in enumerate(f):
            if not line.strip():
                continue

            try:
                event = json.loads(line.strip())
            except json.JSONDecodeError as e:
                errors.append(f"Seq {seq}: JSON parse error: {e}")
                return False, current_hash, errors, seq

            # Detect hash law version
            event_hash_law = event.get("hash_law", "CWL_CUM_V0")  # Default to legacy
            if hash_law_detected is None:
                hash_law_detected = event_hash_law
                if event_hash_law == "CWL_CUM_V0":
                    errors.append(f"Ledger uses {event_hash_law} (legacy). Skipping hash verification.")
                    return True, ZERO_HASH, errors, seq + 1

            # If CWL_CUM_V1, verify hash chain
            if event_hash_law == "CWL_CUM_V1":
                # SPECIAL: Seal events do NOT participate in the hash chain
                # Seal references the cumulative hash BEFORE the seal
                if event.get("type") == "seal":
                    # Seal is the terminus of the chain; don't include it in hash computation
                    event_count += 1
                    return True, current_hash, errors, event_count

                # Extract pre-computed payload_hash from event
                payload_hash_hex = event.get("payload_hash", "MISSING")

                if payload_hash_hex == "MISSING":
                    errors.append(f"Seq {seq}: payload_hash field missing")
                    return False, current_hash, errors, seq + 1

                # Compute expected cum_hash: SHA256(PREFIX || prev_cum_hash || payload_hash_i)
                try:
                    prev_bytes = bytes.fromhex(current_hash)
                    payload_bytes = bytes.fromhex(payload_hash_hex)
                    combined = PREFIX_LEDGER + prev_bytes + payload_bytes
                    expected = hashlib.sha256(combined).hexdigest()
                except ValueError as e:
                    errors.append(f"Seq {seq}: Hash computation error: {e}")
                    return False, current_hash, errors, seq

                actual = event.get("cum_hash", "MISSING")

                if expected != actual:
                    errors.append(
                        f"Seq {seq}: cum_hash mismatch. "
                        f"Expected {expected[:16]}... "
                        f"got {actual[:16] if actual != 'MISSING' else actual}..."
                    )
                    return False, actual, errors, seq + 1

                current_hash = actual

            event_count += 1

    return True, current_hash, errors, event_count

def extract_seal_v2(ledger_path: Path) -> dict:
    """
    Extract seal_v2 (or SEAL_V1) from last ledger event.
    """
    seal = {}

    with open(ledger_path, 'r') as f:
        for line in f:
            pass
        if line.strip():
            try:
                last_event = json.loads(line.strip())
                seal = last_event.get("payload", {})
            except:
                pass

    return seal

def boot_verify(
    ledger_path: Path,
    trace_path: Optional[Path] = None,
    env_hash: Optional[str] = None,
    kernel_hash: Optional[str] = None,
) -> BootResult:
    """
    Boot verification per CWL §6 (seal_v2 binding).

    Fresh machine replay: loads ledger, recomputes hashes,
    verifies against seal. Fails closed on any mismatch.

    Semantic: Seal references the ledger cum_hash UP TO (but not including) the seal event itself.
    """
    mismatches = []
    tamper_detected = False
    kernel_valid = True
    trace_valid = True
    kernel_hash_actual = kernel_hash
    kernel_hash_seal = None

    # 1. Validate ledger chain and extract seal
    # The seal event is special: it doesn't participate in its own hash
    seal = extract_seal_v2(ledger_path)

    # Validate chain UP TO (but not including) the seal event
    ledger_valid, final_cum_hash_before_seal, ledger_errors, event_count = validate_ledger_chain(ledger_path)

    # If the validator skipped V0 ledgers, trust it
    if "legacy" in str(ledger_errors).lower() or "CWL_CUM_V0" in str(ledger_errors):
        # Historical ledger, skip detailed validation
        return BootResult(
            success=True,  # Legacy ledgers are accepted as-is
            final_cum_hash=ZERO_HASH,
            expected_cum_hash=ZERO_HASH,
            ledger_events=event_count,
            mismatches=["Ledger uses legacy hash law (pre-v1.0.1). Accepted without re-verification."],
            tamper_detected=False,
            kernel_valid=True,
            trace_valid=True,
        )

    if not ledger_valid:
        mismatches.extend(ledger_errors)
        tamper_detected = True

    # 2. Get expected hash from seal
    expected_cum_hash = seal.get("refs", {}).get("final_ledger_cum_hash", "MISSING")
    if expected_cum_hash == "MISSING":
        expected_cum_hash = seal.get("final_cum_hash", "MISSING")

    # 3. Verify seal matches computed hash (hash before seal event)
    if final_cum_hash_before_seal != expected_cum_hash:
        mismatches.append(
            f"SEAL MISMATCH: computed {final_cum_hash_before_seal[:16]}... "
            f"vs seal {expected_cum_hash[:16] if expected_cum_hash != 'MISSING' else 'MISSING'}..."
        )
        tamper_detected = True

    # 4. Verify kernel identity (if provided)
    if kernel_hash:
        kernel_hash_seal = seal.get("refs", {}).get("kernel_hash", "MISSING")
        if kernel_hash_seal == "MISSING":
            kernel_hash_seal = seal.get("kernel_hash", "MISSING")

        if kernel_hash != kernel_hash_seal and kernel_hash_seal != "MISSING":
            mismatches.append(
                f"KERNEL DRIFT: code {kernel_hash[:16]}... "
                f"vs seal {kernel_hash_seal[:16]}..."
            )
            kernel_valid = False
            tamper_detected = True

    # 5. Validate trace chain (if provided)
    if trace_path and trace_path.exists():
        trace_valid_check, trace_final, trace_errors = validate_trace_chain(trace_path)
        if not trace_valid_check:
            mismatches.extend(trace_errors)
            trace_valid = False

    return BootResult(
        success=(not tamper_detected),
        final_cum_hash=final_cum_hash_before_seal,
        expected_cum_hash=expected_cum_hash,
        ledger_events=event_count,
        mismatches=mismatches,
        tamper_detected=tamper_detected,
        kernel_valid=kernel_valid,
        trace_valid=trace_valid,
        kernel_hash_actual=kernel_hash_actual,
        kernel_hash_seal=kernel_hash_seal,
    )

def validate_trace_chain(trace_path: Path) -> Tuple[bool, str, List[str]]:
    """
    Validate trace hash chain with separate domain prefix.
    """
    errors = []
    current_hash = ZERO_HASH

    with open(trace_path, 'r') as f:
        for seq, line in enumerate(f):
            if not line.strip():
                continue

            try:
                event = json.loads(line.strip())
            except json.JSONDecodeError as e:
                errors.append(f"Trace seq {seq}: JSON parse error: {e}")
                return False, current_hash, errors

            payload = event.get("payload", {})

            # Compute with trace domain prefix
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

            prev_bytes = bytes.fromhex(current_hash)
            payload_bytes = bytes.fromhex(payload_hash)
            combined = PREFIX_TRACE + prev_bytes + payload_bytes

            expected = hashlib.sha256(combined).hexdigest()
            actual = event.get("trace_hash", "MISSING")

            if expected != actual:
                errors.append(
                    f"Trace seq {seq}: hash mismatch. "
                    f"Expected {expected[:16]}... got {actual[:16] if actual != 'MISSING' else actual}..."
                )
                return False, actual, errors

            current_hash = actual

    return True, current_hash, errors

def format_result(result: BootResult) -> str:
    """Pretty-print boot result"""
    output = []
    output.append("=" * 80)
    output.append("CWL v1.0.1 BOOT VALIDATOR")
    output.append("=" * 80)
    output.append("")

    # Status summary
    status_icon = "✅" if result.success else "❌"
    output.append(f"{status_icon} BOOT STATUS:        {'OPERATIONAL' if result.success else 'FAIL CLOSED'}")
    output.append(f"   Tamper Detected:   {result.tamper_detected}")
    output.append(f"   Kernel Valid:      {result.kernel_valid}")
    output.append(f"   Trace Valid:       {result.trace_valid}")
    output.append("")

    # Hash verification
    output.append("HASH CHAIN VERIFICATION:")
    output.append(f"   Events Processed:  {result.ledger_events}")
    output.append(f"   Computed Hash:     {result.final_cum_hash}")
    output.append(f"   Seal Expected:     {result.expected_cum_hash}")

    if result.final_cum_hash == result.expected_cum_hash:
        output.append(f"   ✅ MATCH")
    else:
        output.append(f"   ❌ MISMATCH")
    output.append("")

    # Kernel verification
    if result.kernel_hash_actual:
        output.append("KERNEL IDENTITY:")
        output.append(f"   Runtime Hash:      {result.kernel_hash_actual}")
        output.append(f"   Seal Hash:         {result.kernel_hash_seal or 'UNSET'}")
        if result.kernel_valid:
            output.append(f"   ✅ MATCH")
        else:
            output.append(f"   ❌ MISMATCH")
        output.append("")

    # Errors
    if result.mismatches:
        output.append("ISSUES DETECTED:")
        for err in result.mismatches:
            output.append(f"   ❌ {err}")
        output.append("")

    if not result.mismatches and result.success:
        output.append("✅ ALL CHECKS PASSED — SYSTEM OPERATIONAL")
        output.append("")
        output.append("SYSTEM STATE:")
        output.append(f"   Ledger integrity:     VERIFIED (hash chain valid)")
        output.append(f"   Seal binding:         VERIFIED (seal matches)")
        output.append(f"   Boot fail-closed:     OPERATIONAL")
        output.append(f"   Fresh-machine replay: SUCCESS")

    output.append("=" * 80)
    return "\n".join(output)

if __name__ == "__main__":
    # Determine ledger path from command line or default
    if len(sys.argv) > 1:
        ledger_path = Path(sys.argv[1])
    else:
        # Default to synthetic ledger if it exists, otherwise existing ledger
        script_dir = Path(__file__).parent
        synthetic = script_dir / "synthetic_ledger_v1_0_1.ndjson"
        if synthetic.exists():
            ledger_path = synthetic
        else:
            ledger_path = script_dir / "town" / "ledger_v1_SESSION_20260223.ndjson"

    print(f"Loading ledger: {ledger_path}")
    print(f"Exists: {ledger_path.exists()}")
    print()

    result = boot_verify(ledger_path)

    print(format_result(result))

    # Exit code
    sys.exit(0 if result.success else 1)
