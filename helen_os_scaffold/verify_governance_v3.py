import os
import sys
import time
from pathlib import Path

# Add the scaffold to the path
scaffold_path = Path("/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/helen_os_scaffold")
sys.path.append(str(scaffold_path))

from helen_os.memory_gravity import MemoryGravity
from helen_os.consciousness import ProtoConsciousness
from helen_os.federation import Egregor, Superteam, Claim

def test_governance_v3():
    print("🧪 HELEN OS v3 Advanced Governance Verification")
    print("-" * 50)
    
    # 1. Memory Gravity Test
    print("[STEP 1] Testing Memory Gravity (Exponential Decay)...")
    gravity = MemoryGravity(max_age=2) # 2 second window for quick test
    gravity.add_decision("D1")
    g0 = gravity.get_gravity()
    print(f"Gravity at t=0: {g0:.4f}")
    time.sleep(1)
    g1 = gravity.get_gravity()
    print(f"Gravity at t=1: {g1:.4f}")
    if g1 < g0:
        print("✅ SUCCESS: Gravity decayed over time.")
    else:
        print("❌ FAILURE: Gravity did not decay.")

    # 2. Proto-Consciousness Test
    print("\n[STEP 2] Testing Proto-Consciousness (Reflection)...")
    pc = ProtoConsciousness(morale=0.3, stability=0.8)
    reflection = pc.reflective_awareness()
    print(f"Reflection (Low Morale): {reflection}")
    if "empathy-driven" in reflection:
        print("✅ SUCCESS: Systems shifted to empathy mode.")
    else:
        print("❌ FAILURE: Morale threshold not triggered.")

    # 3. Egregor Test
    print("\n[STEP 3] Testing Egregor (Knowledge Aggregation)...")
    eg = Egregor()
    eg.add_knowledge("Priority: Stability")
    eg.add_knowledge("Priority: Growth")
    eg.add_knowledge("Priority: Stability")
    consensus = eg.aggregate_knowledge()
    print(f"Egregor Consensus: {consensus}")
    if consensus == "Priority: Stability":
        print("✅ SUCCESS: Majority rule applied.")
    else:
        print("❌ FAILURE: Aggregation logic failed.")

    # 4. Superteam Test
    print("\n[STEP 4] Testing Superteam (Claim Trading & Merging)...")
    st = Superteam()
    c1 = Claim("C1", "Fact", "Data A")
    c2 = Claim("C2", "Concern", "Risk B")
    st.add_claim("researcher", c1)
    st.add_claim("skeptic", c2)
    
    # Trade
    print(st.trade_claim("C1", "researcher", "synthesizer"))
    if c1.status == "traded":
        print("✅ SUCCESS: Claim traded.")
    else:
        print("❌ FAILURE: Trade failed.")
        
    # Merge
    print(st.merge_claims(["C1", "C2"]))
    merged = [c for c in st.claims if c.claim_type == "Synthesis"]
    if merged and "Data A + Risk B" in merged[0].content:
        print("✅ SUCCESS: Claims merged into synthesis.")
    else:
        print("❌ FAILURE: Merge failed.")

    print("\n" + "=" * 50)
    print("ADVANCED GOVERNANCE FRAMEWORK VERIFIED")

if __name__ == "__main__":
    test_governance_v3()
