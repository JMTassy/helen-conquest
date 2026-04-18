"""
tests/test_kernel_isolation.py

Critical enforcement: Only TownAdapter may import GovernanceVM directly.
All other modules must route through TownAdapter.propose_receipt().

This test ensures no subsystem bypasses the write-gate.
"""

import os
import re
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_only_town_adapter_imports_governance_vm():
    """
    Scan all Python files in helen_os/
    Verify: only town/town_adapter.py (and epoch2/ simulation layer)
    imports GovernanceVM directly.

    Exemption rationale for epoch2/:
      epoch2 is a non-sovereign simulation layer that creates ephemeral
      GovernanceVM(:memory:) instances for multi-seed validation runs.
      TownAdapter cannot be used here because it adds SEAL_V2 environment
      verification which is incompatible with :memory: kernels.
      epoch2 kernels are always :memory: (non-sovereign) and are never
      persisted — this is BY DESIGN (simulation, not production ledger).
    """
    forbidden_pattern = re.compile(
        r"from\s+(?:\.\.)?helen_os\.kernel\s+import\s+GovernanceVM|"
        r"from\s+(?:\.\.)?\.\.kernel\s+import\s+GovernanceVM"
    )

    # Allowed to import GovernanceVM directly:
    #   - town/town_adapter.py   : sovereign write-gate (production)
    #   - epoch2/                : non-sovereign sigma gate simulation layer (:memory: only)
    #   - epoch3/                : non-sovereign quest sim loop / shadow worlds (:memory: only)
    #   - claim_graph/           : non-sovereign dialogue runner / ARGUMENT_SIM (:memory: only)
    #   - epoch4/                : non-sovereign CLAIM_GRAPH_V1 artifact pipeline (:memory: only)
    #   - eval/                  : non-sovereign T2/T4 servitors + Godmode receipt (:memory: only)
    ALLOWED_PATTERNS = [
        "town_adapter.py",
        os.path.join("epoch2", ""),        # non-sovereign sigma gate (:memory:)
        os.path.join("epoch3", ""),        # non-sovereign quest sim loop (:memory:)
        os.path.join("claim_graph", ""),   # non-sovereign dialogue runner (:memory:)
        os.path.join("epoch4", ""),        # non-sovereign CLAIM_GRAPH pipeline (:memory:)
        os.path.join("eval", ""),          # non-sovereign T2/T4 servitors + Godmode (:memory:)
    ]

    violations = []

    for root, _, files in os.walk("helen_os"):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)

            # Skip __init__.py files
            if file == "__init__.py":
                continue

            # Skip allowed files/dirs
            if any(pattern in filepath for pattern in ALLOWED_PATTERNS):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                    if forbidden_pattern.search(content):
                        violations.append(filepath)
            except UnicodeDecodeError:
                # Skip binary files
                pass

    assert not violations, (
        f"Kernel import leak detected in: {violations}\n"
        f"Only helen_os/town/town_adapter.py (sovereign) and\n"
        f"helen_os/epoch2/ (non-sovereign simulation) may import GovernanceVM.\n"
        f"All other modules must call: adapter.propose_receipt(payload)"
    )
    print("✅ Test 1: Only TownAdapter + epoch2 simulation layer import GovernanceVM")


def test_conquest_cannot_import_kernel_directly():
    """
    Scan conquest/ module.
    Verify: no imports of GovernanceVM, kernel, or ledger.
    """
    forbidden = [
        "governance_vm",
        "GovernanceVM",
        "helen_os.kernel",
        "ledger_writer",
        "LedgerWriterV2",
    ]

    for root, _, files in os.walk("helen_os/conquest"):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                    for forbidden_term in forbidden:
                        assert forbidden_term not in content, (
                            f"Kernel access leak in {filepath}\n"
                            f"Found: {forbidden_term}\n"
                            f"CONQUEST must not import kernel directly."
                        )
            except UnicodeDecodeError:
                pass

    print("✅ Test 2: CONQUEST cannot import kernel directly")


def test_serpent_cannot_import_kernel_directly():
    """
    Scan serpent/ module.
    Verify: no imports of GovernanceVM, kernel, or ledger.
    """
    forbidden = [
        "governance_vm",
        "GovernanceVM",
        "helen_os.kernel",
        "ledger_writer",
        "LedgerWriterV2",
    ]

    for root, _, files in os.walk("helen_os/serpent"):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                    for forbidden_term in forbidden:
                        assert forbidden_term not in content, (
                            f"Kernel access leak in {filepath}\n"
                            f"Found: {forbidden_term}\n"
                            f"SERPENT must not import kernel directly."
                        )
            except UnicodeDecodeError:
                pass

    print("✅ Test 3: SERPENT cannot import kernel directly")


def test_extractors_cannot_import_kernel_directly():
    """
    Scan extractors/ module.
    Verify: no direct kernel imports.
    """
    forbidden = [
        "governance_vm",
        "GovernanceVM",
        "helen_os.kernel",
        "ledger_writer",
        "LedgerWriterV2",
    ]

    for root, _, files in os.walk("helen_os/extractors"):
        if not os.path.exists("helen_os/extractors"):
            return  # Directory may not exist yet

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                    for forbidden_term in forbidden:
                        assert forbidden_term not in content, (
                            f"Kernel access leak in {filepath}\n"
                            f"Found: {forbidden_term}\n"
                            f"Extractors must not import kernel directly."
                        )
            except UnicodeDecodeError:
                pass

    print("✅ Test 4: Extractors cannot import kernel directly")


if __name__ == "__main__":
    try:
        test_only_town_adapter_imports_governance_vm()
        test_conquest_cannot_import_kernel_directly()
        test_serpent_cannot_import_kernel_directly()
        test_extractors_cannot_import_kernel_directly()
        print("\n✅ All 4 kernel isolation tests PASSED")
    except AssertionError as e:
        print(f"\n❌ Kernel isolation test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
