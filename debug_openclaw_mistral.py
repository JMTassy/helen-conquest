#!/usr/bin/env python3
"""
OPENCLAW + Mistral Debugging Script
Diagnoses common issues and tests connectivity

Run: python3 debug_openclaw_mistral.py
"""

import os
import sys
import subprocess
from pathlib import Path

def check_api_key():
    """Check if Mistral API key is set"""
    print("\n" + "=" * 70)
    print("CHECK 1: MISTRAL_API_KEY")
    print("=" * 70)

    api_key = os.getenv("MISTRAL_API_KEY")

    if api_key:
        # Mask the key for security
        masked = api_key[:10] + "..." + api_key[-4:]
        print(f"✅ API Key found: {masked}")
        return True
    else:
        print(f"❌ API Key not set")
        print(f"\n   Set it with:")
        print(f"   export MISTRAL_API_KEY='sk_your-key-here'")
        return False


def check_sdk():
    """Check if Mistral SDK is installed"""
    print("\n" + "=" * 70)
    print("CHECK 2: MISTRAL SDK INSTALLATION")
    print("=" * 70)

    try:
        from mistralai import Mistral
        print(f"✅ mistralai SDK is installed")
        return True
    except ImportError as e:
        print(f"❌ mistralai SDK is NOT installed")
        print(f"\n   Install with:")
        print(f"   pip install mistralai --break-system-packages")
        return False


def check_python_version():
    """Check Python version"""
    print("\n" + "=" * 70)
    print("CHECK 3: PYTHON VERSION")
    print("=" * 70)

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"Python version: {version_str}")

    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python 3.8+ (required)")
        return True
    else:
        print(f"❌ Python < 3.8 (upgrade required)")
        return False


def check_files():
    """Check if required files exist"""
    print("\n" + "=" * 70)
    print("CHECK 4: REQUIRED FILES")
    print("=" * 70)

    required_files = [
        "mistral_workflow.py",
        "openclaw_helen_proxy.py",
        "OPENCLAW_MISTRAL_SETUP.md",
    ]

    all_exist = True
    for filename in required_files:
        path = Path(filename)
        if path.exists():
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename} (missing)")
            all_exist = False

    return all_exist


def check_ledger():
    """Check ledger directory and contents"""
    print("\n" + "=" * 70)
    print("CHECK 5: LEDGER DIRECTORY")
    print("=" * 70)

    ledger_dir = Path("runs/openclaw_proxy")
    if ledger_dir.exists():
        print(f"✅ Ledger directory exists: {ledger_dir}")

        ledger_file = ledger_dir / "ledger.ndjson"
        if ledger_file.exists():
            count = sum(1 for _ in open(ledger_file))
            print(f"✅ Ledger file exists with {count} entries")
            return True
        else:
            print(f"ℹ️  Ledger file doesn't exist yet (will be created)")
            return True
    else:
        print(f"ℹ️  Ledger directory doesn't exist yet")
        print(f"   Will be created on first run")
        return True


def test_mock_mode():
    """Test OPENCLAW in mock mode (no API key required)"""
    print("\n" + "=" * 70)
    print("CHECK 6: MOCK MODE TEST")
    print("=" * 70)

    try:
        # Temporarily unset API key
        saved_key = os.environ.pop("MISTRAL_API_KEY", None)

        print("Running OPENCLAW proxy in mock mode...")
        result = subprocess.run(
            ["python3", "openclaw_helen_proxy.py"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"✅ Mock mode works")
            # Restore key
            if saved_key:
                os.environ["MISTRAL_API_KEY"] = saved_key
            return True
        else:
            print(f"❌ Mock mode failed")
            print(f"Error: {result.stderr[:200]}")
            if saved_key:
                os.environ["MISTRAL_API_KEY"] = saved_key
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ Mock mode test timed out")
        return False
    except Exception as e:
        print(f"❌ Mock mode test failed: {e}")
        return False


def test_mistral_module():
    """Test Mistral module directly"""
    print("\n" + "=" * 70)
    print("CHECK 7: MISTRAL MODULE TEST")
    print("=" * 70)

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print(f"⏭️  Skipping (API key not set)")
        return None

    try:
        print("Testing Mistral workflow module...")
        result = subprocess.run(
            ["python3", "mistral_workflow.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(f"✅ Mistral module works")
            # Show first successful response
            if "SUCCESS" in result.stdout:
                print(f"   Execution: ✅ SUCCESS")
            return True
        else:
            print(f"❌ Mistral module failed")
            error_lines = result.stderr.split("\n")[:5]
            for line in error_lines:
                if line.strip():
                    print(f"   {line}")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ Mistral test timed out (API may be slow)")
        return False
    except Exception as e:
        print(f"❌ Mistral test failed: {e}")
        return False


def test_network():
    """Test network connectivity to Mistral API"""
    print("\n" + "=" * 70)
    print("CHECK 8: NETWORK CONNECTIVITY")
    print("=" * 70)

    try:
        # Try to reach Mistral API
        result = subprocess.run(
            ["curl", "-I", "-s", "https://api.mistral.ai/"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print(f"✅ Can reach api.mistral.ai")
            return True
        else:
            print(f"❌ Cannot reach api.mistral.ai")
            return False

    except FileNotFoundError:
        print(f"⏭️  curl not found (skipping network test)")
        return None
    except subprocess.TimeoutExpired:
        print(f"❌ Network test timed out")
        return False
    except Exception as e:
        print(f"⚠️  Network test error: {e}")
        return None


def generate_report(results):
    """Generate final report"""
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)

    checks = [
        ("API Key Set", results.get("api_key")),
        ("SDK Installed", results.get("sdk")),
        ("Python 3.8+", results.get("python")),
        ("Files Present", results.get("files")),
        ("Ledger Ready", results.get("ledger")),
        ("Mock Mode Works", results.get("mock")),
        ("Mistral Module", results.get("mistral")),
        ("Network OK", results.get("network")),
    ]

    passed = sum(1 for _, result in checks if result is True)
    failed = sum(1 for _, result in checks if result is False)
    skipped = sum(1 for _, result in checks if result is None)

    for check_name, result in checks:
        if result is True:
            print(f"✅ {check_name}")
        elif result is False:
            print(f"❌ {check_name}")
        elif result is None:
            print(f"⏭️  {check_name} (skipped)")

    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 All checks passed! OPENCLAW is ready to use.")
        if results.get("api_key"):
            print("\n   Next: python3 mistral_workflow.py")
        else:
            print("\n   Next:")
            print("   1. export MISTRAL_API_KEY='sk_your-key-here'")
            print("   2. python3 mistral_workflow.py")
    else:
        print(f"\n⚠️  {failed} checks failed. Review the output above.")


def main():
    """Run all checks"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║  OPENCLAW + MISTRAL DEBUGGING SCRIPT                               ║")
    print("╚" + "═" * 68 + "╝")

    results = {}

    results["api_key"] = check_api_key()
    results["sdk"] = check_sdk()
    results["python"] = check_python_version()
    results["files"] = check_files()
    results["ledger"] = check_ledger()
    results["mock"] = test_mock_mode()
    results["mistral"] = test_mistral_module()
    results["network"] = test_network()

    generate_report(results)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
