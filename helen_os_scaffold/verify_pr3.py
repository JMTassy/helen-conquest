import os
import subprocess
import time

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result

def test_pr3():
    # 0. Cleanup
    ledger = "storage/ledger.ndjson"
    idemp = "storage/idempotence_index_v1.ndjson"
    for f in [ledger, idemp]:
        if os.path.exists(f): os.remove(f)
    
    venv_python = ".venv/bin/python"
    venv_helen = ".venv/bin/helen"
    
    print("Initial check: No seal exists.")
    res = run_command(f"{venv_helen} chat 'Hello'")
    assert "IN WULmoji" in res.stdout
    print("Step 1: PASS (No seal)")

    print("Step 2: Creating SEAL_V2...")
    res = run_command(f"{venv_helen} seal-v2")
    assert "Ledger SEALED (V2)" in res.stdout
    assert "Pinned Env Hash" in res.stdout
    print("Step 2: PASS (SEAL_V2 created)")

    print("Step 3: Verification with original code...")
    res = run_command(f"{venv_helen} chat 'Status'")
    assert "IN WULmoji" in res.stdout
    print("Step 3: PASS (Verification successful)")

    print("Step 4: Tampering with helen.py...")
    helen_py = "helen_os/helen.py"
    with open(helen_py, "r") as f:
        original_content = f.read()
        
    with open(helen_py, "a") as f:
        f.write("\n# TAMPERED\n")
        
    try:
        print("Step 5: Verifying tamper detection...")
        res = run_command(f"{venv_helen} chat 'Status'")
        assert "LNSA_CRITICAL_ERROR: Environment verification FAILED!" in res.stdout
        assert "System is in fail-closed mode" in res.stdout
        print("Step 5: PASS (Tamper detected, system failed closed)")
    finally:
        # Restore helen_py
        with open(helen_py, "w") as f:
            f.write(original_content)
            
    print("Step 6: Verifying restoration...")
    res = run_command(f"{venv_helen} chat 'Status'")
    assert "IN WULmoji" in res.stdout
    print("Step 6: PASS (Restoration successful)")
    
    print("\nPR#3 Verification: ALL PASS (Startup Verification & Env Pinning)")

if __name__ == "__main__":
    test_pr3()
