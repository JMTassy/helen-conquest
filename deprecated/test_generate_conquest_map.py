#!/usr/bin/env python3
"""
Quick test: Generate a CONQUEST map and display it visually
"""

import json
from oracle_town.skills.map_generator_skill import MapGeneratorSkill

# Initialize skill
skill = MapGeneratorSkill()

# Generate map
print("=" * 70)
print("CONQUEST MAP GENERATOR — LIVE MAP")
print("=" * 70)

result = skill.generate_map(seed=111, game_id="conquest_test_001")

if result["status"] == "success":
    map_data = result["map_data"]

    # Display map metadata
    print(f"\n✅ Status: {result['status']}")
    print(f"📍 Seed: {map_data['seed']}")
    print(f"📏 Size: {map_data['width']}×{map_data['height']}")
    print(f"🏰 Territories: {len(map_data['territories'])}")
    print(f"🔐 Map Hash: {result['validation_results']['k7_policy_pinning']['map_hash'][:32]}...")

    # Display visual grid
    print("\n" + "=" * 70)
    print("TERRITORY GRID (5×5)")
    print("=" * 70)

    # Build grid for visualization
    grid = [['.' for _ in range(5)] for _ in range(5)]

    # Map territory IDs to symbols
    symbols = ['①', '②', '③', '④', '⑤', '⑥']

    # Fill grid with territory IDs
    for territory in map_data['territories']:
        tid = territory['territory_id']
        for x, y in territory['cells']:
            grid[y][x] = symbols[tid]

    # Print grid
    print("\n  0 1 2 3 4")
    for y in range(5):
        print(f"{y} {' '.join(grid[y])}")

    # Display territory details
    print("\n" + "=" * 70)
    print("TERRITORY DETAILS")
    print("=" * 70)

    for territory in map_data['territories']:
        tid = territory['territory_id']
        cells = territory['cells']
        terrain = territory['terrain_distribution']
        climate = territory['climate_distribution']

        print(f"\n{symbols[tid]} Territory {tid}:")
        print(f"   Size: {len(cells)} tiles")
        print(f"   Center: ({territory['center'][0]:.1f}, {territory['center'][1]:.1f})")
        print(f"   Terrain: {dict(terrain)}")
        print(f"   Climate: {dict(climate)}")
        print(f"   Cells: {cells}")

    # K-gate validation results
    print("\n" + "=" * 70)
    print("K-GATE VALIDATION RESULTS")
    print("=" * 70)

    for gate, result_data in result['validation_results'].items():
        if isinstance(result_data, dict) and 'pass' in result_data:
            status = "✅ PASS" if result_data['pass'] else "❌ FAIL"
            print(f"\n{gate.upper()}: {status}")
            for key, value in result_data.items():
                if key != 'pass':
                    print(f"  {key}: {value}")

    # Claim info
    print("\n" + "=" * 70)
    print("K2 CLAIM (AWAITING FOREMAN APPROVAL)")
    print("=" * 70)
    claim = result['claim']
    print(f"\nClaim ID: {claim['claim_id']}")
    print(f"Type: {claim['type']}")
    print(f"Author: {claim['author']}")
    print(f"Statement: {claim['statement']}")
    print(f"Status: {claim['status']} (awaiting Foreman)")

    # Ledger info
    print("\n" + "=" * 70)
    print("K7 LEDGER RECORD")
    print("=" * 70)
    print(f"\nLedger Entry ID: {result['ledger_entry_id']}")
    print(f"Location: kernel/ledger/map_generation_records.jsonl")
    print(f"Append-only JSONL format (immutable record)")

    print("\n" + "=" * 70)
    print("✨ MAP GENERATION COMPLETE ✨")
    print("=" * 70)

    # Show full map_data as JSON
    print("\nFull Map Data (JSON):")
    print(json.dumps(map_data, indent=2)[:500] + "...\n")

else:
    print(f"❌ Error: {result['error']}")
    print(f"Details: {result.get('error_details', 'No details')}")
