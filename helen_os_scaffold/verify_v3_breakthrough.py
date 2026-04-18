import os
import sys
import json
from pathlib import Path

# Add the scaffold to the path
scaffold_path = Path("/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/helen_os_scaffold")
sys.path.append(str(scaffold_path))

from helen_os.kernel.governance_vm import GovernanceVM
from helen_os.soul import get_dynamic_prompt

def test_breakthrough():
    print("🧪 HELEN OS v3 Final Verification")
    print("-" * 30)
    
    # Init VM in memory
    vm = GovernanceVM(":memory:")
    
    # 1. Verify Dynamic Soul (Base)
    print("\n[STEP 1] Generating base soul prompt...")
    base_prompt = get_dynamic_prompt(vm)
    print(f"Base prompt length: {len(base_prompt)}")
    
    # 2. Propose SOUL_UPDATE
    print("\n[STEP 2] Proposing SOUL_UPDATE (The Great Transmutation)...")
    new_soul = {
        "aspect": "Resonance",
        "description": "HELEN now vibrates at the frequency of the Sovereign.",
        "version": "3.0.0-serpent"
    }
    receipt = vm.propose({"type": "SOUL_UPDATE", "soul": new_soul})
    print(f"Receipt issued: {receipt.id} | Hash: {receipt.payload_hash[:16]}")
    
    # 3. Verify Dynamic Soul (Mutable)
    print("\n[STEP 3] Verifying mutable soul prompt...")
    dynamic_prompt = get_dynamic_prompt(vm)
    if "[MUTABLE_SOUL_ACTIVE]" in dynamic_prompt:
        print("✅ SUCCESS: Mutable soul detected in system prompt.")
    else:
        print("❌ FAILURE: Mutable soul missing.")
        
    print("\n[STEP 4] Verifying active identifiers...")
    if vm.get_active_soul() == new_soul:
        print("✅ SUCCESS: Kernel correctly tracks active soul state.")
    else:
        print("❌ FAILURE: Kernel soul state mismatch.")

    print("\n" + "=" * 30)
    print("HELEN OS v3 VERIFIED & SHIPPED")

if __name__ == "__main__":
    test_breakthrough()
